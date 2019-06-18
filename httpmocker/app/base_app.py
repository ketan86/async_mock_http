"""Abstract Base Application"""
import logging
from uuid import uuid4

from httpmocker.exceptions import DuplicateAppError
from httpmocker.handler import AbstractHandler, register_handler_routes
from httpmocker.mixins import SSLMixin
from httpmocker.config import get_config
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
        self.id = '-'.join([self.NAME, str(uuid4())])
        self._host = '0.0.0.0'
        self._port = None
        self.handler_data = {}
        cert = config.get('ssl_cert', None)
        key = config.get('ssl_key', None)
        if cert and key:
            self.save_cert(cert, key)

    def get_handler_storage_root(self):
        return get_config().get('HANDLER_STORAGE_ROOT') + \
            f'/{self.NAME}/' + str(self._port)

    def get_cert_storage_root(self):
        return get_config().get('CERT_STORAGE_ROOT') + \
            f'/{self.NAME}/'

    @property
    def port(self):
        return self._port

    @property
    def host(self):
        return self._host

    @property
    def name(self):
        return self.NAME
