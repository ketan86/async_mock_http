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


class AppException(ClientException):
    """Raised when app specific exceptions occur"""


class HandlerException(ClientException):
    """Raised when handler specific exceptions occur"""


class AccessNotAllowed(Exception):
    """Raised when method access not allowed"""


class ConnectError(ClientException):
    """Raised when client can not connect to a server"""


class ServerException(PyMockHttpException):
    """Base server exception"""


class DuplicateAppError(Exception):
    """Raised when duplicate app is registered"""


class AppNotSupported(ServerException):
    """Raised when application requested by client is not supported"""


class AppStartFailed(ServerException):
    """Raised when application could not start"""


class AppStopFailed(ServerException):
    """Raised when application could not stop"""


class InvalidAppError(ServerException):
    """Raised when server finds the application invalid"""
