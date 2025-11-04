import functools
import warnings


def beta(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"Function '{func.__name__}' is in BETA and may change in future versions.",
            category=UserWarning,
            stacklevel=2
        )
        return func(*args, **kwargs)
    return wrapper
