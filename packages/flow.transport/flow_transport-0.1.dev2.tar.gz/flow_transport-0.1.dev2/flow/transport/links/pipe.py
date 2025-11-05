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

    from typing_extensions import Self

log = logging.getLogger(__name__)


class PipeClientLink(ClientLink):
    def __init__(self, address: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.address = make_pipe_address(address)

        if sys.platform != "win32":
            raise LinkError("Pipe link is only available on win32")

    def __repr__(self) -> str:
        uplink = f" uplink={self.uplink!r}" if self.uplink else ""
        return f"<{self.__class__.__name__} address={self.address!r}{uplink}>"

    async def _connect(self, protocol_factory: Callable[[], T], **kwargs) -> tuple[asyncio.Transport, T]:
        log.debug("%s connecting to %s", self, self.address)

        loop = asyncio.get_running_loop()
        return await loop.create_pipe_connection(protocol_factory, self.address)


class PipeServerLink(ServerLink):
    def __init__(self, address: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.address = make_pipe_address(address)

        if sys.platform != "win32":
            raise LinkError("Pipe link is only available on win32")

    def __repr__(self) -> str:
        uplink = f" uplink={self.uplink!r}" if self.uplink else ""
        return f"<{self.__class__.__name__} address={self.address!r}{uplink}>"

    async def _serve(self, protocol_factory: Callable[[], T], **kwargs) -> asyncio.AbstractServer:
        loop = asyncio.get_running_loop()
        server = CompatiblePipeServer(loop, self.address, protocol_factory)
        if kwargs.get("start_serving", True):
            await server.start_serving()

        log.debug("%s listening on %s", self, self.address)

        return server


class CompatiblePipeServer(asyncio.AbstractServer):
    def __init__(self, loop: asyncio.AbstractEventLoop, address: str, protocol_factory: Callable[[], T]):
        self._loop = loop
        self._address = address
        self._protocol_factory = protocol_factory

        self._pipe_server = None
        self._serving = False
        self._serving_forever_fut = None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} pipe_server={self._pipe_server!r}>"

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc) -> None:
        self.close()
        await self.wait_closed()

    def close(self) -> None:
        if self._pipe_server:
            self._pipe_server.close()
        self._serving = False

    def get_loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    def is_serving(self) -> bool:
        return self._serving

    async def start_serving(self) -> None:
        if self._serving:
            return
        [self._pipe_server] = await self._loop.start_serving_pipe(self._protocol_factory, self._address)
        self._serving = True

    async def serve_forever(self) -> None:
        if self._serving_forever_fut is not None:
            raise RuntimeError(f"server {self!r} is already being awaited on serve_forever()")
        if self._pipe_server is None:
            raise RuntimeError(f"server {self!r} is closed")

        await self.start_serving()
        self._serving_forever_fut = self._loop.create_future()

        try:
            await self._serving_forever_fut
        except asyncio.CancelledError:
            try:
                self.close()
                await self.wait_closed()
            finally:
                raise
        finally:
            self._serving_forever_fut = None

    async def wait_closed(self) -> None:
        return


def make_pipe_address(address: str) -> str:
    if address.startswith("\\\\.\\pipe\\"):
        return address

    return f"\\\\.\\pipe\\{address}"
