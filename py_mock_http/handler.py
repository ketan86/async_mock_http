import abc
import importlib

HANDLER_URL = '/mock/app/handler/'
HANDLER_DATA_URL = '/mock/app/handler/data'
HANDLER_LOCATION = './py_mock_http/handlers/'


class AbstractHandler():

    def __init__(self):
        self.handler_data = {}

    @abc.abstractmethod
    def register_for_handler_data(self):
        pass

    # @abc.abstractmethod
    # def remove_data(self):
    #     pass

    @abc.abstractmethod
    def register_for_handler(self):
        pass

    # @abc.abstractmethod
    # def remove_handler(self):
    #     pass

    def save_handler(self, name, body_string):
        location = HANDLER_LOCATION + '/' + name + '.py'
        with open(location, 'w+') as wh:
            wh.write(body_string)
        return location

    def load_handler(self, name, body_string):
        location = self.save_handler(name, body_string)
        spec = importlib.util.spec_from_file_location(
            name, location)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
