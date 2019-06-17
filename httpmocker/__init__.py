"""Import meta properties.
"""
from .__meta__ import __author__, __version__
from httpmocker.client import Client, mock_via
from httpmocker.server import run as run_mock_server
from httpmocker.log import configure_logging

__all__ = ['Client', 'mock_via', 'run_mock_server']

configure_logging()
