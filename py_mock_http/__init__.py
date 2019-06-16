"""Import meta properties.
"""
from .__meta__ import __author__, __version__
from py_mock_http.client import Client, mock_app
from py_mock_http.log import configure_logging

__all__ = ['Client', 'mock_app']

configure_logging()
