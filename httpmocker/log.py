import logging.config
from httpmocker.config import get_config

DEFAULT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:'
            '%(lineno)d] %(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S",
        }
    },
    'handlers': {
        'console': {
            'formatter': 'default',
            'class': 'logging.StreamHandler',
        },
        'rotate_file': {
            'formatter': 'default',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': get_config().get('SERVER_LOG_FILE'),
            'encoding': 'utf8',
            'maxBytes': 100000,
            'backupCount': 1,
        }
    },
    'root': {
        'level': get_config().get('SERVER_LOG_LEVEL'),
        'handlers': ['console', 'rotate_file']
    },
    'loggers': {
        'httpmocker': {
            'level': get_config().get('SERVER_LOG_LEVEL'),
            'handlers': ['console', 'rotate_file']
        }
    }
}


def configure_logging():
    logging.config.dictConfig(DEFAULT_LOGGING)
