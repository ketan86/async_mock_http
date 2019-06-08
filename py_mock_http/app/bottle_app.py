"""Bottle application manages Bottle server and handles
bottle requests.
"""
from __future__ import absolute_import
import json
from http import HTTPStatus
import logging
from app.base_app import BaseApp
from handler import HANDLER_DATA_URL, HANDLER_URL, HandlerMixin
from bottle import Bottle, run, request, HTTPResponse
logger = logging.getLogger(__name__)

app = Bottle()


class BottleApp(HandlerMixin, BaseApp):
    HANDLER_LOCATION = './py_mock_http/handlers/bottle/'
    name = 'bottle'

    def __init__(self, config):
        super().__init__()
        self.app = Bottle()
        self.app.config.update(**config)

    def reg_request_middleware(self):
        @self.app.hook('before_request')
        def request_middleware():
            if request.url.decode() in self.handler_data:
                request.handler_data = self.handler_data[
                    request.url.decode()]

    def run(self, **kwargs):
        if 'host' in kwargs:
            self._host = kwargs['host']
        self._port = kwargs['port']
        self.app.run(**kwargs)

    def reg_handler_route(self):
        pass
            
    def request_middleware(self, request):
        if request.raw_url.decode() in self.handler_data_map:
            request['handler_data'] = self.handler_data_map[
                request.raw_url.decode()]

    def register_blueprint(self, request):
        self.store_handler(request)
        handler_name = request.headers['m-handler-name']
        m = importlib.import_module(
            '.' + handler_name,
            'py_mock_http.handler')
        importlib.reload(m)

        bp = getattr(m, 'bp')
        try:
            self.app.blueprint(bp)
        except AssertionError:
            return response.text('BAD')
        return response.text('OK')

    def register_handler(self):
        self.app.add_route(self.register_blueprint,
                           Handler.url,
                           methods=['POST'])

    def unregister_blueprint(self, request):
        return response.text('OK')

    def unregister_handler(self):
        self.app.add_route(self.unregister_blueprint,
                           Handler.url,
                           methods=['DELETE'])

    def set_blueprint_data(self, request):
        url = request.headers['m-url']
        self.handler_data_map[url] = json.loads(
            request.body.decode())
        return response.text('OK')

    def register_handler_data(self):
        self.app.add_route(self.set_blueprint_data,
                           Handler.url,
                           methods=['PUT'])

    def handle_stop(self, request):
        self.app.stop()

    def register_stop(self):
        self.app.add_route(self.handle_stop,
                           Server.url,
                           methods=['DELETE'])
