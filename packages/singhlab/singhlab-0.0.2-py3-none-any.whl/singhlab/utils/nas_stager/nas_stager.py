"""
NAS Stager — simple, safe scratch→NAS staging for HPC jobs.

Students write to a *NAS path* but your code actually writes to local scratch
for speed, then a background worker copies the file to NAS and atomically
renames it into place. No hardcore async/await required.

Key API
-------
1) Context manager (drop‑in for open):

   from nas_stager import staged_open, stager
   with staged_open("/nas/project/out.ckpt", "wb") as f:
       torch.save(state, f)
   # returns immediately after close; background copy to NAS continues
   stager.flush()  # ensure all copies finished (or rely on atexit)

2) Decorator to autostage function outputs (by argument name):

   from nas_stager import autostage_files

   @autostage_files("model_path", "log_path")
   def train(..., model_path: str, log_path: str):
       # Inside, these are scratch paths; write like normal.
       torch.save(..., model_path)
       with open(log_path, "w") as f: f.write("done\n")

   train(..., model_path="/nas/runA/model.pt", log_path="/nas/runA/log.txt")
   # After train() returns, background copies stage→NAS atomically.

Environment
-----------
- STAGER_SCRATCH_DIR: override scratch root; defaults to /scratch/$USER/$SLURM_JOB_ID if available, else /scratch/$USER.
- STAGER_WORKERS: number of copy worker threads (default: 2)
- STAGER_QUEUE: max queued copy tasks (default: 32)
- STAGER_LOG: set to "1" for INFO logging, "2" for DEBUG.

Notes
-----
- Uses rsync if available; falls back to shutil copy.
- Creates destination directories on NAS (including `.staging`), copies to `dest_dir/.staging/<file>.tmp.<uuid>`, then atomically renames into place.
- On exceptions inside a staged_open() block, the temp file is kept on scratch
  (not copied) and its path is logged for inspection.
- Atexit handler flushes outstanding copies; you can also call stager.flush().
- SIGINT/SIGTERM are trapped to flush in-flight copies before exit.
"""
from __future__ import annotations

import atexit
import functools
import inspect
import logging
import os
import queue
import shutil
import signal
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Optional

# ------------------------------ Logging ------------------------------------
_LOG = logging.getLogger("nas_stager")
_level = os.environ.get("STAGER_LOG", "0")
if _level == "1":
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
elif _level == "2":
    logging.basicConfig(level=logging.DEBUG, format="[%(asctime)s] %(levelname)s: %(message)s")
else:
    logging.basicConfig(level=logging.WARNING, format="[%(asctime)s] %(levelname)s: %(message)s")

# ------------------------------ Utilities ----------------------------------

def _default_scratch_dir() -> Path:
    # Priority: STAGER_SCRATCH_DIR > /scratch/$USER/$SLURM_JOB_ID > /scratch/$USER
    if (p := os.environ.get("STAGER_SCRATCH_DIR")):
        return Path(p).expanduser()
    user = os.environ.get("USER", "user")
    jid = os.environ.get("SLURM_JOB_ID")
    if jid:
        return Path(f"/scratch/{user}/{jid}")
    return Path(f"/scratch/{user}")


def _which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


# ------------------------------ Copy Task ----------------------------------

@dataclass
class _CopyTask:
    tmp: Path
    dest: Path


# ------------------------------ Stager -------------------------------------

