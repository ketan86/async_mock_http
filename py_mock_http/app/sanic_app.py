"""Sanic application manages Sanic server and handles
sanic requests.
"""
from __future__ import absolute_import

import json
from uuid import uuid4

from app.base_app import BaseApp
from sanic import Sanic, response
from handler import AbstractHandler, HANDLER_URL, HANDLER_DATA_URL


class SanicApp(BaseApp, AbstractHandler):
    name = 'sanic'

    def __init__(self, config):
        self.app = Sanic()
        BaseApp.__init__(self, config)

    def handle_blueprint(self, request):
        handler_name = request.headers['m-handler-name']
        handler_body = request.body.decode()
        module = self.load_handler(handler_name,
                                   handler_body)
        bp = getattr(module, 'bp')
        try:
            self.app.blueprint(bp)
        except AssertionError:
            return response.text('BAD')
        return response.text('OK')

    def register_for_handler(self):
        self.app.add_route(self.handle_blueprint,
                           uri=HANDLER_URL,
                           methods=['POST'])

    def set_blueprint_data(self, request):
        url = request.headers['m-handler-url']
        self.handler_data[url] = json.loads(
            request.body.decode())
        return response.text('OK')

    def register_for_handler_data(self):
        self.app.add_route(self.set_blueprint_data,
                           uri=HANDLER_DATA_URL,
                           methods=['POST'])

    def run(self, **kwargs):
        self.app.register_middleware(
            self.request_middleware)
        self.app.run(**kwargs)

    def request_middleware(self, request):
        if request.raw_url.decode() in self.handler_data:
            request['handler_data'] = self.handler_data[
                request.raw_url.decode()]
