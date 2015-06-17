from unittest import TestCase
from flowthings import *


CREDS = Token('acc', 'tok')


class IdEncoder(object):
    def loads(self, x):
        return x

    def dumps(self, x):
        return x


def mock_api_request_ok(method, url, params=None, data=None, creds=None):
    resp = {
        'head': {
            'ok': True,
            'status': 200,
            'errors': [],
            'messages': [],
            'references': {},
        },
        'body': {
            'method': method,
            'url': url,
            'params': params,
            'data': data,
            'creds': creds
        }
    }
    return (resp, {}, 200)


def mock_api_request_not_found(method, url, params=None, data=None, creds=None):
    raise FlowThingsNotFound


class TestAsyncLib(object):
    def __init__(self):
        self.__name__ = 'eventlet'

    class GreenThread(object):
        def __init__(self, value):
            self.value = value

        def wait(self):
            # Box as proof it was executed "async"
            return { 'async': self.value }

    class GreenPool(object):
        def __init__(self, *args, **kwargs):
            pass

        def spawn(self, method, *args, **kwargs):
            return TestAsyncLib.GreenThread(method(*args, **kwargs))


def TestAPI(*args, **kwargs):
    if 'request' not in kwargs:
        kwargs['request'] = mock_api_request_ok

    if 'encoder' not in kwargs:
        kwargs['encoder'] = IdEncoder()

    if 'host' not in kwargs:
        kwargs['host'] = 'test'

    if 'ws_host' not in kwargs:
        kwargs['ws_host'] = 'ws.test'

    if 'version' not in kwargs:
        kwargs['version'] = 'test'

    if 'async_lib' not in kwargs:
        kwargs['async_lib'] = TestAsyncLib()

    if len(args) == 0:
        args = (CREDS,)

    return API(*args, **kwargs)

