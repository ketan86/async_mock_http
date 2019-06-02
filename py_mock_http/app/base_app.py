"""Abstract Base Application"""
from exceptions import DuplicateAppError
from uuid import uuid4
from handler import AbstractHandler, register_handler_routes


class AppRegistry():
    pass


class MetaApp(type):
    def __new__(meta, name, bases, cls_dict):
        cls = super().__new__(meta, name, bases, cls_dict)
        if not hasattr(AppRegistry, cls.name.lower()):
            setattr(AppRegistry, cls.name.lower(), cls)
        else:
            raise DuplicateAppError(
                f'App name {cls.name} is registered twice.')
        return cls

    @register_handler_routes
    def __call__(cls, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class BaseApp(AbstractHandler, metaclass=MetaApp):
    name = 'Base'

    def __init__(self):
        self.id = '-'.join([self.name, str(uuid4())])
        self._host = '0.0.0.0'
        self._port = 8000
        self.handler_data = {}

    @property
    def port(self):
        return self._port

    @property
    def host(self):
        return self._host
