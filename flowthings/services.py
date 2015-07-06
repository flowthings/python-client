from __future__ import absolute_import
import json
import websocket
from copy import copy

from .exceptions import *
from .utils import api_request, default, plat_exception
from .builders import *
from .default import defaults
import six


__all__ = (
    'IdentityService',
    'GroupService',
    'TrackService',
    'APITaskService',
    'MQTTTaskService',
    'RSSTaskService',
    'FlowService',
    'DropServiceFactory',
    'TokenService',
    'ShareService',
    'DeviceService',
    'StatisticsService',
    'WebSocketService',
)


class BaseService(object):
    """ A bare-bones service that only supports a `request` method for making
    HTTP requests to a scoped path. """

    path = ''

    def __init__(self, creds, secure=None, host=None, version=None,
                 encoder=None, params=None, request=None, **kwargs):

        self.creds = creds
        self._secure    = default(secure, defaults.secure)
        self._host      = default(host, defaults.host)
        self._version   = default(version, defaults.version)
        self._encoder   = default(encoder, defaults.encoder)
        self._params    = default(params, defaults.params)
        self._request   = default(request, defaults.request)

    def request(self, method, path='', data=None, params=None):
        """ A basic request method where you can supply a method, path, data
        and params. This method will parse the platform response and strip
        out the request headers. """

        data = self._mk_data(data)
        params = self._mk_params(params)
        raw, hdr, status = self.raw_request(method, path, data, params)
        res = self._encoder.loads(raw)

        if 200 <= status < 400:
            if params and params.get('refs', False):
                return (res['body'], res['head']['references'])
            return res['body']

        raise plat_exception(res, status, creds=self.creds, method=method,
                             path=self.path + path)

    def raw_request(self, method, path='', data=None, params=None):
        """ A lower level request method that returns the raw response. This
        doesn't touch the data or params and passes them along as is. """

        url = self._mk_url(path)
        return self._request(method, url, data=data, params=params,
                             creds=self.creds)


    def _mk_url(self, path):
        return '%s://%s/v%s/%s%s%s' % (
            'https' if self._secure else 'http',
            self._host,
            self._version,
            self.creds.account,
            self.path,
            path)

    def _mk_data(self, data):
        return self._encoder.dumps(data) if data is not None else None

    def _mk_params(self, params):
        p = copy(self._params)
        if params is not None:
            if not isinstance(params, dict):
                params = params.to_dict()
            p.update(params)
        return p


class FindableServiceMixin(object):
    """ A mixin to support various retrieval methods. """

    def read(self, id, **kwargs):
        return self.request('GET', '/' + id, params=P(**kwargs))

    def read_or_else(self, id, default=None, **kwargs):
        """ Supply a default value instead of throwing a FlowThingsNotFound
        exception. Note, that this does not silence other exceptions, only
        404s from the platform. """

        try:
            return self.read(id, **kwargs)
        except FlowThingsNotFound:
            return default

    def read_many(self, ids, **kwargs):
        """ Make an MGET query to the platform to return multiple resources
        at the same time. This returns a map of id -> resource. """

        return self.request('MGET', data=ids, params=P(**kwargs))

    def find_many(self, *args, **kwargs):
        """ Make a parameterized search. Args are assumed to be filters. """

        if len(args):
            params = P(filter=args, **kwargs)
        else:
            params = P(**kwargs)
        return self.request('GET', params=params)

    def find(self, *args, **kwargs):
        """ Overloaded find method that intuitively calls the correct method
        based upon the type of the first argument. """

        args = list(args)
        tail = args[1:]
        try:
            first = args[0]
        except IndexError:
            first = None

        if isinstance(first, (str, six.text_type)):
            return self.read(first, *tail, **kwargs)
        if isinstance(first, list):
            return self.read_many(first, *tail, **kwargs)
        return self.find_many(*args, **kwargs)


