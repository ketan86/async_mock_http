"""Django application manages Django server and handles
django requests.
"""
from __future__ import absolute_import

import importlib
import json
from uuid import uuid4
import logging
from app.base_app import BaseApp
from handler import AbstractHandler, HANDLER_URL, HANDLER_DATA_URL
from django.core import management


logger = logging.getLogger(__name__)


class DjangoApp(BaseApp, AbstractHandler):
    name = 'flask'

    def __init__(self, config):
        self.app = Flask(__name__)
        BaseApp.__init__(self, config)
