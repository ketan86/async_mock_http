"""Flask application manages Flask server and handles
flask requests.
"""
from __future__ import absolute_import

import ast
import json
import logging
from http import HTTPStatus

from flask import Blueprint, Flask, jsonify, make_response, request
from httpmocker.app.base_app import BaseApp
from httpmocker.handler import HANDLER_DATA_URL, HANDLER_URL, HandlerMixin

logger = logging.getLogger(__name__)


def enforce_headers(headers):
    @wraps(headers)
    def decorated(func):
        def wrapper(*args, **kwargs):
            print(args)
            for h in headers:
                if h not in request.headers:
                    return make_response(
                        jsonify(error=f'{h} header is mandatory.'),
                        HTTPStatus.BAD_REQUEST)
            return func(*args, **kwargs)
        return wrapper
    return decorated


class FlaskApp(HandlerMixin, BaseApp):
    NAME = 'flask'

    def __init__(self, config):
        super().__init__(config)
        self.app = Flask(__name__)
        self.app.config.update(**config)

    def reg_request_middleware(self):
        @self.app.before_request
        def request_middleware():
            request.handler_data = self.handler_data.get(
                request.path, {})

    def _remove_bp(self, bp):
        for view in list(self.app.view_functions.keys()):
            if bp.name in view:
                del self.app.view_functions[view]
                break
        else:
            raise KeyError(f'Blueprint with {bp.name} name not found.')

        if bp.name in self.app.blueprints:
            del self.app.blueprints[bp.name]
        else:
            raise KeyError(f'Blueprint with {bp.name} name not found.')

    def reg_handler_route(self):
        @self.app.route(HANDLER_URL, methods=['POST'])
        def add_blueprint():
            handler_name = request.headers['m-handler-name']
            blueprint_name = request.headers.get(
                'm-blueprint-name', None) or 'bp'

            try:
                module = self.import_handler(handler_name,
                                             request.data.decode())
                bp = getattr(module, blueprint_name)
            except Exception:
                return make_response(jsonify(error='Invalid handler data.'),
                                     HTTPStatus.BAD_REQUEST)

            try:
                self.app.register_blueprint(bp)
            except (AssertionError) as error:
                return make_response(jsonify(msg=str(error)),
                                     HTTPStatus.CONFLICT)
            return make_response(jsonify(msg='Blueprint registered.'),
                                 HTTPStatus.OK)

        @self.app.route(HANDLER_URL, methods=['DELETE'])
        def delete_blueprint():
            handler_name = request.headers['m-handler-name']
            blueprint_name = request.headers.get(
                'm-blueprint-name', None) or 'bp'

            try:
                module = self.import_handler(handler_name,
                                             request.data.decode())
                bp = getattr(module, blueprint_name)
            except Exception:
                return make_response(jsonify(error='Invalid handler data.'),
                                     HTTPStatus.BAD_REQUEST)
            try:
                self._remove_bp(bp)
            except (AssertionError, KeyError) as error:
                return make_response(jsonify(msg=str(error)),
                                     HTTPStatus.NOT_FOUND)
            return make_response(jsonify(msg='Blueprint de-registered.'),
                                 HTTPStatus.OK)

    def reg_handler_data_route(self):

        @self.app.route(HANDLER_DATA_URL, methods=['GET'])
        def get_blueprint_data():
            url = request.headers['m-handler-url']
            if url in self.handler_data:
                return make_response(json.dumps(self.handler_data[url]),
                                     HTTPStatus.OK)
            else:
                return make_response(jsonify(
                    msg=f'Blueprint data not found for a given url.'),
                    HTTPStatus.NOT_FOUND)

        @self.app.route(HANDLER_DATA_URL, methods=['POST'])
        def set_blueprint_data():
            url = request.headers['m-handler-url']
            for rule in self.app.url_map.iter_rules():
                print(rule.rule, url)
                print(type(rule), type(url))
                if rule.rule == url:
                    self.handler_data[url] = json.loads(
                        request.data.decode())
                    return make_response(jsonify(
                        msg=f'Data registered for \'{url}\' route.'),
                        HTTPStatus.OK)
            return make_response(jsonify(
                msg=f'Route not found.'),
                HTTPStatus.NOT_FOUND)

        @self.app.route(HANDLER_DATA_URL, methods=['DELETE'])
        def delete_blueprint_data():
            url = request.headers['m-handler-url']
            if url in self.handler_data:
                del self.handler_data[url]
                return make_response(jsonify(
                    msg=f'Blueprint data deleted.'),
                    HTTPStatus.OK)
            else:
                return make_response(jsonify(
                    msg=f'Blueprint data not found for a given url.'),
                    HTTPStatus.NOT_FOUND)

    def run(self, **kwargs):
        if 'host' in kwargs:
            self._host = kwargs['host']
        self._port = kwargs['port']

        if ast.literal_eval(kwargs['enable_ssl']):
            kwargs.update(
                {'ssl_context': (self.ssl_cert, self.ssl_key)})

        kwargs.pop('enable_ssl', None)

        self.app.run(**kwargs)