class NASStager:
    def __init__(self, scratch_root: Optional[Path] = None, workers: Optional[int] = None, max_queue: Optional[int] = None):
        self.scratch_root = Path(scratch_root) if scratch_root else _default_scratch_dir()
        self.scratch_root.mkdir(parents=True, exist_ok=True)
        self._staging_dir = self.scratch_root / ".tmp_out"
        self._staging_dir.mkdir(parents=True, exist_ok=True)

        self.workers = int(workers or os.environ.get("STAGER_WORKERS", 2))
        self.q: "queue.Queue[_CopyTask]" = queue.Queue(maxsize=int(max_queue or os.environ.get("STAGER_QUEUE", 32)))
        self._threads: list[threading.Thread] = []
        self._stop = threading.Event()
        self._active = 0
        self._active_lock = threading.Lock()
        self._all_done = threading.Condition(self._active_lock)

        # Launch workers
        for i in range(self.workers):
            t = threading.Thread(target=self._worker, name=f"stager-copy-{i}", daemon=True)
            t.start()
            self._threads.append(t)

        # Clean shutdown
        atexit.register(self.flush)
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, self._signal_handler)
            except Exception:
                pass  # in some environments signal setting may fail

    # -------------------------- Public API ---------------------------------

    def stage_path(self, dest_path: os.PathLike | str, suffix_from_dest: bool = True) -> Path:
        """Return a unique scratch path for a future NAS destination.
        The file isn't created yet. Parent dirs are created.
        """
        dest = Path(dest_path)
        ext = dest.suffix if suffix_from_dest else ""
        name = dest.stem or dest.name
        unique = uuid.uuid4().hex[:8]
        scratch = self._staging_dir / f"{name}.{unique}{ext}"
        scratch.parent.mkdir(parents=True, exist_ok=True)
        return scratch

    def enqueue(self, tmp_path: os.PathLike | str, dest_path: os.PathLike | str) -> None:
        """Queue a copy tmp→dest (atomic rename on NAS). Blocks if queue is full."""
        tmp = Path(tmp_path)
        dest = Path(dest_path)
        if not tmp.exists():
            _LOG.warning("Temp path missing, skip: %s", tmp)
            return
        self.q.put(_CopyTask(tmp=tmp, dest=dest))

    def flush(self, timeout: Optional[float] = None) -> None:
        """Wait until the queue is empty and all copies finished."""
        _LOG.info("Flushing staged copies…")
        # Wait queue drained
        self.q.join()
        # Wait active tasks
        with self._active_lock:
            if timeout is None:
                while self._active > 0:
                    self._all_done.wait(timeout=0.5)
            else:
                end = time.time() + timeout
                while self._active > 0 and time.time() < end:
                    remaining = end - time.time()
                    self._all_done.wait(timeout=max(0.1, remaining))
        _LOG.info("Flush complete.")

    # ------------------------ Worker internals -----------------------------

    def _worker(self) -> None:
        while not self._stop.is_set():
            try:
                task: _CopyTask = self.q.get(timeout=0.2)
            except queue.Empty:
                continue
            with self._active_lock:
                self._active += 1
            try:
                self._do_copy(task.tmp, task.dest)
            except Exception as e:
                _LOG.error("Copy failed tmp=%s dest=%s: %s", task.tmp, task.dest, e)
            finally:
                with self._active_lock:
                    self._active -= 1
                    if self._active == 0 and self.q.unfinished_tasks == 0:
                        self._all_done.notify_all()
                self.q.task_done()

    def _do_copy(self, tmp: Path, dest: Path) -> None:
        dest_dir = dest.parent
        dest_dir.mkdir(parents=True, exist_ok=True)
        staging_dir = dest_dir / ".staging"
        staging_dir.mkdir(parents=True, exist_ok=True)
        temp_dest = staging_dir / f"{dest.name}.tmp.{uuid.uuid4().hex[:8]}"

        _LOG.info("Copying %s → %s", tmp, temp_dest)
        rsync = _which("rsync")
        if rsync:
            # rsync preserves perms/times and is robust for big files
            cmd = [rsync, "-a", "--partial", str(tmp), str(temp_dest)]
            subprocess.run(cmd, check=True)
        else:
            # Python fallback
            shutil.copy2(tmp, temp_dest)
        # Atomic promote
        os.replace(temp_dest, dest)
        # Optionally remove tmp scratch file
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass
        _LOG.info("Staged file available: %s", dest)

    def _signal_handler(self, signum, frame):
        _LOG.warning("Signal %s received; flushing staged copies before exit…", signum)
        try:
            self.flush()
        finally:
            # re-raise default action
            try:
                signal.signal(signum, signal.SIG_DFL)
            except Exception:
                pass
            os.kill(os.getpid(), signum)


# Global stager instance
stager = NASStager()


# ---------------------------- Context Manager ------------------------------

class _StagedOpen:
    def __init__(self, dest_path: os.PathLike | str, mode: str = "wb", encoding: Optional[str] = None, stager_obj: NASStager = None):
        self.dest = Path(dest_path)
        self.mode = mode
        self.encoding = encoding
        self.stager = stager_obj or stager
        # Use a temp path on scratch with same suffix for UX
        suffix = self.dest.suffix if self.dest.suffix else None
        self.tmp = Path(tempfile.mkstemp(dir=str(self.stager._staging_dir), suffix=suffix)[1])
        self._fh = None

    def __enter__(self):
        if "b" in self.mode:
            self._fh = open(self.tmp, self.mode)
        else:
            self._fh = open(self.tmp, self.mode, encoding=self.encoding)
        return self._fh

    def __exit__(self, exc_type, exc, tb):
        try:
            if self._fh and not self._fh.closed:
                self._fh.flush()
                try:
                    os.fsync(self._fh.fileno())
                except Exception:
                    pass
                self._fh.close()
        finally:
            if exc_type is None:
                self.stager.enqueue(self.tmp, self.dest)
            else:
                _LOG.error("Exception inside staged_open; keeping temp at %s (not copied)", self.tmp)
        # Do not suppress exceptions
        return False


