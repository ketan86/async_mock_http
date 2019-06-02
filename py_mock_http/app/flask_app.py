"""Flask application manages Flask server and handles
flask requests.
"""
from __future__ import absolute_import

import json
from http import HTTPStatus
import logging
from app.base_app import BaseApp
from handler import HANDLER_DATA_URL, HANDLER_URL, HandlerMixin
from flask import Flask, request, make_response, jsonify, Blueprint
logger = logging.getLogger(__name__)


class FlaskApp(BaseApp, HandlerMixin):
    HANDLER_LOCATION = './py_mock_http/handlers/flask/'
    name = 'flask'

    def __init__(self, config):
        super().__init__()
        self.app = Flask(__name__)
        self.app.config.update(**config)

    def reg_request_middleware(self):
        @self.app.before_request
        def request_middleware():
            logger.info(f'request url is {request.path}')
            logger.info(f'handler_data is {self.handler_data}')
            if request.path in self.handler_data:
                request.handler_data = self.handler_data[
                    request.path]

    def reg_handler_route(self):
        @self.app.route(HANDLER_URL, methods=['POST'])
        def add_blueprint():
            handler_name = request.headers['m-handler-name']
            blueprint_name = request.headers.get(
                'm-blueprint-name', None) or 'bp'

            module = self.import_handler(handler_name,
                                         request.data.decode())
            bp = getattr(module, blueprint_name)
            try:
                self.app.register_blueprint(bp)
            except (AssertionError) as error:
                return make_response(jsonify(message=str(error)),
                                     HTTPStatus.CONFLICT)
            return make_response(jsonify(message='Blueprint registered.'),
                                 HTTPStatus.OK)

    def reg_handler_data_route(self):
        @self.app.route(HANDLER_DATA_URL, methods=['POST'])
        def set_blueprint_data():
            url = request.headers['m-handler-url']
            self.handler_data[url] = json.loads(
                request.data.decode())
            return make_response(jsonify(
                message=f'Data registered for \'{url}\' route.'),
                HTTPStatus.OK)

        @self.app.route(HANDLER_DATA_URL, methods=['DELETE'])
        def delete_blueprint_data():
            url = request.headers['m-handler-url']
            if url in self.handler_data:
                del self.handler_data[url]
                return make_response(jsonify(
                    message=f'Blueprint data deleted.'),
                    HTTPStatus.OK)
            else:
                return make_response(jsonify(
                    message=f'Blueprint data not found for a given url.'),
                    HTTPStatus.NOT_FOUND)

    def run(self, **kwargs):
        if 'host' in kwargs:
            self._host = kwargs['host']
        self._port = kwargs['port']

        self.app.run(**kwargs)
