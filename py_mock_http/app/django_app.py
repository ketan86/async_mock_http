"""Django application manages Django server and handles
django requests.
"""
from __future__ import absolute_import

import json
import logging
from http import HTTPStatus

from django.conf import LazySettings, settings
from django.core import management
from django.core.management import execute_from_command_line
from django.http import HttpResponse
from django.urls import path

from app.base_app import BaseApp
from handler import HANDLER_DATA_URL, HANDLER_URL, HandlerMixin

logger = logging.getLogger(__name__)

urlpatterns = []

global request_middleware
request_middleware = None


def export_at_module(func):
    global request_middleware
    request_middleware = func

    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
    return wrapper


class DjangoApp(BaseApp, HandlerMixin):
    HANDLER_LOCATION = './py_mock_http/handlers/django/'
    name = 'django'

    def __init__(self, config):
        super().__init__()
        settings.configure(ALLOWED_HOSTS=['*'],
                           ROOT_URLCONF='app.django_app',
                           DEBUG=True,
                           **config)

    def reg_request_middleware(self):
        @export_at_module
        def request_middleware(get_response):
            def middleware(request):
                print(type(request))
                request.handler_data = self.handler_data.get(
                    request.path, {})
                response = get_response(request)
                return response
            return middleware

        settings.MIDDLEWARE = [
            'app.django_app.request_middleware']

    def reg_handler_route(self):

        def handle_handler_data(request):
            handler_name = request.headers['m-handler-name']
            urlpatterns_name = request.headers.get(
                'm-urlpatterns-name', None) or 'urlpatterns'
            module = self.import_handler(handler_name,
                                         request.body.decode())
            paths = getattr(module, urlpatterns_name)

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
                    json.dumps({'msg': 'View registered.'}),
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
                        json.dumps({'msg': 'View unregistered.',
                                    'un_registered_views': str(
                                        not_deleted_paths)
                                    }),
                        status=HTTPStatus.OK)
                return HttpResponse(
                    json.dumps({'msg': 'View unregistered.'}),
                    status=HTTPStatus.OK)
            else:
                return HttpResponse(status=HTTPStatus.METHOD_NOT_ALLOWED)
        urlpatterns.append(path(HANDLER_URL[1:], handle_handler_data))

    def reg_handler_data_route(self):
        def handle_data(request):
            url = request.headers['m-handler-url']
            if request.method == "POST":
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
                            {'msg': 'View data not found for a given url.'}),
                        status=HTTPStatus.NOT_FOUND)
            else:
                return HttpResponse(status=HTTPStatus.METHOD_NOT_ALLOWED)
        urlpatterns.append(path(HANDLER_DATA_URL[1:], handle_data))

    def run(self, **kwargs):
        if 'host' in kwargs:
            self._host = kwargs['host']
        execute_from_command_line(
            ['manage.py', 'runserver', '0.0.0.0:' +
                str(kwargs['port']), '--noreload']
        )
