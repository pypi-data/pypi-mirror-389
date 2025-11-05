from __future__ import annotations

import asyncio
import platform
import random
import sys
from typing import TYPE_CHECKING

import pytest

from flow.transport.base import ClientLink, ServerLink

from ._util import TEST_PARAMS

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from pathlib import Path

    from flow.transport.links.tls import TlsServerLink


LINK_PARAMS = [
    pytest.param("tls://127.0.0.1", id="tls"),
    pytest.param("tcp+tls://127.0.0.1", id="tcp+tls"),
    pytest.param(
        "unix+tls://socket",
        id="unix+tls",
        marks=pytest.mark.skipif(sys.platform == "win32", reason="Unix link is not available on win32"),
    ),
    pytest.param(
        "pipe+tls://pipe",
        id="pipe+tls",
        marks=[
            pytest.mark.skipif(sys.platform != "win32", reason="Pipe link is only available on win32"),
            pytest.mark.skipif(
                platform.python_implementation() == "PyPy",
                reason="TLS over pipes suffers from a bug: https://github.com/pypy/pypy/issues/5335",
            ),
        ],
    ),
]


@pytest.mark.parametrize(
    "test",
    TEST_PARAMS,
)
@pytest.mark.parametrize(
    "uri",
    LINK_PARAMS,
)
@pytest.mark.asyncio
async def test_tls(
    test: Coroutine[None, None, bool],
    uri: str,
    unused_tcp_port: int,
    cafile: Path,
    server_certfile: Path,
    server_keyfile: Path,
    client_certfile: Path,
    client_keyfile: Path,
) -> None:
    """Test TLS client and server stream links."""
    if uri.startswith(("pipe", "unix")):
        # We can't use tmp_path here because the path might be too long for a socket, or the pipe may already exist
        num = random.randint(1000, 9999)
        uri += f"-{num}"

    server_link = ServerLink.create(
        uri,
        port=unused_tcp_port,
        cafile=cafile,
        certfile=server_certfile,
        keyfile=server_keyfile,
        verify=False,
    )
    client_link = ClientLink.create(
        uri,
        port=unused_tcp_port,
        cafile=cafile,
        certfile=client_certfile,
        keyfile=client_keyfile,
        verify=False,
    )
    assert await test(server_link, client_link)


@pytest.mark.asyncio
async def test_tls_sanity(unused_tcp_port: int, cafile: Path, server_certfile: Path, server_keyfile: Path) -> None:
    """Sanity test to ensure that we're actually speaking TLS."""
    server_link = ServerLink.create(
        "tls://127.0.0.1",
        port=unused_tcp_port,
        cafile=cafile,
        certfile=server_certfile,
        keyfile=server_keyfile,
    )
    assert await asyncio.wait_for(_tls_sanity(server_link), 3)


@pytest.mark.asyncio
async def test_tls_tcp_sanity(unused_tcp_port: int, cafile: Path, server_certfile: Path, server_keyfile: Path) -> None:
    """Sanity test to ensure that we're actually speaking TLS when using an uplink."""
    server_link = ServerLink.create(
        "tcp+tls://127.0.0.1",
        port=unused_tcp_port,
        cafile=cafile,
        certfile=server_certfile,
        keyfile=server_keyfile,
    )
    assert await asyncio.wait_for(_tls_sanity(server_link), 3)


async def _tls_sanity(server_link: TlsServerLink) -> None:
    async def server_cb(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        data = await reader.read(4)
        writer.write(data.upper())
        await writer.drain()

    server = await server_link.serve_stream(server_cb)

    client_link = ClientLink.create(f"tcp://{server_link.address}:{server_link.port}")
    client_reader, client_writer = await client_link.connect_stream()

    # Send a raw ClientHello over a plain TCP transport
    client_writer.write(
        bytes.fromhex(
            "16 03 01 00 a5 01 00 00 a1 03 03 00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e"
            "0f 10 11 12 13 14 15 16 17 18 19 1a 1b 1c 1d 1e 1f 00 00 20 cc a8 cc a9 c0 2f"
            "c0 30 c0 2b c0 2c c0 13 c0 09 c0 14 c0 0a 00 9c 00 9d 00 2f 00 35 c0 12 00 0a"
            "01 00 00 58 00 00 00 18 00 16 00 00 13 65 78 61 6d 70 6c 65 2e 75 6c 66 68 65"
            "69 6d 2e 6e 65 74 00 05 00 05 01 00 00 00 00 00 0a 00 0a 00 08 00 1d 00 17 00"
            "18 00 19 00 0b 00 02 01 00 00 0d 00 12 00 10 04 01 04 03 05 01 05 03 06 01 06"
            "03 02 01 02 03 ff 01 00 01 00 00 12 00 00"
        )
    )
    await client_writer.drain()

    # Expect some kind of TLS response (probably a ServerHello)
    assert await client_reader.read(4) == b"\x16\x03\x03\x00"

    server.close()
    client_writer.close()

    # Give some time for everything to close properly
    await asyncio.sleep(0.1)

    return True
