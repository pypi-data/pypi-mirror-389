from __future__ import annotations

import asyncio
import struct
from unittest.mock import Mock

import pytest

from flow.transport.base import ClientLink, FlowPacketProtocol, FlowProtocol, ReconnectMixin, ServerLink
from flow.transport.exception import ProtocolError

DEFAULT_TIMEOUT = 3


async def stream_test(server_link: ServerLink, client_link: ClientLink, timeout: int = DEFAULT_TIMEOUT) -> bool:
    return await asyncio.wait_for(_test_stream(server_link, client_link), timeout)


async def protocol_test(server_link: ServerLink, client_link: ClientLink, timeout: int = DEFAULT_TIMEOUT) -> bool:
    return await asyncio.wait_for(_test_protocol(server_link, client_link), timeout)


async def protocol_packet_test(
    server_link: ServerLink, client_link: ClientLink, timeout: int = DEFAULT_TIMEOUT
) -> bool:
    return await asyncio.wait_for(_test_protocol_packet(server_link, client_link), timeout)


async def protocol_reconnect_test(
    server_link: ServerLink, client_link: ClientLink, timeout: int = DEFAULT_TIMEOUT
) -> bool:
    return await asyncio.wait_for(_test_protocol_reconnect(server_link, client_link), timeout)


TEST_PARAMS = [
    pytest.param(stream_test, id="stream"),
    pytest.param(protocol_test, id="protocol"),
    pytest.param(protocol_packet_test, id="protocol-packet"),
    pytest.param(protocol_reconnect_test, id="protocol-reconnect"),
]


async def _test_stream(server_link: ServerLink, client_link: ClientLink) -> bool:
    """Stream echo server/client test. Server upper-cases data."""

    async def server_cb(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        data = await reader.read(4)
        writer.write(data.upper())
        await writer.drain()

    server = await server_link.serve_stream(server_cb)
    client_reader, client_writer = await client_link.connect_stream()

    client_writer.write(b"test")
    await client_writer.drain()
    client_data = await client_reader.read(4)
    assert client_data == b"TEST"

    client_writer.close()
    server.close()

    return True


async def _test_protocol(server_link: ServerLink, client_link: ClientLink) -> bool:
    """Protocol-based echo server/client test. Server reverses data."""

    class ServerProtocol(FlowProtocol):
        def __init__(self, future: asyncio.Future):
            super().__init__()
            self.future = future

        def on_data(self, data: bytes) -> None:
            # When data is received, set the future result and send back the reversed data
            self.future.set_result(data)
            self.send(data[::-1])

    class ClientProtocol(FlowProtocol):
        def __init__(self, future: asyncio.Future):
            super().__init__()
            self.future = future

        def on_data(self, data: bytes) -> None:
            # When data is received, set the future result
            self.future.set_result(data)

    loop = asyncio.get_running_loop()

    # The protocols will set these futures when they receive data
    server_future = loop.create_future()
    client_future = loop.create_future()

    server = await server_link.serve(lambda: ServerProtocol(server_future))
    client = await client_link.connect(lambda: ClientProtocol(client_future))
    await asyncio.sleep(0.01)  # Give server time to fully initialize

    client.send(b"some data")

    # Check that the server received the data and the client received the reversed data
    assert await server_future == b"some data"
    assert await client_future == b"atad emos"

    client.close()
    server.close()

    return True


async def _test_protocol_packet(server_link: ServerLink, client_link: ClientLink) -> bool:
    """Protocol-based echo server/client test with fragmented packets. Server reverses data."""

    class ServerProtocol(FlowPacketProtocol):
        def __init__(self, future: asyncio.Future):
            super().__init__()
            self.future = future
            self.received = []

        def on_data(self, data: bytes) -> None:
            self.received.append(data)
            self.send(data[::-1])

        def on_close(self, exc: Exception | None) -> None:
            self.future.set_result((self.received, exc))

    class ClientProtocol(FlowPacketProtocol):
        def __init__(self, future: asyncio.Future):
            super().__init__()
            self.future = future
            self.received = []

        def on_data(self, data: bytes) -> None:
            self.received.append(data)

        def on_close(self, exc: Exception | None) -> None:
            self.future.set_result((self.received, exc))

    loop = asyncio.get_running_loop()

    # The protocols will set these futures when they receive data
    server_future = loop.create_future()
    client_future = loop.create_future()

    server_protocol = ServerProtocol(server_future)
    server_protocol.data_received = Mock(wraps=server_protocol.data_received)

    count = 5
    server = await server_link.serve(lambda: server_protocol)
    client = await client_link.connect(lambda: ClientProtocol(client_future))
    await asyncio.sleep(0.01)  # Give server time to fully initialize

    # Simulate fragmented writes
    for _ in range(5):
        data = b"some data"
        buf = struct.pack(">I", len(data)) + data[:2]
        client.transport.write(buf)
        await asyncio.sleep(0.05)

        server_protocol.data_received.assert_called_with(buf)

        client.transport.write(data[2:])
        await asyncio.sleep(0.05)

    # Simulate a write that is too large
    assert not client._closed
    client.transport.write(struct.pack(">I", 1024 * 1024 * 1024))

    # Check the server received data
    server_received, server_exc = await server_future
    assert server_received == [b"some data"] * count
    assert isinstance(server_exc, ProtocolError)
    assert str(server_exc) == "Packet size (1073741824) exceeds maximum size (104857600)"

    # Check the client received data
    client_received, client_exc = await client_future
    assert client_received == [b"atad emos"] * count
    assert client_exc is None

    server.close()
    client.close()

    return True


async def _test_protocol_reconnect(server_link: ServerLink, client_link: ClientLink) -> bool:
    """Protocol-based echo server/client reconnect test. Server reverses data."""

    class ServerProtocol(FlowProtocol):
        def on_data(self, data: bytes) -> None:
            self.send(data[::-1])

    class ClientProtocol(ReconnectMixin, FlowProtocol):
        def __init__(self):
            super().__init__(reconnect_interval=0.1)
            self.received = []
            self.connect_count = 0

        def on_data(self, data: bytes) -> None:
            self.received.append(data)

        def on_connect(self, transport: asyncio.Transport) -> None:
            super().on_connect(transport)
            self.connect_count += 1

    server_protocol: ServerProtocol = None

    async def server_factory() -> asyncio.Server:
        nonlocal server_protocol
        server_protocol = ServerProtocol()
        return await server_link.serve(lambda: server_protocol)

    server = await server_factory()
    client = await client_link.connect(lambda: ClientProtocol())
    await asyncio.sleep(0.1)  # Give server time to fully initialize

    assert client.connect_count == 1
    client.send(b"first")
    await asyncio.sleep(0.1)
    assert client.received == [b"tsrif"]

    server.close()
    server_protocol.transport.close()
    await asyncio.sleep(0.1)
    server = await server_factory()
    await asyncio.sleep(1)

    assert client.connect_count == 2, "First reconnect failed"
    client.send(b"second")
    await asyncio.sleep(0.2)
    assert client.received == [b"tsrif", b"dnoces"]

    server.close()
    server_protocol.transport.close()
    await asyncio.sleep(0.15)
    server = await server_factory()
    await asyncio.sleep(1)

    assert client.connect_count == 3, "Second reconnect failed"
    client.send(b"third")
    await asyncio.sleep(0.2)
    assert client.received == [b"tsrif", b"dnoces", b"driht"]

    client.close()
    server.close()

    return True
