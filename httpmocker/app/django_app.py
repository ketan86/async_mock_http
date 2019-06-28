"""Django application manages Django server and handles
django requests.
"""
from __future__ import absolute_import

import ast
import json
import logging
import sys
from functools import wraps
from http import HTTPStatus

from django.conf import LazySettings, settings
from django.core import management
from django.core.management import execute_from_command_line
from django.http import HttpResponse
from django.urls import path

from httpmocker.app.base_app import BaseApp
from httpmocker.handler import HANDLER_DATA_URL, HANDLER_URL, HandlerMixin

logger = logging.getLogger(__name__)

urlpatterns = []


def export_globally_as(name):
    def wrapper(func):
        module = sys.modules[__name__]
        setattr(module, name, func)
    return wrapper


def enforce_headers(headers):
    @wraps(headers)
    def decorated(func):
        def wrapper(request):
            for h in headers:
                if h not in request.headers:
                    return HttpResponse(
                        json.dumps({'error': f'{h} header is mandatory.'}),
                        status=HTTPStatus.BAD_REQUEST)
            return func(request)
        return wrapper
    return decorated


class DjangoApp(HandlerMixin, BaseApp):
    NAME = 'django'

    def __init__(self, config):
        super().__init__(config)
        settings.configure(ALLOWED_HOSTS=config.get('ALLOWED_HOSTS', ['*']),
                           ROOT_URLCONF='httpmocker.app.django_app',
                           DEBUG=config.get('ALLOWED_HOSTS', True),
                           **config)

    def reg_request_middleware(self):

        @export_globally_as('request_middleware')
        def request_middleware(get_response):
            def middleware(request):
                request.handler_data = self.handler_data.get(
                    request.path, {})
                response = get_response(request)
                return response
            return middleware

        settings.MIDDLEWARE = [
            'httpmocker.app.django_app.request_middleware']

    def reg_handler_route(self):

        @enforce_headers(['m-handler-name'])
        def handle_handler_data(request):
            handler_name = request.headers['m-handler-name']
            urlpatterns_name = request.headers.get(
                'm-urlpatterns-name', None) or 'urlpatterns'

            try:
                save_temp = True if request.method == "DELETE" else False
                module = self.import_handler(handler_name,
                                             request.body.decode(),
                                             save_temp=save_temp)
                paths = getattr(module, urlpatterns_name)
            except Exception:
                return HttpResponse(
                    json.dumps({'error': 'Invalid handler data.'}),
                    status=HTTPStatus.BAD_REQUEST)

            if request.method == "POST":
                for path in paths:
                    for _path in urlpatterns:
                        if str(path.pattern) == str(_path.pattern):
                            urlpatterns.remove(_path)
                            urlpatterns.append(path)
                            break
                    else:
                        urlpatterns.append(path)

                return HttpResponse(
                    json.dumps({'msg': 'View(s) registered/overridden.'}),
                    status=HTTPStatus.OK)

            elif request.method == "DELETE":
                not_deleted_paths = []
                for path in paths:
                    for _path in urlpatterns:
                        if str(path.pattern) == str(_path.pattern):
                            urlpatterns.remove(_path)
                            break
                    else:
                        not_deleted_paths.append(str(path.pattern))
                if not_deleted_paths:
                    return HttpResponse(
                        json.dumps({'msg': 'View(s) unregistered.',
                                    'de-registered_views': str(
                                        not_deleted_paths)
                                    }),
                        status=HTTPStatus.OK)
                return HttpResponse(
                    json.dumps({'msg': 'View(s) unregistered.'}),
                    status=HTTPStatus.OK)
            else:
                return HttpResponse(status=HTTPStatus.METHOD_NOT_ALLOWED)

        urlpatterns.append(path(HANDLER_URL[1:], handle_handler_data))

    def reg_handler_data_route(self):

        @enforce_headers(['m-handler-url'])
        def handle_data(request):
            url = request.headers['m-handler-url']
            if request.method == "GET":
                if url in self.handler_data:
                    return HttpResponse(
                        json.dumps(self.handler_data[url]),
                        status=HTTPStatus.OK)
                else:
                    return HttpResponse(
                        json.dumps(
                            {'msg': f'View data not found '
                             f'for \'{url}\' route.'}),
                        status=HTTPStatus.NOT_FOUND)
            elif request.method == "POST":
                self.handler_data[url] = json.loads(
                    request.body.decode())
                return HttpResponse(
                    json.dumps(
                        {'msg': f'View data registered for \'{url}\' route.'}),
                    status=HTTPStatus.OK)

            elif request.method == "DELETE":
                if url in self.handler_data:
                    del self.handler_data[url]
                    return HttpResponse(
                        json.dumps({'msg': 'View data deleted.'}),
                        status=HTTPStatus.OK)
                else:
                    return HttpResponse(
                        json.dumps(
                            {'msg': f'View data not found '
                             f'for \'{url}\' route.'}),
                        status=HTTPStatus.NOT_FOUND)
            else:
                return HttpResponse(status=HTTPStatus.METHOD_NOT_ALLOWED)

        urlpatterns.append(path(HANDLER_DATA_URL[1:], handle_data))

    def _derive_run_cmd(self, **kwargs):
        run_cmd = ['manage.py']

        if 'host' in kwargs:
            self._host = kwargs['host']
        self._port = kwargs['port']

        if ast.literal_eval(kwargs['enable_ssl']):
            run_cmd.append('runsslserver')
            settings.INSTALLED_APPS = ('sslserver',)
        else:
            run_cmd.append('runserver')

        run_cmd.append(f'{self._host}:{self._port}')
        run_cmd.append(kwargs.get('reload', '--noreload'))

        if ast.literal_eval(kwargs['enable_ssl']):
            run_cmd.extend(
                ['--certificate', self.ssl_cert, '--key', self.ssl_key])

        return run_cmd

    def run(self, **kwargs):
        run_cmd = self._derive_run_cmd(**kwargs)
        execute_from_command_line(run_cmd)
