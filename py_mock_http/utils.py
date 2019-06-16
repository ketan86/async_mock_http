"""Collection of utilities"""
import functools
from py_mock_http.exceptions import AccessNotAllowed


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
                raise AccessNotAllowed(msg)
            return func(self, *args, **kwargs)
        return wrapper
    return decorator
