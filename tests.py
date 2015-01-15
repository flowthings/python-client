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


def TestAPI(*args, **kwargs):
    if 'request' not in kwargs:
        kwargs['request'] = mock_api_request_ok

    if 'encoder' not in kwargs:
        kwargs['encoder'] = IdEncoder()

    if 'host' not in kwargs:
        kwargs['host'] = 'test'

    if 'version' not in kwargs:
        kwargs['version'] = 'test'

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

    def test_token_create(self):
        api  = TestAPI()
        resp = api.token.create({
            'paths': { '/foo': { 'administer': True }},
            'expiresInMs': 42,
            'description': 'Test',
        })
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/token',
            'method': 'POST',
            'params': {},
            'data': {
              'paths': { '/foo': { 'administer': True }},
              'expiresInMs': 42,
              'description': 'Test',
            },
            'creds': CREDS,
        })

    def test_share_create(self):
        api  = TestAPI()
        resp = api.share.create({
            'issuedTo': 'bar',
            'paths': { '/foo': { 'administer': True }},
            'expiresInMs': 42,
            'description': 'Test',
        })
        self.assertEqual(resp, {
            'url': 'https://test/vtest/acc/share',
            'method': 'POST',
            'params': {},
            'data': {
              'issuedTo': 'bar',
              'paths': { '/foo': { 'administer': True }},
              'expiresInMs': 42,
              'description': 'Test',
            },
            'creds': CREDS,
        })


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