class SaveableServiceMixin(object):
    """ A mixin to support saving and updating. """

    def create(self, model, **kwargs):
        return self.request('POST', data=model, params=P(**kwargs))

    def update(self, model, **kwargs):
        """ If the provided model is an instance of `Modify|M` it will pull
        out the changes and only send what was changed. Otherwise, it will just
        send the entire payload. """

        if isinstance(model, Modify):
            model, changes = model.done()
        else:
            changes = model
        return self.request('PUT', '/' + model['id'], data=changes,
                            params=P(**kwargs))

    def update_many(self, models, **kwargs):
        """ Given a list of models or Modify|M instances, issues a bulk update
        using MPUT. """

        data = {}
        for model in models:
            if isinstance(model, Modify):
                model, changes = model.done()
            else:
                changes = model
            data[model['id']] = changes
        return self.request('MPUT', data=data, params=P(**kwargs))

    def save(self, model, *args, **kwargs):
        """ Overloaded persistance method that intuitively calls the correct
        method my inspecting the type and structure of the first argument. """

        if isinstance(model, list):
            return self.update_many(model, *args, **kwargs)
        if isinstance(model, Modify) or 'id' in model:
            return self.update(model, *args, **kwargs)
        return self.create(model, *args, **kwargs)


class DestroyableServiceMixin(object):
    """ A mixin to support deletion. """

    def delete(self, id, data=None, **kwargs):
        return self.request('DELETE', '/' + id, data=data, params=P(**kwargs))


class AggregateServiceMixin(object):
    """ A mixin to support aggregation. """

    def aggregate(self, output, group_by=None, filter=None, rules=None, sorts=None):
        data = { 'output': output }
        if group_by is not None:
            data['groupBy'] = group_by
        if filter is not None:
            data['filter'] = str(filter)
        if rules is not None:
            data['rules'] = dict([(k, str(v)) for k, v in six.iteritems(rules)])
        if sorts is not None:
            data['sorts'] = sorts
        return self.request('POST', '/aggregate', data, None)


class FullServiceMixin(FindableServiceMixin,
                       SaveableServiceMixin,
                       DestroyableServiceMixin):
    """ A mixin to support finding, saving, and deleting. """
    pass


class AbstractServiceFactory(object):
    """ Some services require context (eg. drops) before you can make requests.
    This will return a bound service based on the context when called. """

    service_class = None

    def __init__(self, *args, **kwargs):
        args = list(args)
        if len(args):
            self.creds = args.pop(0)
        elif 'creds' in kwargs:
            self.creds = kwargs.pop('creds')
        else:
            self.creds = None
        self._args = args
        self._kwargs = kwargs

    def __call__(self, context):
        args = [self.creds] + self._args
        return self.service_class(context, *args, **self._kwargs)


class IdentityService(BaseService, FullServiceMixin):
    path = '/identity'


class GroupService(BaseService, FullServiceMixin):
    path = '/group'


class TrackService(BaseService, FullServiceMixin):
    path = '/track'


class APITaskService(BaseService, FullServiceMixin):
    path = '/api-task'


class MQTTTaskService(BaseService, FullServiceMixin):
    path = '/mqtt'


class RSSTaskService(BaseService, FullServiceMixin):
    path = '/rss'


class DeviceService(BaseService, FullServiceMixin):
    path = '/device'


class FlowService(BaseService, FullServiceMixin):
    path = '/flow'


class DropService(BaseService, FullServiceMixin, AggregateServiceMixin):
    def __init__(self, flow_id, *args, **kwargs):
        self.path = '/drop/' + flow_id
        BaseService.__init__(self, *args, **kwargs)

    def delete_all(self):
        return self.request('DELETE', '')


class DropServiceFactory(BaseService, AbstractServiceFactory):
    path = '/drop'
    service_class = DropService

    def __init__(self, *args, **kwargs):
        BaseService.__init__(self, *args, **kwargs)
        AbstractServiceFactory.__init__(self, *args, **kwargs)

    def create(self, model, **kwargs):
        return self.request('POST', data=model, params=P(**kwargs))


