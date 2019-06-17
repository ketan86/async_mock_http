"""Abstract Base Application"""
import logging
from uuid import uuid4

from httpmocker.exceptions import DuplicateAppError
from httpmocker.handler import AbstractHandler, register_handler_routes
from httpmocker.mixins import SSLMixin

logger = logging.getLogger(__name__)


class AppRegistry():
    pass


class MetaApp(type):
    def __new__(meta, name, bases, cls_dict):
        cls = super().__new__(meta, name, bases, cls_dict)
        if not hasattr(AppRegistry, cls.NAME.lower()):
            setattr(AppRegistry, cls.NAME.lower(), cls)
        else:
            raise DuplicateAppError(
                f'App name {cls.NAME} is registered twice.')
        return cls

    @register_handler_routes()
    def __call__(cls, *args, **kwargs):
        return super().__call__(*args, **kwargs)


class BaseApp(SSLMixin, AbstractHandler, metaclass=MetaApp):
    NAME = 'Base'

    def __init__(self, config):
        SSLMixin.__init__(self, config.get(
            'ssl_cert', None), config.get('ssl_key', None))
        self.id = '-'.join([self.NAME, str(uuid4())])
        self._host = '0.0.0.0'
        self._port = 8000
        self.handler_data = {}

    @property
    def port(self):
        return self._port

    @property
    def host(self):
        return self._host

    @property
    def name(self):
        return self.NAME
