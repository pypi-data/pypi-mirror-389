from functools import lru_cache, wraps
from datetime import datetime, timedelta, UTC


def cache_with_expiration(maxsize: int = 1, **kwargs):
    """
    Wrapper around `functools.lru_cache`, adding the concept of time limit to the
    cache.
    `maxsize` is the number of results cached; how much you need depends on the
    number of parameters your function takes, and how many values they can have,
    and how much memory you can dedicate to the cache.
    The rest of the arguments are passed to `datetime.timedelta()`, as the TTL
    of the results, regardless of the arguments, i.e. after that time has passed,
    all the cached results are cleared; the TTL is not per parameter value.
    """
    def wrapper_cache(func):
        cached_func = lru_cache(maxsize=maxsize)(func)
        cached_func._cache_ttl = timedelta(**kwargs)
        assert cached_func._cache_ttl > timedelta(0)

        def cache_clear():
            cached_func.cache_clear()
            cached_func._cache_expiration = datetime.now(UTC) + cached_func._cache_ttl

        cache_clear()

        @wraps(cached_func)
        def wrapped_func(*args, **kwargs):
            if datetime.now(UTC) >= cached_func._cache_expiration:
                cache_clear()
            return cached_func(*args, **kwargs)

        wrapped_func.cache_clear = cache_clear
        return wrapped_func

    return wrapper_cache