class RequestTestCase(TestCase):

    def test_request(self):
        api  = TestAPI()
        resp = api.root.request('PUT', '/foo', data='foo', params={ 'foo': True })
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/foo',
            'method': 'PUT',
            'params': { 'foo': True },
            'data': 'foo',
            'creds': CREDS,
        })

    def test_request_proxy(self):
        api  = TestAPI()
        resp = api.request('PUT', '/foo', data='foo', params={ 'foo': True })
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/foo',
            'method': 'PUT',
            'params': { 'foo': True },
            'data': 'foo',
            'creds': CREDS,
        })

    def test_read(self):
        api  = TestAPI()
        resp = api.flow.read('foo')
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow/foo',
            'method': 'GET',
            'params': {},
            'data': None,
            'creds': CREDS,
        })

    def test_read_many(self):
        api  = TestAPI()
        resp = api.flow.read_many(['foo', 'bar'])
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow',
            'method': 'MGET',
            'params': {},
            'data': ['foo', 'bar'],
            'creds': CREDS,
        })
    
    def test_find_many(self):
        api  = TestAPI()
        resp = api.flow.find_many()
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow',
            'method': 'GET',
            'params': {},
            'data': None,
            'creds': CREDS,
        })
    
    def test_read_or_else(self):
        api  = TestAPI()
        resp = api.flow.read_or_else('foo', 'bar')
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow/foo',
            'method': 'GET',
            'params': {},
            'data': None,
            'creds': CREDS,
        })

        api  = TestAPI(request=mock_api_request_not_found)
        resp = api.flow.read_or_else('foo', 'bar')
        self.assertEqual(resp, 'bar')

    def test_find(self):
        api  = TestAPI()
        resp = api.flow.find()
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow',
            'method': 'GET',
            'params': {},
            'data': None,
            'creds': CREDS,
        })

        resp = api.flow.find('foo')
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow/foo',
            'method': 'GET',
            'params': {},
            'data': None,
            'creds': CREDS,
        })

        resp = api.flow.find(['foo', 'bar'])
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow',
            'method': 'MGET',
            'params': {},
            'data': ['foo', 'bar'],
            'creds': CREDS,
        })

    def test_find_params(self):
        api = TestAPI()
        resp, refs = api.flow.find(limit=10, refs=True, only=('name', 'path'))
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow',
            'method': 'GET',
            'params': {
                'limit': 10,
                'refs': 1,
                'only': 'name,path',
            },
            'data': None,
            'creds': CREDS,
        })

    def test_find_filter(self):
        api  = TestAPI()
        resp = api.flow.find(mem.foo == True)
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow',
            'method': 'GET',
            'params': { 'filter': 'foo == true' },
            'data': None,
            'creds': CREDS,
        })

    def test_find_filter_and_params(self):
        api  = TestAPI()
        resp = api.flow.find(mem.foo == True, limit=10)
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow',
            'method': 'GET',
            'params': { 'filter': 'foo == true', 'limit': 10 },
            'data': None,
            'creds': CREDS,
        })
                
    def test_create(self):
        api  = TestAPI()
        resp = api.flow.create({ 'displayName': 'foo' })
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow',
            'method': 'POST',
            'params': {},
            'data': { 'displayName': 'foo' },
            'creds': CREDS,
        })
                
    def test_update(self):
        api  = TestAPI()
        resp = api.flow.update({ 'id': 'foo', 'displayName': 'foo' })
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow/foo',
            'method': 'PUT',
            'params': {},
            'data': {
                'id': 'foo',
                'displayName': 'foo',
            },
            'creds': CREDS,
        })

    def test_update_many(self):
        api  = TestAPI()
        resp = api.flow.update_many([
            { 'id': 'foo', 'displayName': 'foo' },
            { 'id': 'bar', 'displayName': 'bar' },
        ])
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow',
            'method': 'MPUT',
            'params': {},
            'data': {
                'foo': { 'id': 'foo', 'displayName': 'foo' },
                'bar': { 'id': 'bar', 'displayName': 'bar' },
            },
            'creds': CREDS,
        })

    def test_save(self):
        api  = TestAPI()
        resp = api.flow.save({ 'displayName': 'foo' })
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow',
            'method': 'POST',
            'params': {},
            'data': { 'displayName': 'foo' },
            'creds': CREDS,
        })

        resp = api.flow.save({ 'id': 'foo', 'displayName': 'foo' })
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow/foo',
            'method': 'PUT',
            'params': {},
            'data': {
                'id': 'foo',
                'displayName': 'foo',
            },
            'creds': CREDS,
        })

        resp = api.flow.save([
            { 'id': 'foo', 'displayName': 'foo' },
            { 'id': 'bar', 'displayName': 'bar' },
        ])
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow',
            'method': 'MPUT',
            'params': {},
            'data': {
                'foo': { 'id': 'foo', 'displayName': 'foo' },
                'bar': { 'id': 'bar', 'displayName': 'bar' },
            },
            'creds': CREDS,
        })

    def test_delete(self):
        api  = TestAPI()
        resp = api.flow.delete('foo')
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/flow/foo',
            'method': 'DELETE',
            'params': {},
            'data': None,
            'creds': CREDS,
        })

    def test_delete_all(self):
        api  = TestAPI()
        resp = api.drop('foo').delete_all()
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/drop/foo',
            'method': 'DELETE',
            'params': {},
            'data': None,
            'creds': CREDS,
        })

    def test_token_create(self):
        api  = TestAPI()
        resp = api.token.create({
            'paths': { '/foo': { 'administer': True }},
            'duration': 42,
            'description': 'Test',
        })
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/token',
            'method': 'POST',
            'params': {},
            'data': {
              'paths': { '/foo': { 'administer': True }},
              'duration': 42,
              'description': 'Test',
            },
            'creds': CREDS,
        })

    def test_share_create(self):
        api  = TestAPI()
        resp = api.share.create({
            'issuedTo': 'bar',
            'paths': { '/foo': { 'administer': True }},
            'duration': 42,
            'description': 'Test',
        })
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/share',
            'method': 'POST',
            'params': {},
            'data': {
              'issuedTo': 'bar',
              'paths': { '/foo': { 'administer': True }},
              'duration': 42,
              'description': 'Test',
            },
            'creds': CREDS,
        })

    def test_aggregate(self):
        api  = TestAPI()
        resp = api.drop('test').aggregate(['$avg:foo', '$min:bar'],
            group_by=['$month'],
            filter=mem.foo > 12,
            rules={'rule': mem.bar > 42},
            sorts=['foo'])
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/drop/test/aggregate',
            'method': 'POST',
            'params': {},
            'data': {
                'output': ['$avg:foo', '$min:bar'],
                'groupBy': ['$month'],
                'filter': 'foo > 12',
                'rules': {'rule': 'bar > 42'},
                'sorts': ['foo']
            },
            'creds': CREDS,
        })

    def test_statistics(self):
        api  = TestAPI()
        resp = api.statistics.flow_drop_added('foo', 2015, 12, 1, 'year')
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/statistics/flowDropAdded/foo/2015/12/1',
            'method': 'GET',
            'params': { 'level': 'year' },
            'data': None,
            'creds': CREDS,
        })

    def test_drop_create(self):
        api  = TestAPI()
        resp = api.drop.create({ 'path': '/foo' })
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/drop',
            'method': 'POST',
            'params': {},
            'data': { 'path': '/foo' },
            'creds': CREDS,
        })

    def test_ws_session_create(self):
        api  = TestAPI()
        resp = api.websocket.request('POST')
        self.assertEqual(resp, {
            'url': 'https://ws.test/session',
            'method': 'POST',
            'params': {},
            'data': None,
            'creds': CREDS,
        })


