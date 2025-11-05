from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from flow.transport.base import (
    ClientLink,
    ServerLink,
    T,
)

if TYPE_CHECKING:
    from collections.abc import Callable

log = logging.getLogger(__name__)


class TcpClientLink(ClientLink):
    """TCP client link.

    Args:
        address: Server address to connect to.
        port: Server port to connect to.
    """

    def __init__(self, address: str, port: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.address = address
        self.port = port

    def __repr__(self) -> str:
        uplink = f" uplink={self.uplink!r}" if self.uplink else ""
        return f"<{self.__class__.__name__} address={self.address!r} port={self.port}{uplink}>"

    async def _connect(self, protocol_factory: Callable[[], T], **kwargs) -> tuple[asyncio.Transport, T]:
        log.debug("%s connecting to %s:%u", self, self.address, self.port)
        loop = asyncio.get_running_loop()
        return await loop.create_connection(protocol_factory, self.address, self.port, **kwargs)


class TcpServerLink(ServerLink):
    """TCP server link.

    Args:
        address: Address to bind the server to.
        port: Port to bind the server to.
    """

    def __init__(self, address: str, port: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.address = address
        self.port = port

    def __repr__(self) -> str:
        uplink = f" uplink={self.uplink!r}" if self.uplink else ""
        return f"<{self.__class__.__name__} address={self.address!r} port={self.port}{uplink}>"

    async def _serve(self, protocol_factory: Callable[[], T], **kwargs) -> asyncio.Server:
        loop = asyncio.get_running_loop()

        server = await loop.create_server(protocol_factory, self.address, self.port, **kwargs)
        for sock in server.sockets:
            address, port = sock.getsockname()
            log.debug("%s listening on %s:%u", self, address, port)

        return server
