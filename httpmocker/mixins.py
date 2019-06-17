from collections import namedtuple
import os

from httpmocker.config import get_config


class SSLMixin(object):

    def save_cert(self, cert, key):
        # get storage location
        storage_root = self.get_cert_storage_root()

        # create storage root folder if does not exist
        os.makedirs(storage_root, exist_ok=True)

        self.ssl_cert = f'{storage_root}/app.crt'
        self.ssl_key = f'{storage_root}/app.key'

        # save cert
        with open(self.ssl_cert, 'w') as f:
            f.write(cert)
        with open(self.ssl_key, 'w') as f:
            f.write(key)
