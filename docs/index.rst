==========
flowthings
==========

.. py:module:: flowthings

.. py:class:: Token(account, token)

   Token objects may be passed to an :py:class:`API`. This will be used to
   sign requests to the platform. ::

      >>> creds = Token('<account>', '<token>')

.. py:class:: API(creds, \
                  async_lib=DEFAULT, \
                  secure=DEFAULT, \
                  params=DEFAULT)

   Creates a new API instance for interacting with the platform. ::

      >>> api = API(creds)

   Options labelled as ``DEFAULT`` will use the options set in the
   :py:data:`defaults` configuration object.

   An :py:class:`API` is comprised of services for querying the different
   domains on the platform:
   
   * ``flow``
   * ``drop``
   * ``track``
   * ``group``
   * ``identity``
   * ``token``
   * ``share``
   * ``websocket``

   For documentation on these services, read :ref:`services`,
   :ref:`authentication`, and :ref:`websockets`.

   .. py:method:: async([pool])
      
      Returns an API wrapper for making asynchronous requests using either
      ``eventlet`` or ``gevent``. Requests made using an :py:meth:`async` API
      will return green threads.

      For more documentation, read :ref:`async-and-parallel`.

   .. py:method:: lazy([pool])

      Returns an API wrapper for making implicitly parallel requests using
      either ``eventlet`` or ``gevent``. Requests made using a :py:meth:`lazy`
      API will return thunks that wait on their respective green thread when
      accessed.

      For more documentation, read :ref:`async-and-parallel`.

   .. py:attribute:: creds

      Get or set the API's :py:class:`Token`.

.. py:data:: defaults

   Configuration object for globally setting default options for
   :py:class:`API` instances.

   .. py:attribute:: defaults.async_lib

      Defaults to ``None``. Supports ``eventlet`` and ``gevent``. ::

         import eventlet

         flowthings.defaults.async_lib = eventlet

   .. py:attribute:: defaults.secure

      Defaults to ``True``. When set to ``False``, requests will be made over
      ``http://`` rather than ``https://``.

   .. py:attribute:: defaults.params
    
      The default set of query string parameters sent with all requests.
      Defaults to ``{}``.

.. _services:

Service Methods
---------------

All :py:class:`API` service requests return plain dictionaries of the request
body. They may throw :ref:`exceptions <exceptions>` in case of an error.

.. py:method:: service.read(id, **params)

   :param str id: The resource id

   >>> api.flow.read('<flow_id>')

.. py:method:: service.read_or_else(id, default=None, **params)

   :param str id: The resource id
   :param any default: Default value when the resource is not found

   >>> api.flow.read_or_else('<flow_id>', None)

.. py:method:: service.read_many(ids, **params)

   :param list ids: List of resource ids

   >>> api.flow.read_many(['<flow_id_1>', '<flow_id_2'])

.. py:method:: service.find_many(*filters, **params)

   :param Filter filters: Request filters

   >>> api.flow.find_many(mem.displayName == 'Foo')

.. py:method:: service.find(..., **params)

   An overloaded method which may call one of :py:meth:`read`,
   :py:meth:`read_many`, or :py:meth:`find_many` depending upon the type of
   the first argument.

   >>> api.flow.find('<flow_id>')
   >>> api.flow.find(['<flow_id_1>', '<flow_id_2'])
   >>> api.flow.find(mem.displayName == 'Foo')

.. py:method:: service.create(model, **params)
  
   :param dict model: Initial data for a new resource

   >>> api.flow.create({'path': '/path/to/flow'})

.. py:method:: service.update(model, **params)

   :param model: Updated model
   :type model: dict or :py:class:`M`

   Requests are made based on the model's ``'id'`` key.

   >>> api.flow.update({'id': '<flow_id>', 'displayName': 'Foo'})
   >>> api.flow.update(M(model, displayName='Foo'))

.. py:method:: service.update_many(models, **params)

   :param list models: List of updated models

.. py:method:: service.save(..., **params)

   An overloaded method which may call one of :py:meth:`create`,
   :py:meth:`update`, or :py:meth:`update_many` depending upon the type of the
   first argument. :py:meth:`create` or :py:meth:`update` are called based on
   the presence of an ``'id'`` key.

.. py:method:: service.delete(id, data=None, **params)
  
   :param str id: The resource to delete
   :param any data: Request data

   >>> api.flow.delete('<flow_id>')

.. note::

   The ``drop`` service is slightly different in that it must first be
   parameterized by the Flow id.

   >>> api.drop('<flow_id>').find(limit=10)

.. _request-params:

Request Parameters
------------------

:ref:`Service methods <services>` take additional keyword arguments that act
as query parameters on the requests. These are not fixed in any way, so please
refer to the platform documentation for the options.

.. note::

   When a request is made with the ``refs`` parameter set to ``True``, the return
   type becomes a tuple rather than a single dictionary::

   >>> resp, refs = api.flow.find('<flow_id>', refs=True)

.. _criteria:

Request Filters
---------------

