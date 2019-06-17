import json
import logging
import os
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer, HTTPStatus
from multiprocessing import Process, ProcessError

import click
from httpmocker.app.base_app import AppRegistry
from httpmocker.exceptions import AppStartFailed, AppStopFailed
from httpmocker.utils import singleton
from httpmocker.log import configure_logging
from httpmocker.config import get_config

logger = logging.getLogger(__name__)

BASE_URL = '/mock/'


@singleton
class Server:
    """Manages applications."""

    def __init__(self, config=None):
        """Initialize the server with configurations.

        :param dict config: server configurations, Defaults -> None
        """
        self._apps = {}
        self.config = config or {}

    @property
    def apps(self):
        """Retrive running applications.

        :return: list of application instances.
        :rtype: list
        """
        return self._apps

    def _is_alive(self, app):
        """Check the application status.

        :param BaseApp app: application instance.
        :return: True if alive else False
        :rtype: bool
        """
        return self._apps[app].is_alive()

    def start(self, app, port, **kwargs):
        """Start the application on given port.

        :param BaseApp app: application instance.
        :param str port: port to attach to.
        :param bool ssl: enable ssl.
        :raises AppStartFailed: when application fails to start.
        """
        try:
            process = Process(target=app.run, kwargs={
                'port': port,
                'enable_ssl': kwargs.get('enable_ssl', 'False')
            }, daemon=True)
            process.start()
            # If process is alive after 5 secs, consider
            # the app running.
            process.join(5)
            if process.is_alive():
                logger.info(
                    f'{app.name} app started on port {port}.'
                )
            else:
                raise AppStartFailed(
                    f'Could not start the {app.name} app on port {port}.')
        except (ProcessError):
            raise AppStartFailed(
                f'Could not start the {app.name} app on port {port}.')
        else:
            self._apps[app] = process

    def stop(self, app):
        """Stop the application.

        :param BaseApp app: application instance.
        :raises AppStopFailed: when application fails to stop.
        """
        try:
            self._apps[app].terminate()
            logger.info(
                f'{app.name} app stopped.')
        except ProcessError:
            raise AppStopFailed(f'Could not stop the app {app.name}')
        else:
            del self._apps[app]


class MockHTTPRequestHandler(BaseHTTPRequestHandler):
    MOCK_APP_URL = re.compile(r'^\/mock\/app\/*$')

    def do_DELETE(self):
        if self.MOCK_APP_URL.match(self.path):
            logger.debug(f'Handing {self.command} on {self.path}')
            self.delete_app()

    def do_POST(self):
        if self.MOCK_APP_URL.match(self.path):
            logger.debug(f'Handing {self.command} on {self.path}')
            self.create_app()

    def do_GET(self):
        if self.MOCK_APP_URL.match(self.path):
            logger.debug(f'Handing {self.command} on {self.path}')
            self.get_app()

    def get_body(self):
        return self.rfile.read(int(self.headers.get('Content-Length')))

    def get_app(self):
        app_id = self.headers.get('m-app-id')
        if app_id is not None:
            for app in Server().apps:
                if app.id == app_id:
                    if Server()._is_alive(app):
                        self.send_response(HTTPStatus.OK)
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            'status': 'running',
                            'host': app.host,
                            'port': app.port
                        }).encode())
                    else:
                        self.send_response(HTTPStatus.NOT_FOUND)
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            'msg': f'{app.name} app not running.'
                        }).encode())
                    break
            else:
                self.send_response(HTTPStatus.NOT_FOUND)
                self.end_headers()
                self.wfile.write(
                    json.dumps({'error': 'App not found.'}).encode())

        else:
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.end_headers()
            self.wfile.write(json.dumps(
                {'error': 'm-app-id not found.'}).encode())

    def create_app(self):
        app_name = self.headers.get('m-app-name')
        app_port = self.headers.get('m-app-port')
        app_enable_ssl = self.headers.get('m-app-enable-ssl', 'False')

        if app_name is not None and app_port is not None:
            try:
                app = getattr(AppRegistry, app_name.lower())(
                    json.loads(self.get_body().decode()))
            except AttributeError:
                msg = f'App {app_name} is not supported'
                logger.exception(msg)
                self.send_response(HTTPStatus.NOT_FOUND)
                self.end_headers()
                self.wfile.write(json.dumps({'error': msg}).encode())
                return
            except Exception as error:
                logger.exception(error)
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(error)}).encode())
                return

            try:
                Server().start(app, port=int(app_port),
                               enable_ssl=app_enable_ssl)
            except (AppStartFailed, OSError) as error:
                logger.exception(error)
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(error)}).encode())
                return
            else:
                self.send_response(HTTPStatus.OK)
                self.send_header('m-app-id', app.id)
                self.end_headers()
                self.wfile.write(json.dumps(
                    {'msg': f'{app.name} app created.'}).encode())
        else:
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.end_headers()
            self.wfile.write(json.dumps(
                {'error': 'm-app-name and m-app-port not found.'}).encode())

    def delete_app(self):
        app_id = self.headers.get('m-app-id')

        if app_id is not None:
            for app in Server().apps:
                if app.id == app_id:
                    try:
                        Server().stop(app)
                    except AppStopFailed as error:
                        self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR)
                        self.end_headers()
                        self.wfile.write(
                            json.dumps({'error': str(error)}).encode())
                    else:
                        self.send_response(HTTPStatus.OK)
                        self.end_headers()
                        self.wfile.write(json.dumps(
                            {'msg': 'App {} stopped.'.format(
                                    app.name)}).encode())

                    break
            else:
                self.send_response(HTTPStatus.NOT_FOUND)
                self.end_headers()
                self.wfile.write(json.dumps(
                    {'error': 'App not found.'}).encode())

        else:
            self.send_response(HTTPStatus.BAD_REQUEST)
            self.end_headers()
            self.wfile.write(json.dumps(
                {'error': 'm-app-id not found.'}).encode())


@click.command()
@click.argument('host', default='0.0.0.0', type=click.STRING)
@click.argument('port', default=8080, type=click.INT)
def run(host, port):
    config = get_config()
    host = config.get('HOST', host)
    port = int(config.get('PORT', port))

    server = Server(config)

    http_server = HTTPServer((host, port), MockHTTPRequestHandler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt. Stopping all apps.')
        for app in list(server.apps):
            server.stop(app)
        http_server.server_close()


if __name__ == '__main__':
    run()
