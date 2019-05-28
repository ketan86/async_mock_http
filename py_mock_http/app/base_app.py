"""Abstract Base Application"""
import abc
from enum import Enum, unique, auto
from functools import wraps
from uuid import uuid4
from exceptions import DuplicateAppRegistration
from handler import AbstractHandler


class AppRegistry():
    pass


class MetaApp(type):
    def __new__(meta, name, bases, cls_dict):
        cls = super().__new__(meta, name, bases, cls_dict)
        if not hasattr(AppRegistry, cls.name.lower()):
            setattr(AppRegistry, cls.name.lower(), cls)
        else:
            raise DuplicateAppRegistration(
                f'App name {cls.name} is registered twice.')
        return cls


class BaseApp(metaclass=MetaApp):
    name = 'Base'

    def __init__(self, config):
        AbstractHandler.__init__(self)
        self.config = config
        self.id = '-'.join([self.name, str(uuid4())])
        self.register()

    def register(self):
        self.register_for_handler()
        self.register_for_handler_data()