def staged_open(dest_path: os.PathLike | str, mode: str = "wb", *, encoding: Optional[str] = None, stager_obj: Optional[NASStager] = None):
    """Drop-in replacement for open() that stages writes to scratch then copies to NAS.
    Example:
        with staged_open("/nas/out.bin", "wb") as f:
            f.write(b"hello")
    """
    return _StagedOpen(dest_path, mode=mode, encoding=encoding, stager_obj=stager_obj or stager)


# ---------------------------- Decorators -----------------------------------

def autostage_files(*arg_names: str):
    """Decorator: given output path arguments by name, replace them with scratch
    paths before calling the function, then enqueue copies to NAS after return.

    @autostage_files("model_path", "log_path")
    def train(..., model_path: str, log_path: str):
        torch.save(..., model_path)
        open(log_path, "w").write("ok\n")

    train(..., model_path="/nas/run/model.pt", log_path="/nas/run/log.txt")
    """
    def deco(fn: Callable):
        sig = inspect.signature(fn)
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            bound = sig.bind_partial(*args, **kwargs)
            bound.apply_defaults()
            replacements: list[tuple[Path, Path, str]] = []  # (scratch, dest, name)
            for name in arg_names:
                if name not in bound.arguments:
                    continue
                dest = Path(bound.arguments[name])
                scratch = stager.stage_path(dest)
                replacements.append((scratch, dest, name))
                bound.arguments[name] = str(scratch)
            try:
                return fn(*bound.args, **bound.kwargs)
            finally:
                for scratch, dest, _ in replacements:
                    stager.enqueue(scratch, dest)
        return wrapper
    return deco


# ----------------------------- Directory API -------------------------------

def stage_dir(dir_path: os.PathLike | str, dest_dir: os.PathLike | str) -> None:
    """Enqueue a whole directory copy (rsync -a). Useful for checkpoint dirs."""
    src = Path(dir_path)
    dst = Path(dest_dir)
    if not src.exists():
        raise FileNotFoundError(src)

    # Create a tarball *on scratch* then enqueue copy of the tarball + unpack? Too heavy.
    # Simpler: enqueue a task per file. For large trees, advise users to
    # rsync after the run or use sbatch-postcopy; we keep this minimal.
    for p in src.rglob("*"):
        if p.is_file():
            rel = p.relative_to(src)
            stager.enqueue(p, dst / rel)


# ----------------------------- Slurm helper --------------------------------

def sbatch_postcopy(tmp: os.PathLike | str, dest: os.PathLike | str, dependency: str = "afterok") -> Optional[str]:
    """Submit a tiny Slurm job to copy tmp→dest after current job completes.
    Returns job id or None if sbatch not found.
    """
    sbatch = _which("sbatch")
    if not sbatch:
        _LOG.warning("sbatch not found; cannot submit postcopy job")
        return None
    cur = os.environ.get("SLURM_JOB_ID")
    dep = f"--dependency={dependency}:{cur}" if cur else ""
    script = f"""#!/bin/bash
#SBATCH -p {os.environ.get('SLURM_PARTITION','scavenger')}
#SBATCH -J postcopy
set -euo pipefail
dest_dir="$(dirname "{dest}")"
staging_dir="$dest_dir/.staging"
mkdir -p "$staging_dir"
tmp_dest="$staging_dir/$(basename "{dest}").tmp.$(date +%s).$$"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --partial "{tmp}" "$tmp_dest"
else
  cp -p "{tmp}" "$tmp_dest"
fi
mv "$tmp_dest" "{dest}"
rm -f "{tmp}"
"""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".sh") as f:
        f.write(script)
        f.flush()
        path = f.name
    out = subprocess.run([sbatch, dep, path], capture_output=True, text=True)
    if out.returncode != 0:
        _LOG.error("sbatch postcopy failed: %s", out.stderr.strip())
        return None
    jid = out.stdout.strip().split()[-1]
    return jid