class AsyncTestCase(TestCase):

    def test_async_methods(self):
        par = TestAPI().async()
        par.flow.find('foo')
        par.drop('foo').find('bar')
        par.drop.create({ 'path': '/foo' })
        self.assertEqual(par.results(), [
            {
                'async': {
                    'url': 'https://test/vtest/acc/flow/foo',
                    'method': 'GET',
                    'params': {},
                    'data': None,
                    'creds': CREDS
                }
            },
            {
                'async': {
                    'url': 'https://test/vtest/acc/drop/foo/bar',
                    'method': 'GET',
                    'params': {},
                    'data': None,
                    'creds': CREDS
                }
            },
            {
                'async': {
                    'url': 'https://test/vtest/acc/drop',
                    'method': 'POST',
                    'params': {},
                    'data': { 'path': '/foo' },
                    'creds': CREDS
                }
            },
        ])

    def test_lazy_methods(self):
        laz = TestAPI().lazy()
        results = [
            laz.flow.find('foo').unwrap(),
            laz.drop('foo').find('bar').unwrap(),
            laz.drop.create({ 'path': '/foo' }).unwrap(),
        ]
        self.assertEqual(results, [
            {
                'async': {
                    'url': 'https://test/vtest/acc/flow/foo',
                    'method': 'GET',
                    'params': {},
                    'data': None,
                    'creds': CREDS
                }
            },
            {
                'async': {
                    'url': 'https://test/vtest/acc/drop/foo/bar',
                    'method': 'GET',
                    'params': {},
                    'data': None,
                    'creds': CREDS
                }
            },
            {
                'async': {
                    'url': 'https://test/vtest/acc/drop',
                    'method': 'POST',
                    'params': {},
                    'data': { 'path': '/foo' },
                    'creds': CREDS
                }
            },
        ])


class FilterTestCase(TestCase):

    def test_mem_name(self):
        a = str(mem.foo)
        b = str(mem['foo'])
        self.assertEqual(a, b)
        self.assertEqual(a, 'foo')

    def test_mem_operators(self):
        m = mem.foo
        self.assertEqual(str(m == 1), 'foo == 1')
        self.assertEqual(str(m != 1), 'foo != 1')
        self.assertEqual(str(m >  1), 'foo > 1')
        self.assertEqual(str(m >= 1), 'foo >= 1')
        self.assertEqual(str(m <  1), 'foo < 1')
        self.assertEqual(str(m <= 1), 'foo <= 1')
        self.assertEqual(str(m.re('/foo', 'i')), 'foo =~ /\\/foo/i')
        self.assertEqual(str(m.IN(1, 2, 3)), 'foo IN [1,2,3]')
        self.assertEqual(str(m.CONTAINS(1, 2, 3)), 'foo CONTAINS [1,2,3]')
        self.assertEqual(str(m.WITHIN(5, 'KM', [1, 2])), 'foo WITHIN 5 KM OF [1,2]')
        self.assertEqual(str(m.WITHIN(5, 'KM', zip=123)), 'foo WITHIN 5 KM OF [ZIP=123]')

    def test_AGE(self):
        self.assertEqual(str(AGE == 123), 'AGE == 123')
        self.assertEqual(str(AGE != 123), 'AGE != 123')
        self.assertEqual(str(AGE >  123), 'AGE > 123')
        self.assertEqual(str(AGE >= 123), 'AGE >= 123')
        self.assertEqual(str(AGE <  123), 'AGE < 123')
        self.assertEqual(str(AGE <= 123), 'AGE <= 123')

    def test_EXISTS(self):
        self.assertEqual(str(EXISTS('foo')), 'EXISTS foo')
        self.assertEqual(str(EXISTS(mem['foo'])), 'EXISTS foo')
        self.assertEqual(str(EXISTS(mem.foo)), 'EXISTS foo')

    def test_MATCHES(self):
        self.assertEqual(str(MATCHES('foo', 'i')), 'MATCHES /foo/i')

    def test_HAS(self):
        self.assertEqual(str(HAS('foo')), 'HAS foo')

    def test_NOT(self):
        self.assertEqual(str(NOT(mem.foo == 1)), 'NOT foo == 1')

    def test_AND(self):
        self.assertEqual(str((mem.foo == 1).AND(mem.bar == 2)), '(foo == 1) && (bar == 2)')

    def test_OR(self):
        self.assertEqual(str((mem.foo == 1).OR(mem.bar == 2)), '(foo == 1) || (bar == 2)')


class BluemixTestCase(TestCase):

    def test_load_env(self):
        import os
        import json
        os.environ['VCAP_SERVICES'] = json.dumps({
            'flowthings': [
                {
                    'credentials': {
                        'account': 'test',
                        'token': 'token',
                    }
                }
            ]
        })

        token = Token.from_bluemix()
        self.assertEqual(token.account, 'test')
        self.assertEqual(token.token, 'token')

    def test_default(self):
        token = Token.from_bluemix(Token('foo', 'bar'), env_var='DOES_NOT_EXIST_PROBABLY')
        self.assertEqual(token.account, 'foo')
        self.assertEqual(token.token, 'bar')
