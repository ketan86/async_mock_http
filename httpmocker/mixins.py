from collections import namedtuple
import os


class SSLMixin(object):
    SSL = namedtuple('SSL', 'cert key')
    CERT_STORAGE_LOCATION = './httpmocker/certs/'

    def __init__(self, cert, key):
        self.ssl_cert = None
        self.ssl_key = None

        if cert and key:
            os.makedirs(self.CERT_STORAGE_LOCATION, exist_ok=True)
            self.ssl_cert = f'{self.CERT_STORAGE_LOCATION}/server.crt'
            self.ssl_key = f'{self.CERT_STORAGE_LOCATION}/server.key'
            with open(self.ssl_cert, 'w') as f:
                f.write(cert)
            with open(self.ssl_key, 'w') as f:
                f.write(key)
