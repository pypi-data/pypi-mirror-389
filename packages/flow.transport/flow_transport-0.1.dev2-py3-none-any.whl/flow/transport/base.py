from __future__ import annotations

import asyncio
import importlib
import logging
import struct
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar
from urllib.parse import parse_qsl, urlparse

from flow.transport.exception import ConnectionClosed, LinkError, ProtocolError

if TYPE_CHECKING:
    from collections.abc import Callable

    from typing_extensions import Self

TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")


class TraceLogger(logging.Logger):
    def trace(self, msg: Any, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(TRACE_LEVEL):
            self._log(TRACE_LEVEL, msg, args, **kwargs)


logging.setLoggerClass(TraceLogger)


def get_logger(name: str | None = None) -> TraceLogger:
    """Get a logger with ``TRACE`` support."""
    return logging.getLogger(name)


log = get_logger(__package__)

DEFAULT_STREAM_LIMIT = 2**16  # 64 KiB


class FlowProtocol(asyncio.Protocol):
    """Slightly customized ``asyncio.Protocol`` class to provide some convenience methods and callbacks.

    Users of flow.transport must subclass from this class when using a protocol factory.
    """

    link: Link | None
    transport: asyncio.Transport | None

    def __init__(self):
        self.link = None
        self.transport = None
        self._kwargs = {}
        self._closed = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc) -> None:
        self.close()

    def send(self, data: bytes) -> None:
        """Send data over the transport, if it's connected."""
        if not self.transport:
            raise ConnectionClosed("Connection is closed")
        self.transport.write(data)

    def close(self, exc: Exception | None = None) -> None:
        """Close the transport."""
        log.trace("%s: Closing protocol: %s", self, exc)
        if self.transport:
            self.transport.close()
            self.transport = None

        if not self._closed:
            self._closed = True
            self.on_close(exc)

    def connection_made(self, transport: asyncio.Transport) -> None:
        """Original asyncio callback, store a reference to the transport and call :meth:`FlowProtocol.on_connect`."""
        log.trace("%s: Connection made: %s", self, transport)
        self.transport = transport
        self.on_connect(transport)

    def data_received(self, data: bytes) -> None:
        """Original asyncio callback, call :meth:`FlowProtocol.on_data`."""
        self.on_data(data)

    def connection_lost(self, exc: Exception | None) -> None:
        """Original asyncio callback, close the protocol."""
        log.trace("%s: Connection lost: %s", self, exc)
        self.on_connection_lost(exc)
        self.close(exc)

    # There's not much we want to do with eof_received, so don't implement it

    def on_connect(self, transport: asyncio.Transport) -> None:
        """Callback when a new connection is made."""

    def on_data(self, data: bytes) -> None:
        """Callback when new data is received."""

    def on_connection_lost(self, exc: Exception | None) -> None:
        """Callback when the connection is lost."""

    def on_close(self, exc: Exception | None) -> None:
        """Callback when the connection is closed."""


class FlowPacketProtocol(FlowProtocol):
    """A packet based protocol implementation.

    This protocol implementation adds a simple packet framing on top of :class:`FlowProtocol`.
    Each packet is prefixed with a 4-byte big-endian unsigned integer indicating the packet size.

    Data is received in chunks and reassembled into complete packets before being passed to
    :meth:`FlowProtocol.on_data`.

    Args:
        max_packet_size: Maximum allowed packet size. If a packet exceeds this size, the connection is closed.
    """

    def __init__(self, max_packet_size: int = 100 * 1024 * 1024):
        super().__init__()
        self.max_packet_size = max_packet_size
        self._packet_size = None
        self._buffer = bytearray()

    def send(self, data: bytes) -> None:
        """Send a packet over the transport, if it's connected.

        Prepends the data with a size indicator so that the receiving side can wait until the packet is complete.
        """
        super().send(struct.pack(">I", len(data)) + data)

    def data_received(self, data: bytes) -> None:
        """Original asyncio callback, only call :meth:`FlowProtocol.on_data` with a complete packet."""
        self._buffer += data

        if self._packet_size is None:
            self._read_packet_size()

        while self._packet_size is not None and len(self._buffer) >= self._packet_size:
            self.on_data(self._buffer[: self._packet_size])
            self._buffer = self._buffer[self._packet_size :]
            self._read_packet_size()

    def _read_packet_size(self) -> None:
        if len(self._buffer) < 4:
            self._packet_size = None
            return

        new_packet_size = struct.unpack(">I", self._buffer[:4])[0]
        if new_packet_size > self.max_packet_size:
            # Something is wrong, close the connection
            self.close(ProtocolError(f"Packet size ({new_packet_size}) exceeds maximum size ({self.max_packet_size})"))
            return

        self._buffer = self._buffer[4:]
        self._packet_size = new_packet_size