class TokenService(BaseService, FindableServiceMixin, DestroyableServiceMixin):
    path = '/token'

    def create(self, model, **kwargs):
        return self.request('POST', data=model, params=P(**kwargs))


class ShareService(BaseService, FindableServiceMixin, DestroyableServiceMixin):
    path = '/share'

    def create(self, model, **kwargs):
        return self.request('POST', data=model, params=P(**kwargs))


def statistic(name):
    def method(self, id, year=None, month=None, day=None, level=None):
        path = '/%s/%s' % (name, id)
        if year is not None:
            path += '/%s' % year
            if month is not None:
                path += '/%s' % month
                if day is not None:
                    path += '/%s' % day
        if level is not None:
            params = { 'level': level }
        else:
            params = None
        return self.request('GET', path, None, params)
    return method


class StatisticsService(BaseService):
    path = '/statistics'

    flowDropAdded = statistic('flowDropAdded')
    flowTracked = statistic('flowTracked')
    trackHit = statistic('trackHit')
    trackPass = statistic('trackPass')
    apiCallByIdentity = statistic('apiCallByIdentity')
    dropCreatedBy = statistic('dropCreatedBy')
    flow_drop_added = statistic('flowDropAdded')
    flow_tracked = statistic('flowTracked')
    track_hit = statistic('trackHit')
    track_pass = statistic('trackPass')
    api_call_by_identity = statistic('apiCallByIdentity')
    drop_created_by = statistic('dropCreatedBy')


class WebSocketService(BaseService):
    path = '/session'

    def __init__(self, *args, **kwargs):
        super(WebSocketService, self).__init__(*args, **kwargs)
        self._host = default(kwargs.get('ws_host'), defaults.ws_host)

    def connect(self, **kwargs):
        session = self.request('POST')
        ws_url = '%s://%s%s/%s/ws' % (
            'wss' if self._secure else 'ws',
            self._host,
            self.path,
            session['id'])
        return WebSocketClient(ws_url, self._encoder, **kwargs)

    def _mk_url(self, path):
        return '%s://%s%s%s' % (
            'https' if self._secure else 'http',
            self._host,
            self.path,
            path)


class WebSocketClient(object):
    def __init__(self, url, encoder, on_open=None, on_close=None,
                 on_error=None, on_message=None, **kwargs):

        self.on_open    = on_open
        self.on_close   = on_close
        self.on_error   = on_error
        self.on_message = on_message

        self._encoder   = encoder
        self._reply_id  = 0
        self._reply_cbs = {}
        self._app = websocket.WebSocketApp(url,
                                           on_open=self._on_open,
                                           on_close=self._on_close,
                                           on_error=self._on_error,
                                           on_message=self._on_message,
                                           **kwargs)

    def run(self):
        self._app.run_forever()

    def subscribe(self, resource, callback=None):
        self._send('subscribe', 'drop', resource, callback)

    def unsubscribe(self, resource, callback=None):
        self._send('unsubscribe', 'drop', resource, callback)

    def _send(self, type, object, value, callback):
        data = { 'type': type, 'object': object,}
        if type == 'subscribe' or type == 'unsubscribe':
            data['flowId'] = value
        else:
            data['value'] = value

        if callable(callback):
            rid = self._reply_id
            data['msgId'] = rid
            self._reply_id += 1
            self._reply_cbs[rid] = callback
        self._app.send(self._encoder.dumps(data))

    def _on_open(self, ws):
        if self.on_open: self.on_open(self)

    def _on_close(self, ws):
        if self.on_close: self.on_close(self)

    def _on_error(self, ws, error):
        if self.on_error: self.on_error(self, error)

    def _on_message(self, ws, payload):
        data = self._encoder.loads(payload)

        if 'type' in data and data['type'] == 'message':
            self.on_message(self, data['resource'], data['value'])

        elif 'head' in data:
            rid = data['head']['msgId']
            if rid in self._reply_cbs:
                self._reply_cbs[rid](self, data['body'])
                del self._reply_cbs[rid]
