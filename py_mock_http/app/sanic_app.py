"""Sanic application manages Sanic server and handles
sanic requests.
"""
from __future__ import absolute_import

import json
from http import HTTPStatus
import logging
from functools import wraps
from app.base_app import BaseApp
from handler import HANDLER_DATA_URL, HANDLER_URL, HandlerMixin
from sanic import Sanic, request, response, Blueprint
from sanic.exceptions import SanicException
from sanic.router import RouteExists


logger = logging.getLogger(__name__)


def enforce_headers(headers):
    @wraps(headers)
    def decorated(func):
        def wrapper(request):
            for h in headers:
                if h not in request.headers:
                    return response.json(
                        {'error': f'{h} header is mandatory.'},
                        status=HTTPStatus.BAD_REQUEST)
            return func(request)
        return wrapper
    return decorated


class SanicApp(HandlerMixin, BaseApp):
    HANDLER_LOCATION = './py_mock_http/handlers/sanic/'
    name = 'sanic'

    def __init__(self, config):
        super().__init__()
        self.app = Sanic()
        self.app.config.update(**config)

    def reg_request_middleware(self):
        @self.app.middleware('request')
        def request_middleware(request):
            request['handler_data'] = self.handler_data.get(
                request.raw_url.decode(), {})
            logger.info(
                f'Setting handler data on {request.raw_url.decode()} route.')

    def reg_handler_route(self):
        @self.app.route(HANDLER_URL, methods=['POST'])
        @enforce_headers(['m-handler-name'])
        def add_blueprint(request):
            handler_name = request.headers['m-handler-name']
            blueprint_name = request.headers.get(
                'm-blueprint-name', None) or 'bp'
            try:
                module = self.import_handler(handler_name,
                                             request.body.decode())
                bp = getattr(module, blueprint_name)
            except (ImportError, AttributeError) as error:
                return response.json(
                    {'error': str(error)},
                    status=HTTPStatus.BAD_REQUEST)
            try:
                self.app.blueprint(bp)
            except (AssertionError, RouteExists) as error:
                _bp = self.app.blueprints[bp.name]
                _bp.routes.clear()
                self.app.blueprint(bp)
            except SanicException as error:
                return response.json(
                    {'error': str(error)},
                    status=HTTPStatus.CONFLICT)
            return response.json(
                {'msg': 'Blueprint registered.'},
                status=HTTPStatus.OK)

        @self.app.route(HANDLER_URL, methods=['DELETE'])
        @enforce_headers(['m-handler-name'])
        def remove_blueprint(request):
            handler_name = request.headers['m-handler-name']
            blueprint_name = request.headers.get(
                'm-blueprint-name', None) or 'bp'
            try:
                module = self.import_handler(handler_name,
                                             request.body.decode())
                bp = getattr(module, blueprint_name)
            except (ImportError, AttributeError) as error:
                return response.json(
                    {'error': str(error)},
                    status=HTTPStatus.BAD_REQUEST)
            try:
                _bp = self.app.blueprints[bp.name]
                _bp.routes.clear()
                del self.app.blueprints[bp.name]
            except SanicException as error:
                return response.json(
                    {'error': str(error)},
                    status=HTTPStatus.CONFLICT)
            return response.json(
                {'msg': 'Blueprint unregistered.'},
                status=HTTPStatus.OK)

    def reg_handler_data_route(self):
        @self.app.route(HANDLER_DATA_URL, methods=['POST'])
        @enforce_headers(['m-handler-url'])
        def set_blueprint_data(request):
            url = request.headers['m-handler-url']
            for bp in self.app.blueprints:
                logger.debug(
                    f'Blueprint {bp} routes {self.app.blueprints[bp].routes}'
                )
                for route in self.app.blueprints[bp].routes:
                    if url == route.uri:
                        self.handler_data[url] = json.loads(
                            request.body.decode())
                        return response.json(
                            {'msg': f'Data registered for \'{url}\' route.'},
                            status=HTTPStatus.OK)

            return response.json(
                {'msg': 'Route not found.'},
                status=HTTPStatus.NOT_FOUND)

        @self.app.route(HANDLER_DATA_URL, methods=['DELETE'])
        @enforce_headers(['m-handler-url'])
        def delete_blueprint_data(request):
            url = request.headers['m-handler-url']
            if url in self.handler_data:
                del self.handler_data[url]
                return response.json(
                    {'msg': 'Blueprint data deleted.'},
                    status=HTTPStatus.OK)
            else:
                return response.json(
                    {'msg': 'Blueprint data not found for a given url.'},
                    status=HTTPStatus.NOT_FOUND
                )

    def run(self, **kwargs):
        if 'host' in kwargs:
            self._host = kwargs['host']
        self._port = kwargs['port']
        self.app.run(**kwargs)
