from __future__ import absolute_import
import os
import json
from copy import deepcopy
from collections import namedtuple

from .exceptions import FlowThingsError
from six.moves import map
import six
from functools import reduce


__all__ = (
    'Token',
    'Params',
    'Modify',
    'P',
    'M',
    'mem',
    'AGE',
    'EXISTS',
    'MATCHES',
    'HAS',
    'NOT',
)


Token = namedtuple('Token', ['account', 'token'])


def from_bluemix(default=None, env_var='VCAP_SERVICES'):
    try:
        vcap = json.loads(os.environ[env_var])
        conf = vcap['flowthings'][0]['credentials']
        return Token(conf['account'], conf['token'])
    except:
        if default:
            return default
        else:
            raise FlowThingsError('Bluemix credentials not found')


setattr(Token, 'from_bluemix', staticmethod(from_bluemix))


class Params(object):
    """ All API methods can take a dict for params, but you can also use this
    param builder, which is a little nicer. The API will recognize it and call
    `to_dict` for you. 

    You can use both keyword args and setter methods:

        >>> params = P(start=10, limit=100)
        >>> params.refs(True).some_other_param('foo')
        >>> params.to_dict()
        {'start': 10, 
         'limit': 100, 
         'refs': 1, 
         'some_other_param': 'foo'}
    """

    def __init__(self, **kwargs):
        self._params = {}
        for k, v in kwargs.items():
            getattr(self, k)(v)

    def refs(self, toggle):
        toggle = 1 if toggle else 0
        self._params['refs'] = toggle
        return self

    def only(self, *args):
        args = (','.join(a) if isinstance(a, (list, tuple)) else a for a in args)
        self._params['only'] = ','.join(args)
        return self

    def filter(self, f, *args):
        if isinstance(f, Filter):
            f = str(reduce(lambda x, y: x.AND(y), args, f))
        if isinstance(f, (list, tuple)):
            f = str(reduce(lambda x, y: x.AND(y), f))
        self._params['filter'] = f
        return self

    def to_dict(self):
        return self._params

    def __getattr__(self, name):
        def generic_setter(self, value):
            self._params[name] = value
            return self
        return generic_setter.__get__(self, Params)


class Modify(object):
    """ Use this to wrap a model dict and perform incremental updates. At the
    end you can call `done` to get a new model with the fields updated, and
    another dict of just the changed fields. You can pass Modify objects to
    API services. The services will send only the changed fields.

        >>> data = {'foo': 'bar'}
        >>> mod = M(data, baz='qux')
        >>> data2, diff = mod.done()
        ({'foo': 'bar', 'baz': 'qux'}, {'baz': 'qux'})
    """

    def __init__(self, model=None, **kwargs):
        self._model = deepcopy(model) if model else {}
        self._changes = {}
        for k, v in kwargs.items():
            self.modify(k, v)

    def modify(self, key, val):
        self._model[key] = val
        self._changes[key] = val

    def done(self):
        return (self._model, self._changes)


P = Params
M = Modify


class Filter(object):
    def AND(self, that):
        return LogicalFilter(self, '&&', that)

    def OR(self, that):
        return LogicalFilter(self, '||', that)


class PrefixFilter(Filter):
    def __init__(self, member, operator):
        self.member = member
        self.operator = operator

    def __str__(self):
        return '%s %s' % (self.operator, str(self.member))


class BinaryFilter(Filter):
    def __init__(self, member, operator, operand):
        self.member = member
        self.operator = operator
        self.operand = operand

    def __str__(self):
        return ' '.join((str(self.member), self.operator, prim_str(self.operand)))


class LogicalFilter(BinaryFilter):
    def __init__(self, f1, operator, f2):
        assert isinstance(f1, Filter) and isinstance(f2, Filter), 'Operands must be filters'
        self.member = f1
        self.operator = operator
        self.operand = f2

    def __str__(self):
        return '(%s) %s (%s)' % (str(self.member), self.operator, str(self.operand))


class ListFilter(BinaryFilter):
    def __init__(self, member, operator, operand):
        assert isinstance(operand, (list, tuple)), 'Operand must be a list or tuple'
        self.member = member
        self.operator = operator
        self.operand = operand

    def __str__(self):
        return '%s %s [%s]' % (str(self.member), self.operator, ','.join(map(prim_str, self.operand)))