:py:meth:`Service find methods <service.find_many>` understand a query DSL that
lets you express filters using Python operations instead of manually splicing
strings together. ::

    >>> api.flow.find(mem.displayName == 'foo', mem.path.re('^/foo', 'i'))

.. py:class:: mem

   `mem` represents members of the objects you are querying. You can use use
   properties or key indexing to represent a member.::

   >>> api.drop(<flow_id>).find(mem.elems.foo > 12)

   The supported operators are ``==``, ``<``, ``<=``, ``>``, and ``>=`` along
   with the following methods, mirroring the platform:

   .. py:method:: re(pattern[, flags])

   .. py:method:: IN(*items)

   .. py:method:: CONTAINS(*items)

   .. py:method:: WITHIN(distance, unit[, coords=(lat, lon)[, zip=zipcode]])

Additional platform filter operations are supported:

.. py:function:: EXISTS(member)

.. py:function:: HAS(elem_type)

.. py:function:: MATCHES(pattern[, flags])

.. py:function:: NOT(filter)

.. py:data:: AGE

   Age comparisons can be made using normal python operators with ``AGE``.::

      >>> api.flow.find(AGE > time_millis)

Boolean operations are supported on filters using ``AND`` and ``OR``.::

   >>> api.flow.find((mem.displayName == 'foo').OR(mem.displayName == 'bar'))

.. _modifications:

Modifications
-------------

:py:meth:`Service update methods <service.update>` can also take an instance
of a modification helper called :py:class:`M`. It lets you gradually make
updates to a model and then extract the diff and model with the changes
applied.

When passed directly to an update method, only the changes will be sent to the
server instead of the entire model.

.. py:class:: M(model, **changes)

   .. py:method:: modify(key, val)

   .. py:method:: done()

      Returns a tuple of ``(new_model, diff)``.

.. _exceptions:

Exceptions
----------

.. py:class:: FlowThingsError

.. py:class:: FlowThingsException

   .. py:attribute:: errors

      List of errors returned from the platform

   .. py:attribute:: creds

      Request credentials
      
   .. py:attribute:: method

      Request HTTP method

   .. py:attribute:: path

      Request path

.. py:class:: FlowThingsBadRequest

.. py:class:: FlowThingsForbidden

.. py:class:: FlowThingsNotFound

.. py:class:: FlowThingsServerError

.. _authentication:

Authentication
--------------

If you create your :py:class:`API` using a master token, you can create and
manage tokens and shares.

.. py:function:: api.token.create(model, **params)

.. py:function:: api.share.create(model, **params)

Both tokens and shares support ``find`` and ``delete`` methods like other
services.  They are, however, immutable and do not support updates.

.. _async-and-parallel:

Asynchronous and Parallel Requests
----------------------------------

Two workflows are supported for making asynchronous and parallel requests.

The :py:meth:`API.async` workflow is an imperative API where requests are
queued internally. Once you've made all the requests you need, you can invoke
the ``results()`` method to wait. This can be useful when making large batches
of similar requests::

    paths = [...]
    async_api = api.async()

    for path in paths
        async_api.flow.find(mem.path == path)

    for flows in async_api.results():
        # Do something with the flows
        pass

If some of your requests might fail, and you want to know which ones, you may
set the ``with_exceptions`` keyword argument::

    flows = [...]
    async_api = api.async()

    for flow in flows:
        async_api.drop(flow['id']).find(limit=10)

    for e, drops in async_api.results(with_exceptions=True):
        if e:
            # Do something if there was an error
            pass
        else:
            # Do something with the drops
            pass

The :py:meth:`API.lazy` worklow is useful when building complex compositions of
dependent requests which can benefit from implicit parallelization. All
requests are executed in parallel, but wait when you try to read the data. This
works by requests returning a ``GreenThunk``, which is a ``MutableMapping``
around a green thread. This object acts just like a regular dictionary or list,
but waits on the green thread before performing any look-ups or mutations. ::

    lazy_api = api.lazy()
    flow_a = lazy_api.flow.find(mem.path == '/path/to/flow_a')
    flow_b = lazy_api.flow.find(mem.path == '/path/to/flow_b')
    drops  = lazy_api.drop(flow_a[0]['id']).find(limit=10)

In this example, the two requests for Flows are performed in parallel, while
the requests for drops waits for the ``flow_a`` request to complete first.

You can retrieve the pure data of a ``GreenThunk`` by invoking its ``unwrap()``
method.

.. note::

   It is assumed the user has done the necessary green thread monkey-patching
   for their chosen library before importing the ``flowthings`` package.

.. _websockets:

WebSockets
----------

WebSockets are supported using the ``websocket-client`` package. Here is a
short example::

    def on_open(ws):
        ws.subscribe('<flow_id>')

    def on_message(ws, resource, data):
        print 'Got message:', resource, data

    def on_close(ws):
        print 'Closed'

    def on_error(ws, e):
        print 'Error:', e

    ws = api.websocket.connect(on_open=on_open,
                               on_message=on_message,
                               on_close=on_close,
                               on_error=on_error)
    ws.run()
