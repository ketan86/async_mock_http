"""Python Mock HTTP Client provides APIs to configure and
manage Mock HTTP Server remotely.
"""
from __future__ import absolute_import

import http
import importlib
from .exceptions import ClientException
from .config import DEFAULT_CONFIG

__all__ = ['Client']


class Client:
    def __init__(self, host, port="8888"):
        self.host = host
        self.port = port
        self.http_client = None

    def __enter__(self):
        self.connect()
        return self

    def __exit___(self, type, exec, tb):
        self.disconnect()

    def connect(self):
        try:
            self.http_client = http.client.HTTPConnection(
                self.host, self.port,
                timeout=DEFAULT_CONFIG['SERVER_REQUEST_TIMEOUT']
            )
        except http.client.HTTPException:
            raise ClientException(r'Could not connect to server {self.host}')

    def update_config():
        pass

    def start_server(self):
        pass

    def stop_server(self):
        pass

    def restart_server(self):
        pass

    def set_handler(self, path):
        pass

    def __str__(self):
        return "<Client>"
