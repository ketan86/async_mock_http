"""Flask application manages Flask server and handles
flask requests.
"""
from __future__ import absolute_import

import importlib
import json
from uuid import uuid4
import logging
from app.base_app import BaseApp
from handler import AbstractHandler, HANDLER_URL, HANDLER_DATA_URL
from flask import Flask, request, make_response, jsonify

logger = logging.getLogger(__name__)


class FlaskApp(BaseApp, AbstractHandler):
    name = 'flask'

    def __init__(self, config):
        self.app = Flask(__name__)
        BaseApp.__init__(self, config)

    def run(self, **kwargs):
        self.app.before_request(self.request_middleware)
        self.app.run(**kwargs)

    def request_middleware(self):
        logger.info(f'request url is {request.path}')
        logger.info(f'handler_data is {self.handler_data}')
        if request.path in self.handler_data:
            request.handler_data = self.handler_data[
                request.path]

    def handle_blueprint(self):
        handler_name = request.headers['m-handler-name']
        handler_body = request.data.decode()
        module = self.load_handler(handler_name,
                                   handler_body)
        bp = getattr(module, 'bp')
        self.app.register_blueprint(bp)
        return make_response(jsonify(message='blueprint registered'), 201)

    def register_for_handler(self):
        self.app.add_url_rule(HANDLER_URL,
                              view_func=self.handle_blueprint,
                              methods=['POST'])

    def set_blueprint_data(self):
        url = request.headers['m-handler-url']
        self.handler_data[url] = json.loads(
            request.data.decode())
        return make_response(jsonify(message='blueprint data set'), 201)

    def register_for_handler_data(self):
        self.app.add_url_rule(HANDLER_DATA_URL,
                              view_func=self.set_blueprint_data,
                              methods=['POST'])
