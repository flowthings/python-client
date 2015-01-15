class FlowPlatError(Exception):
    pass


class FlowPlatException(Exception):
    def __init__(self, errors=[], creds=None, method=None, path=None):
        self.errors = errors
        self.creds = creds
        self.method = method
        self.path = path

    def __repr__(self):
        parts = filter(None, [
            self.creds.account if self.creds else None,
            self.method,
            self.path,
            str(self.errors) if self.errors else None ])

        return '<%s %s>' % (self.__class__.__name__, ' '.join(parts))


class FlowPlatBadRequest(FlowPlatException):
    pass


class FlowPlatForbidden(FlowPlatException):
    pass


class FlowPlatNotFound(FlowPlatException):
    pass


class FlowPlatServerError(FlowPlatException):
    pass
