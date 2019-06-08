"""Collection of utilities"""
import functools


def singleton(cls):
    _instances = {}

    @functools.wraps(cls)
    def wrapper(*args, **kwargs):
        if cls not in _instances:
            _instances[cls] = cls(*args, **kwargs)
        return _instances[cls]
    return wrapper


def check(attr, expected_status, msg):
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if getattr(self, attr) != expected_status:
                raise AssertionError(msg)
            return func(self, *args, **kwargs)
        return wrapper
    return decorator
