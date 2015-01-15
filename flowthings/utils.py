from time import time
from hashlib import sha1

import logging
import requests

from .exceptions import *
from .builders import Token


logger = logging.getLogger('flowthings')


def default(x, d):
    """ Returns the value if it isn't None, otherwise the default. """
    return x if x is not None else d


def mk_headers(creds):
    """ Returns a dictionary of request headers given a set of credentials. """
    assert isinstance(creds, Token)
    return {
      'accept': '*/*',
      'content-type': 'application/json; charset="UTF-8"',
      'x-auth-token': creds.token,
      'x-auth-account': creds.account }


def api_request(method, url, params=None, data=None, creds=None):
    """ Make a request with the proper credential headers. """
    logger.info('%s %s %s %s', method, url, params, data)
    res = requests.request(method, url,
                           params=params,
                           data=data,
                           headers=mk_headers(creds))
    logger.info('%d %s', res.status_code, res.content)
    return (res.content, res.headers, res.status_code)


ERROR_TABLE = {
    400: FlowThingsBadRequest,
    403: FlowThingsForbidden,
    404: FlowThingsNotFound,
    500: FlowThingsServerError,
}


def plat_exception(res, status, creds=None, method=None, path=None,):
    """ Builds an appropriate exception given a bad platform response. """
    errors = res['head']['errors']
    exc = ERROR_TABLE.get(res['head']['status'], FlowThingsException)
    return exc(errors=errors, creds=creds, method=method, path=path)
