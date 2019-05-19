"""Server configurations.
"""
import configparser
import os
from collections import abc

PREFIX = "ASYNC_MOCK_HTTP_"

DEFAULT_CONFIG = {
    "HOST": "0.0.0.0",
    "PORTS": "8080",
    "SSL": False,
    "SSL_PORT": "443",
    "REALOAD_CONFIG": False,
    "CERTIFICATE_FILE": None,
    "CERTIFICATE_KEY": None,
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
        self._config.update(**DEFAULT_CONFIG)
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