import abc
import importlib
from functools import wraps
import os
from contextlib import contextmanager

HANDLER_URL = '/mock/app/handler/'
HANDLER_DATA_URL = '/mock/app/handler/data/'


def register_handler_routes(*args, **kwargs):
    def decorator(func):
        @wraps(func)
        def wrapper(cls, *args, **kwargs):
            obj = func(cls, *args, **kwargs)
            obj.reg_handler_route()
            obj.reg_handler_data_route()
            obj.reg_request_middleware()
            return obj
        return wrapper
    return decorator


class AbstractHandler:

    @abc.abstractmethod
    def reg_request_middleware(self):
        raise NotImplementedError

    @abc.abstractmethod
    def reg_handler_data_route(self):
        raise NotImplementedError

    @abc.abstractmethod
    def reg_handler_route(self):
        raise NotImplementedError


class HandlerMixin:
    HANDLER_LOCATION = './py_mock_http/handlers/'

    @contextmanager
    def save_handler(self, name, data, temp=False):
        if temp:
            location = self.HANDLER_LOCATION + '/tmp/'
        else:
            location = self.HANDLER_LOCATION
        file_location = location + '/' + name + '.py'
        if not os.path.exists(location):
            os.makedirs(location, exist_ok=True)

        with open(file_location, 'w+') as wh:
            wh.write(data)

        yield file_location

        if temp:
            os.system('rm ' + file_location + '*')

    def import_handler(self, name, data, save_temp=False):
        with self.save_handler(name, data, temp=save_temp) as file_location:
            spec = importlib.util.spec_from_file_location(
                name, file_location)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

    def reload_module(self, module):
        importlib.reload(module)
