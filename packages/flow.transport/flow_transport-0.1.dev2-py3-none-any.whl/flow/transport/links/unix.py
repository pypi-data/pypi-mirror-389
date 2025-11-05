from __future__ import annotations

import asyncio
import logging
import sys
from typing import TYPE_CHECKING

from flow.transport.base import (
    ClientLink,
    ServerLink,
    T,
)
from flow.transport.exception import LinkError

if TYPE_CHECKING:
    from collections.abc import Callable

log = logging.getLogger(__name__)


class UnixClientLink(ClientLink):
    def __init__(self, address: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.address = address

        if sys.platform == "win32":
            raise LinkError("Unix link is not available on win32")

        if sys.platform == "darwin" and self.address.startswith("@"):
            raise LinkError("Unix abstract sockets are not available on darwin")

    def __repr__(self) -> str:
        uplink = f" uplink={self.uplink!r}" if self.uplink else ""
        abstract = " (abstract)" if self.address.startswith(("@", "\0")) else ""
        return f"<{self.__class__.__name__} address={self.address!r}{abstract}{uplink}>"

    async def _connect(self, protocol_factory: Callable[[], T], **kwargs) -> tuple[asyncio.Transport, T]:
        log.debug("%s connecting to %s", self, self.address)

        address = self.address
        if address.startswith("@"):
            # Abstract namespace: replace leading @ with null byte
            address = "\0" + self.address[1:]

        loop = asyncio.get_running_loop()
        return await loop.create_unix_connection(protocol_factory, address, **kwargs)


class UnixServerLink(ServerLink):
    def __init__(self, address: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.address = address

        if sys.platform == "win32":
            raise LinkError("Unix link is not available on win32")

        if sys.platform == "darwin" and self.address.startswith("@"):
            raise LinkError("Unix abstract sockets are not available on darwin")

    def __repr__(self) -> str:
        uplink = f" uplink={self.uplink!r}" if self.uplink else ""
        abstract = " (abstract)" if self.address.startswith(("@", "\0")) else ""
        return f"<{self.__class__.__name__} address={self.address!r}{abstract}{uplink}>"

    async def _serve(self, protocol_factory: Callable[[], T], **kwargs) -> asyncio.AbstractServer:
        loop = asyncio.get_running_loop()

        address = self.address
        if address.startswith("@"):
            # Abstract namespace: replace leading @ with null byte
            address = "\0" + self.address[1:]

        server = await loop.create_unix_server(protocol_factory, address, **kwargs)
        for sock in server.sockets:
            # Display abstract socket addresses properly
            if isinstance(sock_address := sock.getsockname(), bytes) and sock_address[0] == 0:
                display_address = "@" + sock_address[1:].decode()
            else:
                display_address = sock_address
            log.debug("%s listening on %s", self, display_address)

        return server
