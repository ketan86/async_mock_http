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


class ConnectError(ClientException):
    """Raised when client can not connect to a server"""


class ServerException(PyMockHttpException):
    """Base server exception"""


class DuplicateAppError(Exception):
    """Raised when duplicate app is registered"""


class AppNotSupported(ServerException):
    """Raised when application requested by client is not supported"""


class AppAttachFailed(ServerException):
    """Raised when application could not attach to the server"""


class AppDetachFailed(ServerException):
    """Raised when application could not detach from the server"""


class InvalidAppError(ServerException):
    """Raised when server finds the application invalid"""
