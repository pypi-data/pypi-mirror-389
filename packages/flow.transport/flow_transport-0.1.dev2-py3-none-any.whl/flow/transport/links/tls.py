from __future__ import annotations

import asyncio
import logging
import os
import ssl
from pathlib import Path
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


class TlsClientLink(ClientLink):
    """TLS client link.

    Args:
        address: Server address to connect to.
        port: Server port to connect to.
        cafile: CA file to use.
        certfile: Certificate file to use.
        keyfile: Key file to use.
        verify: Whether to verify the server certificate.
    """

    def __init__(
        self,
        address: str | None = None,
        port: int | None = None,
        cafile: str | Path | None = None,
        certfile: str | Path | None = None,
        keyfile: str | Path | None = None,
        verify: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.address = address
        self.port = port

        if not self.uplink and not self.address and not self.port:
            raise LinkError("TLS link requires an uplink or address and port")

        self.cafile, self.certfile, self.keyfile = get_tls_certs(cafile, certfile, keyfile)
        if not self.cafile or not self.certfile or not self.keyfile:
            raise LinkError("TLS link requires cafile, certfile and keyfile")

        self.verify = verify

    def __repr__(self) -> str:
        uplink = f" uplink={self.uplink!r}" if self.uplink else ""
        return f"<{self.__class__.__name__} address={self.address!r} port={self.port} verify={self.verify}{uplink}>"

    async def _connect(self, protocol_factory: Callable[[], T], **kwargs) -> tuple[asyncio.Transport, T]:
        loop = asyncio.get_running_loop()

        ctx = setup_context(ssl.PROTOCOL_TLS_CLIENT, self.cafile, self.certfile, self.keyfile, self.verify)

        if self.uplink:
            # If we have an uplink, first connect using the uplink, then upgrade to TLS
            log.debug("%s connecting with uplink %s", self, self.uplink)
            uplink_transport, protocol = await self.uplink._connect(protocol_factory, **kwargs)

            log.debug("%s upgrading transport to TLS for %s", self, protocol)
            tls_transport = await loop.start_tls(uplink_transport, protocol, ctx)
            protocol.transport = tls_transport
            return tls_transport, protocol

        if self.address and self.port:
            # If we don't have an uplink, connect directly using TLS (+ TCP)
            log.debug("%s connecting to %s:%u", self, self.address, self.port)
            return await loop.create_connection(protocol_factory, self.address, self.port, ssl=ctx)

        raise RuntimeError("Invalid TLS link state")


class TlsServerLink(ServerLink):
    """TLS server link.

    Args:
        address: Address to bind the server to.
        port: Port to bind the server to.
        cafile: CA file to use.
        certfile: Certificate file to use.
        keyfile: Key file to use.
        verify: Whether to verify client certificates.
    """

    def __init__(
        self,
        address: str | None = None,
        port: int | None = None,
        cafile: Path | None = None,
        certfile: Path | None = None,
        keyfile: Path | None = None,
        verify: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.address = address
        self.port = port

        if not self.uplink and not self.address and not self.port:
            raise LinkError("TLS link requires an uplink or address and port")

        self.cafile, self.certfile, self.keyfile = get_tls_certs(cafile, certfile, keyfile)
        if not self.cafile or not self.certfile or not self.keyfile:
            raise LinkError("TLS link requires cafile, certfile and keyfile")

        self.verify = verify

    def __repr__(self) -> str:
        uplink = f" uplink={self.uplink!r}" if self.uplink else ""
        return f"<{self.__class__.__name__} address={self.address!r} port={self.port} verify={self.verify}{uplink}>"

    async def _serve(self, protocol_factory: Callable[[], T], **kwargs) -> asyncio.AbstractServer:
        ctx = setup_context(ssl.PROTOCOL_TLS_SERVER, self.cafile, self.certfile, self.keyfile, self.verify)

        if self.uplink:
            # If we have an uplink, we serve a special factory that upgrades to TLS
            log.debug("%s serving with uplink %s", self, self.uplink)
            return await self.uplink._serve(_upgrade_factory(protocol_factory, ctx))

        if self.address and self.port:
            # If we don't have an uplink, serve directly using TLS (+ TCP)
            loop = asyncio.get_running_loop()

            server = await loop.create_server(protocol_factory, self.address, self.port, ssl=ctx)
            for sock in server.sockets:
                address = sock.getsockname()
                log.debug("%s listening on %s", self, address)

            return server

        raise RuntimeError("Invalid TLS link state")


def _upgrade_factory(protocol_factory: Callable[[], T], ctx: ssl.SSLContext) -> Callable[[], T]:
    """Wrap a protocol factory to upgrade the transport to TLS when the connection is made."""

    def factory() -> T:
        protocol = protocol_factory()
        original_connection_made = protocol.connection_made

        def connection_made_upgrade(transport: asyncio.Transport) -> None:
            async def _upgrade_tls_server(
                loop: asyncio.AbstractEventLoop, transport: asyncio.Transport, protocol: asyncio.Protocol
            ) -> None:
                log.debug("Upgrading transport to TLS for %s", protocol)
                tls_transport = await loop.start_tls(transport, protocol, ctx, server_side=True)
                original_connection_made(tls_transport)

            loop = asyncio.get_running_loop()
            transport.__upgrade_task = loop.create_task(_upgrade_tls_server(loop, transport, protocol))
            transport.__upgrade_task.add_done_callback(
                lambda t: protocol.close(t.exception()) if t.exception() else None
            )

        protocol.connection_made = connection_made_upgrade
        return protocol

    return factory


def setup_context(
    protocol: ssl._SSLMethod,
    cafile: Path | None,
    certfile: Path | None,
    keyfile: Path | None,
    verify: bool = True,
) -> ssl.SSLContext:
    """Setup an SSLContext with the given arguments.

    Args:
        cafile: CA file to use.
        certfile: Certificate file to use.
        keyfile: Key file to use.

    Returns:
        An SSLContext created from the given arguments.
    """
    if not cafile:
        raise ValueError("Missing cafile")
    if not certfile:
        raise ValueError("Missing certfile")
    if not keyfile:
        raise ValueError("Missing keyfile")

    ctx = ssl.SSLContext(protocol)

    ctx.load_verify_locations(cafile=cafile)
    ctx.load_cert_chain(certfile, keyfile)

    ctx.minimum_version = ssl.TLSVersion.TLSv1_2

    if verify:
        ctx.verify_mode = ssl.CERT_REQUIRED
    else:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    return ctx


def get_tls_certs(
    cafile: str | Path | None, certfile: str | Path | None, keyfile: str | Path | None
) -> tuple[Path | None, Path | None, Path | None]:
    """Returns (cafile, certfile, keyfile) if specified or from the following environment variables:

    - ``FLOW_TLS_CA``
    - ``FLOW_TLS_CRT``
    - ``FLOW_TLS_KEY``

    Args:
        cafile: CA file to use.
        certfile: Certificate file to use.
        keyfile: Key file to use.

    Returns:
        A tuple of (cafile, certfile, keyfile) either loaded from the arguments or environment variables.
    """
    cafile = cafile or os.environ.get("FLOW_TLS_CA")
    certfile = certfile or os.environ.get("FLOW_TLS_CRT")
    keyfile = keyfile or os.environ.get("FLOW_TLS_KEY")
    return (
        Path(cafile) if cafile else None,
        Path(certfile) if certfile else None,
        Path(keyfile) if keyfile else None,
    )
