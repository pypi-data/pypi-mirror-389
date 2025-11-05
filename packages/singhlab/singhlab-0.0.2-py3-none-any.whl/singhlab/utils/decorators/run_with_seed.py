
import numpy as np
import random

from functools import wraps


def main():
    seed = 42

    @run_with_seed(seed)
    def normal(mean, std=1, size=100):
        return np.random.normal(mean, std, size=size)

    print(normal(100))


def run_with_seed(seed):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            np.random.seed(seed)
            random.seed(seed)
            return func(*args, **kwargs)

        return wrapper

    return decorator 


if __name__ == '__main__': 
    main()
