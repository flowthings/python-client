from __future__ import absolute_import
import json
from .utils import api_request


__all__ = ('defaults',)


DEFAULT = {}


class Defaults(object):
    def __init__(self, async_lib=None, secure=True, host='api.flowthings.io',
                 version='0.1', request=api_request, encoder=json,
                 params=DEFAULT, ws_host='ws.flowthings.io'):

        if params is DEFAULT:
            params = {}

        self.async_lib = async_lib
        self.secure = secure
        self.host = host
        self.ws_host = ws_host
        self.version = version
        self.request = request
        self.encoder = encoder
        self.params = params


defaults = Defaults()