class ReconnectMixin(FlowProtocol):
    """Mixin for providing reconnecting functionality to client protocol implementations.

    Add this as a mixin to your protocol class like so::

        class MyClientProtocol(ReconnectMixin, FlowProtocol):

    Will perform incremental reconnects until the connection is reestablished.
    """

    def __init__(self, reconnect_interval: float = 0.5):
        super().__init__()
        self._reconnect_interval = reconnect_interval
        self._reconnect_task = None
        self._current_interval = reconnect_interval

    def connection_lost(self, exc: Exception | None) -> None:
        log.trace("%s: Connection lost, starting reconnect task: %s", self, exc)
        if self.link and self.link.is_client and not self._closed:
            self.on_connection_lost(exc)
            self._reconnect_task = asyncio.get_running_loop().create_task(self._reconnect())

    async def _reconnect(self) -> None:
        while True:
            try:
                await self.link._connect(lambda: self, **self._kwargs)
                self._current_interval = self._reconnect_interval
                break
            except OSError:
                self._current_interval = min(60, 1.5 * self._current_interval)
                log.trace(
                    "%s: Connect failed, retrying in %f seconds...",
                    self,
                    self._current_interval,
                )
                await asyncio.sleep(self._current_interval)
            finally:
                self._reconnect_task = None


T = TypeVar("T", bound="FlowProtocol")


class Link(Generic[T]):
    """Base link implementation.

    Links act as a factory for new connections or servers. They hold no state themselves.

    Both client and server implementations provide two connection type factories:
      - Callback based protocol connections using :class:`FlowProtocol`
      - Streaming connections using :class:`StreamReader` and :class:`StreamWriter`
    """

    def __init__(self, uplink: Link | None = None, **kwargs):
        self.uplink = uplink

    def __repr__(self) -> str:
        uplink = f" uplink={self.uplink!r}" if self.uplink else ""
        return f"<{self.__class__.__name__}{uplink}>"

    @property
    def is_client(self) -> bool:
        return isinstance(self, ClientLink)

    @property
    def is_server(self) -> bool:
        return isinstance(self, ServerLink)

    @staticmethod
    def create(uri: str, **kwargs) -> Link:
        """Create a link based on the given URI."""
        raise NotImplementedError


