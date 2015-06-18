class FlowThingsError(Exception):
    pass


class FlowThingsException(Exception):
    def __init__(self, errors=[], creds=None, method=None, path=None):
        self.errors = errors
        self.creds = creds
        self.method = method
        self.path = path

    def __repr__(self):
        parts = [_f for _f in [
            self.creds.account if self.creds else None,
            self.method,
            self.path,
            str(self.errors) if self.errors else None ] if _f]

        return '<%s %s>' % (self.__class__.__name__, ' '.join(parts))


class FlowThingsBadRequest(FlowThingsException):
    pass


class FlowThingsForbidden(FlowThingsException):
    pass


class FlowThingsNotFound(FlowThingsException):
    pass


class FlowThingsServerError(FlowThingsException):
    pass
