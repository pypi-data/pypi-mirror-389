
import os
import shutil 
import atexit
import tempfile

import sys 
import traceback

from pathlib import Path
from functools import wraps


class StorageManager():

    NEW_DIR = tempfile.gettempdir()
    CACHE = False

    def __init__(self, n_files_in=1, n_files_out=0, kwargs_files_in=[], kwargs_files_out=[], new_dir=None, 
            cache=None, cache_dir=None, output=False, copy=True, exist_ok=True, parents=True):
        # handle default for new_dir 
        if new_dir is None:
            self.new_dir = Path(self.NEW_DIR)
        else: 
            self.new_dir = Path(new_dir)

        try:
            if not isinstance(new_dir, Path):
                self.new_dir.mkdir(parents=parents, exist_ok=exist_ok)
        except Exception as e:
            print(traceback.format_exc(), file=sys.stderr)
            sys.exit(1)

        # file arguments to wrapped function
        self.n_files_in = n_files_in
        self.n_files_out = n_files_out
        self.kwargs_files_in = kwargs_files_in
        self.kwargs_files_out = kwargs_files_out
        
        # file handling 
        self.copy = copy
        self.fmap = {}
        self.fmap_values = set()

        # handle cache and cache dir 
        if cache is None:
            self.cache = self.CACHE
        else:
            self.cache = cache
        
        if self.cache:
            atexit.register(self.clean_out)
        
            # only define self.cache_dir if needed
            if cache_dir is None:
                self.cache_dir = self.new_dir
            else:
                self.cache_dir = Path(cache_dir)

            # move all cached files to temporary directory
            if os.path.exists(self.cache_dir) and (self.cache_dir != self.new_dir):
                for p in self.cache_dir.iterdir():
                    dst_name = self.new_dir / p.relative_to(self.cache_dir)
                    if not os.path.exists(dst_name):
                        if self.copy:
                            if p.is_file():
                                shutil.copy(p, dst_name)
                            elif p.is_dir():
                                shutil.copytree(p, dst_name)
                        else:
                            shutil.move(p, dst_name)

    def __call__(self, func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            # --- args ---
            new_args = []
            count = 0

            # assumes first self.n_files_in inputs are file paths to existing files
            for i in range(min(len(args), self.n_files_in)):
                count += 1
                fpath = args[i]
                if fpath not in self.fmap:
                    self.add_to_fmap(fpath, True)
                new_args.append(self.fmap[fpath])

            # if args is not exhausted, assumes next few files are output file paths
            if count < len(args):
                n_output_files = min(len(args) - count, self.n_files_out)
                for i in range(n_output_files):
                    fpath_out = args[count + i]
                    count += 1
                    if fpath_out not in self.fmap:
                        self.add_to_fmap(fpath_out, False)
                    new_args.append(self.fmap[fpath_out])

            # exhaust args 
            for i in range(count, len(args), 1):
                new_args.append(args[i])

            # --- kwargs --- 
            fpath_kwargs = set(self.kwargs_files_in + self.kwargs_files_out)
            new_kwargs = {k: v for k, v in kwargs.items() if (k not in fpath_kwargs)}

            for kw in self.kwargs_files_in:
                fpath = kwargs.get(kw)
                if fpath:
                    if fpath not in self.fmap:
                        self.add_to_fmap(fpath, True)
                    new_kwargs[kw] = self.fmap[fpath]

            for kw in self.kwargs_files_out:
                fpath_out = kwargs.get(kw)
                if fpath_out:
                    if fpath_out not in self.fmap:
                        self.add_to_fmap(fpath_out, False)
                    new_kwargs[kw] = self.fmap[fpath_out]

            return func(*new_args, **new_kwargs)

        return wrapper

    def add_to_fmap(self, fpath, is_input):
        if fpath not in self.fmap:
            folder, file_name = os.path.split(fpath) 
            new_fpath = os.path.join(self.new_dir, file_name)
            if (not is_input) or (not os.path.exists(new_fpath)):
                if self.copy:
                    if is_input and (fpath not in self.fmap_values):
                        shutil.copy(fpath, new_fpath)
                    else:
                        if self.cache:
                            atexit.register(lambda: self.copyfile(new_fpath, fpath))
                        else:
                            atexit.register(lambda: self.move(new_fpath, fpath))
                else:
                    if is_input and (fpath not in self.fmap_values):
                        shutil.move(fpath, new_fpath)
                    atexit.register(lambda: self.move(new_fpath, fpath))

            self.fmap[fpath] = new_fpath
            self.fmap_values.add(new_fpath)

    def move(self, src, dest):
        if os.path.exists(src):
            shutil.move(src, dest)
        else:
            print(f"WARNING: file {src} does not exist!", file=sys.stderr)

    def copyfile(self, src, dest):
        if os.path.exists(src):
            shutil.copy(src, dest)
        else:
            print(f"WARNING: file {src} does not exist!", file=sys.stderr)

    def clean_out(self):
        # if cache is set to true, move everything to the cache directory 
        if self.cache: 
            if self.cache_dir != self.new_dir:
                try:
                    cache_dir = Path(self.cache_dir)
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    for p in self.new_dir.iterdir():
                        try:
                            shutil.move(p, self.cache_dir)
                        except shutil.Error as e:
                            print(f"Saving Cache: {e}")
                            continue
                except Exception as e:
                    print("Error! Failed to cache directory. Traceback:")
                    print(traceback.format_exc(), file=sys.stderr)
                    return
        else:
            shutil.rmtree(self.new_dir, ignore_errors=True)
            for p in self.new_dir.parents:
                try:
                    p.rmdir()
                except OSError:
                    break
    

# --- testing --- 
@StorageManager(n_files_in=2, kwargs_files_out=['fout'])
def concat(fname1, fname2, fout):
    print(f"--- writing to {fout} ---")
    with open(fout, 'w') as fout:
        print(f"--- reading {fname1} ---")
        with open(fname1, 'r') as f: 
            fout.write(f.read())
        print(f"--- reading {fname2} ---")
        with open(fname2, 'r') as f:
            fout.write(f.read())


if __name__ == '__main__': 
    fname1 = "bar.txt"
    fname2 = "foo.txt"
    fout = "baz.out"
    concat(fname1, fname2, fout=fout)
    print("scratch dir contents:", os.listdir("/scratch"))
