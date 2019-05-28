"""Server configurations.
"""
import configparser
import os
from collections import abc
from .exceptions import EnvNotSetError

PREFIX = "PY_MOCK_HTTP_"
CONFIG_FILE = PREFIX + "CONFIG"


DEFAULT_CONFIG = {
    "HOST": "0.0.0.0",
    "HTTP_PORT": "8888",
    "HTTPS_PORT": "443",
    "REALOAD_CONFIG": False,
    "CERTIFICATE_FILE": None,
    "CERTIFICATE_KEY": None,
    "SERVER_REQUEST_TIMEOUT": 10,
    "HANDLER_LOCATION": "./py_mock_http/handler"
}


def _get_bool(val):
    val = val.lower()
    if val in ("yes", "true", "on"):
        return True
    elif val in ("no", "false", "off"):
        return False
    else:
        raise ValueError("invalid bool value %r" % (val,))


def load_from_file(path, section="server"):
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(path)
    return Config(config[section])


def load_from_string(config_str, section="server"):
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read_string(config_str)
    return Config(config[section])


def load_from_env_file():
    if CONFIG_FILE in os.environ:
        with open(os.environ[CONFIG_FILE], 'r') as fh:
            return load_from_string(fh.read())
    else:
        raise EnvNotSetError('PY_MOCK_HTTP_CONFIG not set.')


def load_from_env_vars(prefix=PREFIX):
    config = Config(None)
    for k, v in os.environ.items():
        if k.startswith(prefix):
            _, config_key = k.split(prefix, 1)
            try:
                config[config_key] = int(v)
            except ValueError:
                try:
                    config[config_key] = float(v)
                except ValueError:
                    try:
                        config[config_key] = _get_bool(v)
                    except ValueError:
                        config[config_key] = v
    return config


class Config(abc.MutableMapping):
    def __init__(self, config):
        config = config or {}
        self._config = {}
        # load default config
        self._config.update(**DEFAULT_CONFIG)
        # override with user config
        self._config.update(**config)

    def __getitem__(self, name):
        return self._config[name]

    def __setitem__(self, name, value):
        self._config[name] = value

    def __delitem__(self, name):
        del self._config[name]

    def __iter__(self):
        return iter(self._config.items())

    def __len__(self):
        return len(self._config)
