import json
from .utils import api_request


__all__ = ('defaults',)


DEFAULT = {}


class Defaults(object):
    def __init__(self, async_lib=None, secure=True, host='api.flow-things.io',
                 version='1b', request=api_request, encoder=json,
                 params=DEFAULT, ws_host='ws.flow-things.io'):

        if params is DEFAULT:
            params = {}

        self.async_lib = async_lib
        self.secure = secure
        self.host = host
        self.ws_host = ws_host
        self.version = version
        self.request = request
        self.encoder = json
        self.params = params


defaults = Defaults()
