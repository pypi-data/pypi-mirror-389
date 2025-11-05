
import numpy as np
from functools import wraps


def main():
    import pandas as pd
    seed = 40
    np.random.seed(seed)
    data = pd.DataFrame({'item1': [x for x in np.random.normal(size=50)],
                         'item2': [x for x in np.random.normal(50, size=50)]})

    @bootstrap(100, seed, lambda x, y: x.iloc[y])
    def take_mean(A):
        return A.mean()

    print(take_mean(data))


def bootstrap(num_trials, seed, indexing_function=(lambda x, y: x[y])):
    def decorator(func):
        @wraps(func)
        def wrapper(data, *args, **kwargs):
            results = []
            rng = np.random.default_rng(seed)
            for i in range(num_trials):
                # take a random sample from the data
                sample_idx = rng.choice(len(data), replace=True, size=len(data)).tolist()
                idata = indexing_function(data, sample_idx)
                results.append(func(idata, *args, **kwargs))
            return results
        return wrapper
    return decorator



if __name__ == "__main__": 
    main()
