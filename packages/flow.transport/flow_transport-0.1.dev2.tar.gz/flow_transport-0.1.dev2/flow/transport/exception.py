class Error(Exception):
    pass


class LinkError(Error):
    pass


class ProtocolError(Error):
    pass


class ConnectionClosed(Error):
    pass