class LocationFilter(Filter):
    def __init__(self, member, unit, loc):
        self.member = member
        self.unit = unit
        self.loc = loc

    def __str__(self):
        return '%s WITHIN %s OF [%s]' % (str(self.member), self.unit, self.loc)


class AgeFilter(Filter):
    def __init__(self, member, operator, ms):
        assert isinstance(ms, (int, float)) and ms > 0, 'Age must be a number greater than 0'
        self.member = member
        self.operator = operator
        self.ms = ms

    def __str__(self):
        if self.member is None:
            return 'AGE %s %s' % (self.operator, self.ms)
        else:
            return 'AGE(%s) %s %s' % (prim_str(self.member), self.operator, self.ms)


class MatchesFilter(Filter):
    def __init__(self, re):
        self.re = re

    def __str__(self):
        return 'MATCHES ' + str(self.re)


class HasFilter(Filter):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return 'HAS ' + str(self.name)


class NotFilter(Filter):
    def __init__(self, filter):
        self.filter = filter

    def __str__(self):
        return 'NOT ' + str(self.filter)


class Regex(object):
    def __init__(self, pattern, flags):
        self.pattern = pattern
        self.flags = flags

    def __str__(self):
        return '/%s/%s' % (self.pattern.replace('/', '\\/'), self.flags)


class Member(object):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __getattr__(self, attr):
        return Member('%s.%s' % (self.name, attr))

    def __getitem__(self, attr):
        return Member('%s.%s' % (self.name, attr))

    def __eq__(self, that):
        return BinaryFilter(self, '==', that);

    def __ne__(self, that):
        return BinaryFilter(self, '!=', that);

    def __gt__(self, that):
        return BinaryFilter(self, '>', that);

    def __ge__(self, that):
        return BinaryFilter(self, '>=', that);

    def __lt__(self, that):
        return BinaryFilter(self, '<', that);

    def __le__(self, that):
        return BinaryFilter(self, '<=', that);

    def re(self, pattern, flags=''):
        return BinaryFilter(self, '=~', Regex(pattern, flags))

    def IN(self, *args):
        return ListFilter(self, 'IN', args)

    def CONTAINS(self, *args):
        return ListFilter(self, 'CONTAINS', args)

    def WITHIN(self, num, unit='MILES', coords=None, zip=None):
        return LocationFilter(self, '%s %s' % (num, unit), ','.join(map(str, coords)) if coords else 'ZIP=' + str(zip))


class MemberFactory(object):
    def __getitem__(self, name):
        return Member(name)

    def __getattr__(self, name):
        return Member(name)

mem = MemberFactory()


class AgeFactory(object):
    def __init__(self, member=None):
        self.member = member

    def __call__(self, name):
        if self.member is None:
            return AgeFactory(name)
        else:
            return AgeFactory('%s.%s' % (self.member, name))

    def __eq__(self, that):
        return AgeFilter(self.member, '==', that)

    def __ne__(self, that):
        return AgeFilter(self.member, '!=', that)

    def __gt__(self, that):
        return AgeFilter(self.member, '>', that)

    def __ge__(self, that):
        return AgeFilter(self.member, '>=', that)

    def __lt__(self, that):
        return AgeFilter(self.member, '<', that)

    def __le__(self, that):
        return AgeFilter(self.member, '<=', that)

AGE = AgeFactory(None)


def EXISTS(name):
    return PrefixFilter(name if isinstance(name, Member) else Member(name), 'EXISTS')


def MATCHES(re, flags=''):
    return MatchesFilter(Regex(re, flags)) 


def HAS(ty):
    return HasFilter(ty)


def NOT(filter):
    return NotFilter(filter)


PRIMITIVE_OPERANDS = (Member, Regex, str, six.text_type, int, float, bool)


def prim_str(prim):
    if isinstance(prim, bool):
        return 'true' if prim else 'false'
    if isinstance(prim, (str, six.text_type)):
        return "'%s'" % prim.replace("'", "\\'")
    if isinstance(prim, (Member, Regex, int, float)):
        return str(prim)
    assert False, 'Must be a filter primitive'
