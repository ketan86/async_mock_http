"""Abstract base class for any handler supported by Python Mock HTTP server.
"""
import abc


class BaseReqHandler(abc.ABC):
    @abc.abstractmethod
    def cleanup(self):
        raise NotImplementedError
