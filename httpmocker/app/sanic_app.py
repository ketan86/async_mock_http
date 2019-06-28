"""Sanic application manages Sanic server and handles
sanic requests.
"""
from __future__ import absolute_import

import ast
import json
import logging
from functools import wraps
from http import HTTPStatus

from httpmocker.app.base_app import BaseApp
from httpmocker.handler import HANDLER_DATA_URL, HANDLER_URL, HandlerMixin
from sanic import Blueprint, Sanic, request, response
from sanic.exceptions import SanicException
from sanic.router import RouteDoesNotExist, RouteExists

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
    NAME = 'sanic'

    def __init__(self, config):
        super().__init__(config)
        self.app = Sanic()
        self.app.config.update(**config)

    def reg_request_middleware(self):
        @self.app.middleware('request')
        def request_middleware(request):
            request['handler_data'] = self.handler_data.get(
                request.raw_url.decode(), {})

    def _remove_routes(self, bp):
        # clear all routes from the app.
        for route in self.app.blueprints[bp.name].routes:
            # if strict slash enforced, only delete the given route,
            # otherwise, delete one with slash also.
            if route.strict_slashes:
                routes_to_delete = [route.uri]
            else:
                routes_to_delete = [route.uri, route.uri + '/']
            for route_uri in routes_to_delete:
                if route_uri in self.app.router.routes_all:
                    logger.debug(f'Removing {route_uri} route from the app.')
                    self.app.remove_route(route_uri)

        # clear routes from blueprint
        self.app.blueprints[bp.name].routes.clear()
        # delete the blueprint
        del self.app.blueprints[bp.name]

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
                logger.exception(error)
                return response.json({'error': str(error)},
                                     status=HTTPStatus.BAD_REQUEST)

            try:
                self.app.blueprint(bp)
            except (AssertionError, RouteExists,
                    RouteDoesNotExist, SanicException) as error:
                logger.exception(error)
                return response.json({'error': str(error)},
                                     status=HTTPStatus.CONFLICT)

            logger.info('Blueprint successfully registered.')
            return response.json({'msg': 'Blueprint registered.'},
                                 status=HTTPStatus.OK)

        @self.app.route(HANDLER_URL, methods=['DELETE'])
        @enforce_headers(['m-handler-name'])
        def remove_blueprint(request):
            handler_name = request.headers['m-handler-name']
            blueprint_name = request.headers.get(
                'm-blueprint-name', None) or 'bp'
            try:
                module = self.import_handler(handler_name,
                                             request.body.decode(),
                                             save_temp=True)
                bp = getattr(module, blueprint_name)
            except (ImportError, AttributeError) as error:
                logger.exception(error)
                return response.json({'error': str(error)},
                                     status=HTTPStatus.BAD_REQUEST)
            try:
                self._remove_routes(bp)
            except (KeyError, RouteExists, RouteDoesNotExist) as error:
                logger.exception(error)
                return response.json(
                    {'error': f'Blueprint not found with the name {bp.name}'},
                    status=HTTPStatus.CONFLICT)
            except SanicException as error:
                logger.exception(error)
                return response.json({'error': str(error)},
                                     status=HTTPStatus.CONFLICT)

            logger.info('Blueprint successfully de-registered.')
            return response.json({'msg': 'Blueprint unregistered.'},
                                 status=HTTPStatus.OK)

    def reg_handler_data_route(self):

        @self.app.route(HANDLER_DATA_URL, methods=['GET'])
        @enforce_headers(['m-handler-url'])
        def set_blueprint_data(request):
            url = request.headers['m-handler-url']
            print(self.app.router.routes_all.keys())
            if url in self.handler_data:
                msg = f'Data found for \'{url}\' route.'
                logger.info(msg)
                return response.json(
                    self.handler_data[url],
                    status=HTTPStatus.OK)

            msg = 'Blueprint data not found for \'{url}\' route.'
            logger.info(msg)
            return response.json({'msg': msg}, status=HTTPStatus.NOT_FOUND)

        @self.app.route(HANDLER_DATA_URL, methods=['POST'])
        @enforce_headers(['m-handler-url'])
        def set_blueprint_data(request):
            url = request.headers['m-handler-url']
            print(self.app.router.routes_all.keys())
            for route in self.app.router.routes_all.keys():
                if url == route:
                    self.handler_data[url] = json.loads(request.body.decode())
                    msg = f'Data registered for \'{url}\' route.'
                    logger.info(msg)
                    return response.json({'msg': msg}, status=HTTPStatus.OK)

            msg = 'Route not found.'
            logger.info(msg)
            return response.json({'msg': msg}, status=HTTPStatus.NOT_FOUND)

        @self.app.route(HANDLER_DATA_URL, methods=['DELETE'])
        @enforce_headers(['m-handler-url'])
        def delete_blueprint_data(request):
            url = request.headers['m-handler-url']
            if url in self.handler_data:
                del self.handler_data[url]
                msg = 'Blueprint data deleted.'
                return response.json({'msg': msg}, status=HTTPStatus.OK)
            else:
                msg = 'Blueprint data not found for \'{url}\' route.'
                return response.json({'msg': msg}, status=HTTPStatus.NOT_FOUND)

    def run(self, **kwargs):
        if 'host' in kwargs:
            self._host = kwargs['host']

        if ast.literal_eval(kwargs['enable_ssl']):
            kwargs.update(
                {'ssl': {'cert': self.ssl_cert, 'key': self.ssl_key}})

        self._port = kwargs['port']
        self.app.run(**kwargs)