class ClientLink(Link):
    @staticmethod
    def create(uri: str, **kwargs) -> ClientLink:
        """Create a link based on the given URI."""
        return create_client_link(uri, **kwargs)

    async def connect(self, protocol_factory: Callable[[], T], **kwargs) -> T:
        """Create a new callback based protocol connection on client links.

        Args:
            protocol_factory: A callable that must return an instance of :class:`FlowProtocol`
            **kwargs: Arguments to be passed to the underlying connect implementation.

        Returns:
            A new instance of :class:`FlowProtocol`.
        """
        protocol = protocol_factory()
        if not isinstance(protocol, FlowProtocol):
            raise TypeError("Protocol must subclass FlowProtocol")

        protocol.link = self
        protocol._kwargs = kwargs

        if isinstance(protocol, ReconnectMixin):
            await protocol._reconnect()
        else:
            await self._connect(lambda: protocol, **kwargs)
        return protocol

    async def connect_stream(
        self, limit: int = DEFAULT_STREAM_LIMIT, **kwargs
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        """Create a new stream based connection on client links.

        Args:
            limit: The buffer size limit for the ``StreamReader`` instance.
            **kwargs: Arguments to be passed to the underlying connect implementation.

        Returns:
            A tuple of ``StreamReader`` and ``StreamWriter``.
        """
        reader = asyncio.StreamReader(limit=limit)
        protocol = asyncio.StreamReaderProtocol(reader)
        transport, _ = await self._connect(lambda: protocol, **kwargs)
        writer = asyncio.StreamWriter(transport, protocol, reader, asyncio.get_running_loop())
        return reader, writer

    async def _connect(self, protocol_factory: Callable[[], T], **kwargs) -> tuple[asyncio.Transport, T]:
        """Internal connect implementation. Must be implemented by client link implementations."""
        raise NotImplementedError


class ServerLink(Link):
    @staticmethod
    def create(uri: str, **kwargs) -> ServerLink:
        """Create a link based on the given URI."""
        return create_server_link(uri, **kwargs)

    async def serve(self, protocol_factory: Callable[[], T], **kwargs) -> asyncio.Server:
        """Create a new callback based protocol server on server links.

        Args:
            protocol_factory: A callable that must return an instance of FlowProtocol
            **kwargs: Arguments to be passed to the underlying server implementation.

        Returns:
            A new ``asyncio.Server`` instance.
        """
        protocol = protocol_factory()
        if not isinstance(protocol, FlowProtocol):
            raise TypeError("Protocol must subclass FlowProtocol")

        server = await self._serve(protocol_factory, **kwargs)
        server.link = self
        server._kwargs = kwargs

        return server

    async def serve_stream(
        self,
        callback: Callable[[asyncio.StreamReader, asyncio.StreamWriter], None],
        limit: int = DEFAULT_STREAM_LIMIT,
        **kwargs,
    ) -> asyncio.Server:
        """Create a new stream based server on server links.

        Args:
            callback: Callable that receives a ``StreamReader`` and ``StreamWriter`` on new connections.
            limit: The buffer size limit for the ``StreamReader`` instance.
            **kwargs: Arguments to be passed to the underlying server implementation.

        Returns:
            A new ``asyncio.Server`` instance.
        """

        def factory() -> asyncio.StreamReaderProtocol:
            reader = asyncio.StreamReader(limit=limit)
            return asyncio.StreamReaderProtocol(reader, callback)

        return await self._serve(factory, **kwargs)

    async def _serve(self, protocol_factory: Callable[[], T], **kwargs) -> asyncio.Server:
        """Internal serve implementation. Must be implemented by server link implementations."""
        raise NotImplementedError


def create_client_link(uri: str, **kwargs) -> Link:
    """Creates a client link with the given arguments based on the given URI.

    Args:
        uri: The URI to find and create a :class:`Link` for.
        **kwargs: Arguments to be passed to the :class:`Link`.
    """
    return create_link(uri, "client", **kwargs)


def create_server_link(uri: str, **kwargs) -> ServerLink:
    """Creates a server link with the given arguments based on the given URI.

    Args:
        uri: The URI to find and create a :class:`Link` for.
        **kwargs: Arguments to be passed to the :class:`Link`.
    """
    return create_link(uri, "server", **kwargs)


def create_link(uri: str, type: Literal["client", "server"] = "client", **kwargs) -> Link:
    """Creates a link with the given arguments based on the given URI.

    Args:
        uri: The URI to find and create a :class:`Link` for.
        type: The type of link to create, either "client" or "server".
        **kwargs: Arguments to be passed to the :class:`Link`.
    """
    link_name, link_layers, kwargs = _parse_link_uri(uri, **kwargs)
    link = _load_link(link_name, type)(**kwargs)

    for layer in link_layers:
        link = _load_link(layer, type)(uplink=link, **kwargs)

    return link


def _parse_link_uri(uri: str, **kwargs) -> tuple[str, list[str], dict[str, Any]]:
    """Utility function to parse URI and kwargs into usable :class:`Link` arguments.

    Examples:

        tcp://127.0.0.1:1337 -> ('tcp',  [], {'address': '127.0.0.1', 'port': 1337})
        unix://path/to/socket -> ('unix', [], {'address': 'path/to/socket'})
        tcp+tls://127.0.0.1:1337 ->  ('tcp', ['tls'], {'address': '127.0.0.1', 'port': 1337})

    Args:
        uri: The URI to parse.
        **kwargs: Additional arguments to be passed to the :class:`Link`.

    Returns:
        A tuple of link name, list of link layers, and kwargs.
    """
    parsed = urlparse(uri)

    # link:// or link
    link_def = parsed.scheme or parsed.path

    if "address" not in kwargs:
        address_def = ""

        if parsed.netloc:
            # link://address
            address_def += parsed.netloc

        if parsed.scheme and parsed.path:
            # link:///path/to/address
            address_def += parsed.path

        address, _, port = address_def.partition(":")
        if address:
            kwargs["address"] = address
        if port and "port" not in kwargs:
            kwargs["port"] = int(port)

    if parsed.query:
        kwargs.update(dict(parse_qsl(parsed.query)))

    link_name, _, link_layers = link_def.partition("+")
    link_layers = link_layers.split("+") if link_layers else []

    return link_name, link_layers, kwargs


def _load_link(link_name: str, link_type: str) -> type[Link]:
    """Load a specific :class:`Link` class for a given link implementation.

    Args:
        link_name: The name of the link implementation, e.g. "tcp", "tls", "pipe".
        link_type: The type of link, either "client" or "server".
    """
    mod_name = f"flow.transport.links.{link_name}"
    cls_name = f"{link_name.title()}{link_type.title()}Link"

    try:
        mod = importlib.import_module(mod_name)
        cls = getattr(mod, cls_name)
    except ImportError:
        raise LinkError(f"Unknown link module {link_name}, expected {mod_name}")
    except (AttributeError, KeyError):
        raise LinkError(f"Unknown link type {link_type} for module {link_name}, expected {cls_name}")

    return cls
