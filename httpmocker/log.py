import logging.config

DEFAULT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] - %(levelname)s - %(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S",
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'formatter': 'default',
            'class': 'logging.StreamHandler',
        },
        'rotate_file': {
            'level': 'DEBUG',
            'formatter': 'default',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'rotated.log',
            'encoding': 'utf8',
            'maxBytes': 100000,
            'backupCount': 1,
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'httpmocker.client': {
            'level': 'INFO',
            'handlers': ['console']
        },
        'httpmocker.server': {
            'level': 'DEBUG',
            'handlers': ['rotate_file']
        },
        'httpmocker.app': {
            'level': 'DEBUG',
            'handlers': ['rotate_file']
        }
    }
}


def configure_logging():
    logging.config.dictConfig(DEFAULT_LOGGING)