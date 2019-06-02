"""Bottle application manages Bottle server and handles
bottle requests.
"""
from __future__ import absolute_import

from app.base_app import BaseApp
from bottle import Bottle, run


class BottleApp(BaseApp):
    name = 'bottle'

    def __init__(self, config):
        self.app = Bottle()
        super().__init__(config)
        self.handler_data_map = {}

    def run(self, **kwargs):
        # self.app.register_middleware(
        #     self.request_middleware)
        self.app.run(**kwargs)

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
