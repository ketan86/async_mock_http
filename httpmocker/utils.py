"""Collection of utilities"""
import functools
import importlib.util
import subprocess
import sys

from httpmocker.exceptions import AccessDenied


def singleton(cls):
    """Singleton class decorator."""
    _instances = {}

    @functools.wraps(cls)
    def wrapper(*args, **kwargs):
        if cls not in _instances:
            _instances[cls] = cls(*args, **kwargs)
        return _instances[cls]
    return wrapper


def permit_access_if(attr, value, msg):
    """Permit access if attribute of the class
    matches the given value.

    :param Any attr: member variable.
    :param Any value: value of the member variable.
    :param str msg: message to assert with when variable
        value does not match.
    :raises AccessNotAllowed
    :return: decorated function
    :rtype: callable
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if getattr(self, attr) != value:
                raise AccessDenied(msg)
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


# class AutoInstall:
#     _loaded = set()

#     @classmethod
#     def find_spec(cls, name, path, target=None):
#         if path is None and name not in cls._loaded:
#             cls._loaded.add(name)
#             print(name)
#             try:
#                 out = subprocess.check_output([
#                     sys.executable, '-m', 'pip', 'install', name
#                 ], stdout=subprocess.DEVNULL,
#                     stderr=subprocess.DEVNULL)
#                 return importlib.util.find_spec(name)
#             except Exception as error:
#                 pass
#         return None
