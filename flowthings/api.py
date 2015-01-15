from collections import MutableMapping

from . import services
from .exceptions import FlowThingsException
from .default import defaults


__all__ = ('API',)


DEFAULT_SERVICES = {
    'root'      : services.BaseService,
    'identity'  : services.IdentityService,
    'group'     : services.GroupService,
    'track'     : services.TrackService,
    'flow'      : services.FlowService,
    'drop'      : services.DropServiceFactory,
    'token'     : services.TokenService,
    'share'     : services.ShareService,
    'websocket' : services.WebSocketService,
}

ASYNC_LIBS = {
    'eventlet': {
        'pool'  : 'GreenPool',
        'get'   : 'wait',
    },
    'gevent': {
        'pool'  : 'Pool',
        'get'   : 'get',
    },
}

DEFAULT = {}


class API(object):
    """ Creates a new API context with the given credentials. All requests
    made through the context will be called as the provided actor. """

    def __init__(self, creds, async_lib=DEFAULT, *args, **kwargs):
        self._creds = creds
        self._args = args
        self._kwargs = kwargs
        self._services = {}
        self._create_services()

        if async_lib is DEFAULT:
            self._async_lib = defaults.async_lib
        else:
            self._async_lib = async_lib

        if self._async_lib:
            self._async_map = ASYNC_LIBS[self._async_lib.__name__]

    def _create_services(self):
        for name, cls in DEFAULT_SERVICES.items():
            self.add_service(name, cls)

    def add_service(self, name, cls):
        """ Add custom services that extend BaseService or
        AbstractServiceFactory. Given a name and a class, will instantiate the
        service with the API's options and add it to the API instance. """

        self._services[name] = cls(self._creds, *self._args, **self._kwargs)
        setattr(self, name, self._services[name])

    def async(self, pool=None):
        """ Returns an async API proxy. All API calls will be fired in
        parallel, returning a green thread. """

        return self._api_proxy(AsyncAPI, pool)

    def lazy(self, pool=None):
        """ Returns a lazy API proxy. All API calls will be fired in parallel,
        returning a GreenThunk dict proxy which will wait when accessed. """

        return self._api_proxy(LazyAPI, pool)

    def _api_proxy(self, proxy_class, pool):
        if self._async_lib is None:
            raise NotImplementedError('Either eventlet or gevent is required for async')
        if pool is None:
            name = self._async_map['pool']
            pool = getattr(self._async_lib, name)()
        return proxy_class(self, pool)

    @property
    def creds(self):
        return self._creds

    @creds.setter
    def creds(self, creds):
        self._creds = creds
        for name, service in self._services.items():
            service.creds = creds


class AsyncAPI(object):
    """ An async wrapper around an API. Services are wrapped with an
    AsyncServiceProxy which calls its methods in a new green thread. Async
    actions can then be collected by calling `results` on the AsyncAPI. """
    
    def __init__(self, api, pool):
        self._api = api
        self._pool = pool
        self._queue = []
        self._proxy_services()

    def _proxy_services(self):
        for name, service in self._api._services.items():
            if isinstance(service, services.AbstractServiceFactory):
                proxy_class = AsyncServiceFactoryProxy
            else:
                proxy_class = AsyncServiceProxy
            setattr(self, name, proxy_class(service, self._pool, self._queue))

    def results(self, with_exceptions=False):
        """ Blocks till all requests are completed, and returns a list of all
        the results. If you wish to silence exceptions, and instead get them
        back with the results, set `with_exceptions=True`. """

        get_method = self._api._async_map['get']
        results = []

        try:
            while len(self._queue):
                thread = self._queue.pop(0)
                try:
                    res = getattr(thread, get_method)()
                except FlowThingsException as e:
                    if with_exceptions:
                        results.append((e, None))
                    else:
                        raise
                else:
                    if with_exceptions:
                        results.append((None, res))
                    else:
                        results.append(res)
        finally:
            while len(self._queue):
                self._queue.pop(0)

        return results


class AsyncServiceProxy(object):
    """ Wraps a service to spawn a new greenthread for each call. """

    def __init__(self, service, pool, queue):
        self._service = service
        self._pool = pool
        self._queue = queue

    def __getattr__(self, attr):
        method = getattr(self._service, attr)
        def spawner(self, *args, **kwargs):
            thread = self._pool.spawn(method, *args, **kwargs)
            self._queue.append(thread)
            return thread
        return spawner.__get__(self, AsyncServiceProxy)


class AsyncServiceFactoryProxy(object):
    """ Wraps an AbstractServiceFactory to create new services wrapped with
    AsyncServiceProxy. """

    def __init__(self, factory, pool, queue):
        self._factory = factory
        self._pool = pool
        self._queue = queue

    def __call__(self, context):
        service = self._factory(context)
        return AsyncServiceProxy(service, self._pool, self._queue)


class LazyAPI(object):
    """ A lazy wrapper around an API. Similar to the async api, but returns
    MutableMapping thunk wrappers around results. All requests are fired off
    in new green threads, but only block once you try to access data. This
    gives us automatic parallelization while using a sync-like API. """

    def __init__(self, api, pool):
        self._api = api
        self._pool = pool
        self._proxy_services()

    def _proxy_services(self):
        get_method = self._api._async_map['get']
        for name, service in self._api._services.items():
            if isinstance(service, services.AbstractServiceFactory):
                proxy_class = LazyServiceFactoryProxy
            else:
                proxy_class = LazyServiceProxy
            setattr(self, name, proxy_class(service, self._pool, get_method))


class LazyServiceProxy(object):
    """ Wraps a service to return a GreenThunk for each call. """

    def __init__(self, service, pool, get_method):
        self._service = service
        self._pool = pool
        self._get_method = get_method

    def __getattr__(self, attr):
        method = getattr(self._service, attr)
        def spawner(self, *args, **kwargs):
            thread = self._pool.spawn(method, *args, **kwargs)
            return GreenThunk(lambda: getattr(thread, self._get_method)())
        return spawner.__get__(self, LazyServiceProxy)


class LazyServiceFactoryProxy(object):
    """ Wraps an AbstractServiceFactory to create new services wrapped with
    LazyServiceProxy. """

    def __init__(self, factory, pool, get_method):
        self._factory = factory
        self._pool = pool
        self._get_method = get_method

    def __call__(self, context):
        service = self._factory(context)
        return LazyServiceProxy(service, self._pool, self._get_method)


class GreenThunk(MutableMapping):
    """ Dict proxy for waiting on async green requests. """

    def __init__(self, wait):
        self.__data = None
        self.__wait = wait

    def __len__(self):
        self.force()
        return len(self.__data)

    def __iter__(self):
        self.force()
        for x in self.__data:
            yield x

    def __getitem__(self, key):
        self.force()
        return self.__data[key]

    def __setitem__(self, key, value):
        self.force()
        self.__data[key] = value

    def __delitem__(self, key):
        self.force()
        del self.__data[key]

    def __str__(self):
        self.force()
        return str(self.__data)

    def force(self):
        if self.__data is None:
            self.__data = self.__wait()

    def unwrap(self):
        self.force()
        return self.__data

