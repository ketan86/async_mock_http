import logging
import os
import re
import json
from exceptions import AppAttachFailed, AppDetachFailed
from http.server import BaseHTTPRequestHandler, HTTPServer, HTTPStatus
from http import HTTPStatus
from multiprocessing import Process, ProcessError
import click
from app.base_app import AppRegistry
from utils import singleton

logger = logging.getLogger(__name__)

BASE_URL = '/mock/'


@singleton
class Server:
    def __init__(self, config=None):
        self._apps = {}
        self.config = config

    @property
    def apps(self):
        return self._apps

    def _is_alive(self, app):
        return self._apps[app].is_alive()

    def __contains__(self, app):
        return app in self._apps

    def attach(self, app, port):
        try:
            process = Process(target=app.run, kwargs={
                'port': port
            }, daemon=True)
            process.start()
            # If process is alive after 5 secs, consider
            # the app running.
            process.join(5)
            if process.is_alive():
                logger.info(
                    f'Attached {app.name} app to a server with an id {app.id}.'
                )
            else:
                raise AppAttachFailed(f'Could not attach the app {app.name}')
        except (ProcessError):
            raise AppAttachFailed(f'Could not attach the app {app.name}')
        else:
            self._apps[app] = process

    def detach(self, app):
        try:
            self._apps[app].terminate()
            logger.info(
                f'Detached {app.name} app from a server with an id {app.id}.')
        except ProcessError:
            raise AppDetachFailed(f'Could not detach the app {app.name}')
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
                self.send_response(HTTPStatus.NOT_FOUND,
                                   f'App not found.')
                self.end_headers()

        else:
            self.send_response(HTTPStatus.BAD_REQUEST,
                               'm-app-id not found.')
            self.end_headers()

    def create_app(self):
        app_name = self.headers.get('m-app-name')
        app_port = self.headers.get('m-app-port')
        if app_name is not None and app_port is not None:
            try:
                app = getattr(AppRegistry, app_name.lower())(
                    json.loads(self.get_body().decode()))
            except AttributeError:
                msg = f'App {app_name} is not supported'
                logger.exception(msg)
                self.send_response(HTTPStatus.NOT_FOUND, msg)
                self.end_headers()
                return
            try:
                Server().attach(app, port=int(app_port))
            except (AppAttachFailed, OSError) as error:
                logger.exception(error)
                self.send_response(HTTPStatus.INTERNAL_SERVER_ERROR, error)
                self.end_headers()
                return
            else:
                self.send_response(HTTPStatus.OK)
                self.send_header('m-app-id', app.id)
                self.end_headers()
                self.wfile.write(json.dumps(
                    {'msg': f'{app.name} app created.'}).encode())
        else:
            self.send_response(HTTPStatus.BAD_REQUEST,
                               'm-app-name and m-app-port not found.')
            self.end_headers()

    def delete_app(self):
        app_id = self.headers.get('m-app-id')

        if app_id is not None:
            for app in Server().apps:
                if app.id == app_id:
                    try:
                        Server().detach(app)
                    except AppDetachFailed as error:
                        self.send_response(
                            HTTPStatus.INTERNAL_SERVER_ERROR, error)
                        self.end_headers()

                    else:
                        self.send_response(
                            HTTPStatus.OK, 'App {} detached from the server.'.format(
                                app.name))
                        self.end_headers()

                    break
            else:
                self.send_response(
                    HTTPStatus.NOT_FOUND, 'App not found.')
                self.end_headers()

        else:
            self.send_response(HTTPStatus.BAD_REQUEST,
                               'm-app-id not found.')
            self.end_headers()


def configure_logging(**kwargs):
    log_level = kwargs['log_level']
    level = getattr(logging, log_level)
    handler = logging.FileHandler('./server.log')
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s')
    handler.setFormatter(formatter)
    logging.getLogger().handlers.append(handler)
    logging.getLogger().setLevel(level)


@click.command()
@click.option('--debug', default=True, type=click.BOOL)
@click.option('--config', default=None, type=click.STRING)
@click.argument('host', default='0.0.0.0', type=click.STRING)
@click.argument('port', default=8090, type=click.INT)
def run(host, port, config, debug):
    if debug:
        configure_logging(log_level='DEBUG')
    if config:
        Server(json.loads(config))

    server = HTTPServer((host, port), MockHTTPRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info('KeyboardInterrupt. Detaching all apps.')
        [Server().detach(app) for app in list(Server().apps)]
        server.server_close()


if __name__ == "__main__":
    run()
