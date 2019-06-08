"""Client exposes APIs to manage server operations.
"""
from __future__ import absolute_import

import logging
import importlib
import json
import abc
from http.client import HTTPConnection, HTTPSConnection, HTTPException
from exceptions import ClientException, ConnectError

from utils import check

logger = logging.getLogger(__name__)


def mock_app(app_type, port, **kwargs):
    with Client() as client:
        app = client.app(app_type, port, **kwargs)
        app.start()
        return app


class BaseAdapter(abc.ABC):

    @abc.abstractmethod
    def connect(self):
        raise NotImplementedError

    @abc.abstractmethod
    def disconnect(self):
        raise NotImplementedError

    @abc.abstractproperty
    def conn(self):
        raise NotImplementedError


class HTTPAdapter(BaseAdapter):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self._conn = None
        self._connected = False

    @property
    def connected(self):
        return self._connected

    @property
    def conn(self):
        return self._conn

    def connect(self):
        try:
            self._conn = HTTPConnection(
                self.host, self.port,
                timeout=10
            )
            self._connected = True
        except HTTPException:
            raise ConnectError(
                f'Could not connect to a {self.host}.')

        return self._conn

    def disconnect(self):
        try:
            self._conn.close()
            self._connected = False
        except HTTPException:
            raise ConnectError(
                f'Could not disconnect from a {self.host}.')


class HTTPSAdapter(HTTPAdapter):
    def __init__(self, host, port, cert_file, key_file):
        super().__init__(host, port)
        self.cert_file = cert_file
        self.key_file = key_file

    def connect(self):
        try:
            self._conn = HTTPSConnection(
                self.host,
                port=self.port,
                cert_file=self.cert_file,
                key_file=self.key_file,
                timeout=10
            )
            self._connected = True
        except HTTPException:
            raise ConnectError(
                f'Could not connect to a server {self.host}')

        return self._conn


class AppType:
    SANIC = 'sanic'
    DJANGO = 'django'
    FLASK = 'flask'


class Handler:

    def __init__(self, name, **kwargs):
        self._name = name
        self.conn = kwargs['conn']
        self.base_url = '/mock/app/handler/'
        self.handler_set = False

    @property
    def name(self):
        return self._name

    @check('handler_set', True, msg='Handler is not set.')
    def set_data(self, url, data):
        headers = {'m-handler-url': url}
        self.conn.request('POST',
                          self.base_url + 'data/',
                          body=json.dumps(data),
                          headers=headers)
        response = self.conn.getresponse()
        if response.status != 200:
            raise ClientException(
                f'Could not set the handler data.')
        return json.loads(response.read())

    @check('handler_set', True, msg='Handler is not set.')
    def remove_data(self, url):
        headers = {'m-handler-url': url}
        self.conn.request('DELETE',
                          self.base_url + 'data/',
                          headers=headers)
        response = self.conn.getresponse()
        if response.status != 200:
            raise ClientException(
                f'Could not remove the handler data.')
        return json.loads(response.read())

    def set(self, data):
        headers = {'m-handler-name': self._name}
        self.conn.request('POST',
                          self.base_url,
                          body=data,
                          headers=headers)
        response = self.conn.getresponse()
        if response.status != 200:
            raise ClientException(
                f'Could not set the {self._name} handler.')
        self.handler_set = True
        return json.loads(response.read())

    @check('handler_set', True, msg='Handler is not set.')
    def remove(self):
        headers = {'m-handler-name': self._name}
        self.conn.request('DELETE',
                          self.base_url,
                          headers=headers)
        response = self.conn.getresponse()
        if response.status != 200:
            raise ClientException(
                f'Could not remove the {self._name} handler.')
        self.handler_set = False
        return json.loads(response.read())

    def __repr__(self):
        return f'<Handler name={self._name}>'

    __str__ = __repr__


class App:
    def __init__(self, name, **kwargs):
        self._name = name
        self._id = None
        self.port = kwargs['port']
        self.conn = kwargs['conn']
        self.base_url = "/mock/app/"
        self.started = False

    @property
    def name(self):
        self._name

    @property
    def id(self):
        self._id

    @check('started', True, msg='App has not started.')
    def status(self):
        headers = {'m-app-id': self._id}
        self.conn.request('GET',
                          self.base_url,
                          headers=headers)
        response = self.conn.getresponse()
        if response.status != 200:
            raise ClientException(
                f'Could not get the app status.')
        return json.loads(response.read())

    @check('started', False, msg='App has not started.')
    def stop(self):
        headers = {'m-app-id': self._id}
        self.conn.request('DELETE',
                          self.base_url,
                          headers=headers)
        response = self.conn.getresponse()
        if response.status != 200:
            raise ClientException(
                f'Could not stop the app {self._name}.')
        self.started = False
        return json.loads(response.read())

    @check('started', False, msg='App has already started.')
    def start(self, config=None):
        config = config or {}
        headers = {'m-app-name': self._name, 'm-app-port': self.port}
        self.conn.request('POST',
                          self.base_url,
                          body=json.dumps(config),
                          headers=headers)
        response = self.conn.getresponse()
        if response.status != 200:
            raise ClientException(
                f'Could not start the app {self._name}.')
        self._id = response.headers['m-app-id']
        self.started = True
        return json.loads(response.read())

    @property
    @check('started', True, msg='App has not started.')
    def running(self):
        if self.status()['status'] == 'running':
            return True
        else:
            return False

    @check('started', True, msg='App has not started.')
    def handler(self, name, **kwargs):
        kwargs['conn'] = kwargs.get(
            'adapter', HTTPAdapter('0.0.0.0', self.port)).connect()
        return Handler(name, **kwargs)

    def __repr__(self):
        status = 'running' if self._running else 'stopped'
        return f'<App name={self._name} status={status}>'

    __str__ = __repr__


class Client:
    def __init__(self, adapter=HTTPAdapter('0.0.0.0', 8090)):
        self.adapter = adapter
        self.base_url = '/mock/'

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type, exec, tb):
        self.disconnect()

    def connect(self):
        self.adapter.connect()

    def disconnect(self):
        self.adapter.disconnect()

    def app(self, name, port, **kwargs):
        kwargs['conn'] = self.adapter.conn
        return App(name, port=port, **kwargs)

    def __repr__(self):
        return f'<Client adapter={self.adapter}>'

    __str__ = __repr__
