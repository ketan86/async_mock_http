"""Project Specific Exceptions
"""


class PyMockHttpException(Exception):
    """Base Exception."""


class ConfigException(PyMockHttpException):
    """Base config exception"""


class EnvNotSetError(ConfigException):
    """Raised when config environment value is not set"""


class ClientException(PyMockHttpException):
    """Base client exception"""


class ServerException(PyMockHttpException):
    """Base server exception"""

class DuplicateAppRegistration(Exception):
    """Raised when duplicate app is registered"""

class AppNotSupported(ServerException):
    """Raised when application requested by client is not supported"""


class AttachFailed(ServerException):
    """Raised when application could not attach to the server"""

class DetachFailed(ServerException):
    """Raised when application could not detach from the server"""


class InvalidAppError(ServerException):
    """Raised when server finds the application invalid"""
