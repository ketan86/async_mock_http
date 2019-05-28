"""Python Mock HTTP server.
"""
import logging
import os
from exceptions import AttachFailed, DetachFailed
from http.server import BaseHTTPRequestHandler, HTTPServer, HTTPStatus
from multiprocessing import Process, ProcessError

import click
from app.base_app import AppRegistry, BaseApp
from app.sanic_app import SanicApp
from app.flask_app import FlaskApp
from app.bottle_app import BottleApp
from utils import singleton

logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler())
logging.getLogger().handlers[0].setFormatter(logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'))

logger = logging.getLogger(__name__)

BASE_URL = '/mock/app/'


@singleton
class Server:
    def __init__(self):
        self._apps = {}

    @property
    def apps(self):
        return self._apps

    def is_alive(self, app):
        return self._apps[app].is_alive()

    def __contains__(self, app):
        return app in self._apps

    def attach(self, app, port):
        try:
            process = Process(target=app.run, kwargs={
                'port': port
            })
            process.daemon = True
            process.start()
            logger.info(
                f'Attached the app {app.name} to a server with an id {app.id}.'
            )
        except ProcessError:
            raise AttachFailed(f'Could not attach the app {app.name}')
        else:
            self._apps[app] = process

    def detach(self, app):
        try:
            self._apps[app].terminate()
            logger.info(
                f'Detached the app {app.name} from a server with an id {app.id}.')
        except ProcessError:
            raise DetachFailed(f'Could not detach the app {app.name}')
        else:
            del self._apps[app]


class MockHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_DELETE(self):
        if BASE_URL.find(self.path) == 0:
            self.handle_delete()

    def do_POST(self):
        if BASE_URL.find(self.path) == 0:
            logger.debug(f'Handing POST on {self.path}')
            self.handle_post()

    def do_GET(self):
        if BASE_URL.find(self.path) == 0:
            self.handle_get()

    def get_body(self):
        return self.rfile.read(int(self.headers.get('Content-Length')))

    def handle_get(self):
        app_name = self.headers.get('m-app-name', None)
        app_id = self.headers.get('m-app-id', None)

        if app_name is not None and app_id is not None:
            for app in Server().apps:
                if app.id == app_id and app.name == app_name:
                    if Server().is_alive(app):
                        self.send_response(
                            200, f'App {app.name} is running.')
                    else:
                        self.send_error(
                            500, f'App {app.name} is not running.')
                    break
            else:
                self.send_error(
                    404, 'App {} with id {} not found'.format(
                        app_name,
                        app_id))
        else:
            msg = 'Headers m-app-name and m-app-id not found.'
            logger.error(msg)
            self.send_error(500, msg)

    def handle_post(self):
        app_name = self.headers.get('m-app-name', None)
        app_port = self.headers.get('m-app-port', None)
        if app_name is not None and app_port is not None:
            try:
                app = getattr(AppRegistry, app_name.lower())(
                    self.get_body().decode())
            except AttributeError:
                msg = 'App {} is not supported'.format(app_name)
                logger.exception(msg)
                self.send_error(500, msg)
                return
            try:
                Server().attach(app, port=int(app_port))
            except AttachFailed as error:
                logger.exception(error)
                self.send_error(500, error)
            else:
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.send_response(200)
                self.wfile.write(app.id.encode())

        else:
            msg = 'Header m-app-name and m-app-port not found.'
            logger.error(msg)
            self.send_error(500, msg)

    def handle_delete(self):
        app_name = self.headers.get('m-app-name', None)
        app_id = self.headers.get('m-app-id', None)

        if app_name is not None and app_id is not None:
            for app in Server().apps:
                if app.id == app_id and app.name == app_name:
                    try:
                        Server().detach(app)
                    except DetachFailed as error:
                        logger.exception(error)
                        self.send_error(500, error)
                    else:
                        self.send_response(
                            200, 'App {} detached from the server.'.format(
                                app_name))
                    break
            else:
                self.send_error(
                    404, 'App {} with id {} not found'.format(
                        app_name,
                        app_id))
        else:
            msg = 'Headers m-app-name and m-app-id not found.'
            logger.error(msg)
            self.send_error(500, msg)


@click.command()
@click.argument('host', default='0.0.0.0', type=click.STRING)
@click.argument('port', default=8999, type=click.INT)
def run(host, port):
    server = HTTPServer((host, port), MockHTTPRequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        [Server().detach(app) for app in list(Server().apps)]
        server.server_close()


if __name__ == "__main__":
    run()
