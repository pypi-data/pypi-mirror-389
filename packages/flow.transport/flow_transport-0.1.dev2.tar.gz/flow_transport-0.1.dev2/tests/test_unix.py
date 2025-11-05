from __future__ import annotations

import random
import sys
from typing import TYPE_CHECKING

import pytest

from flow.transport.base import ClientLink, ServerLink

from ._util import TEST_PARAMS

if TYPE_CHECKING:
    from collections.abc import Coroutine


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Unix link is not available on win32",
)
@pytest.mark.parametrize(
    "test",
    TEST_PARAMS,
)
@pytest.mark.asyncio
async def test_unix(test: Coroutine[None, None, bool]) -> None:
    """Test UNIX client and server links."""
    # We can't use tmp_path here because the path might be too long for a socket
    uri = f"unix:///tmp/flow-transport-socket-{random.randint(1000, 9999)}"
    server_link = ServerLink.create(uri)
    client_link = ClientLink.create(uri)
    assert await test(server_link, client_link)


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Unix link is not available on win32",
)
@pytest.mark.parametrize(
    "test",
    TEST_PARAMS,
)
@pytest.mark.asyncio
async def test_unix_abstract(test: Coroutine[None, None, bool]) -> None:
    """Test UNIX abstract client and server links."""
    # Should work with both @ and \0 prefixes
    uri = f"unix://@flow-transport-abstract-socket-{random.randint(1000, 9999)}"
    server_link = ServerLink.create(uri)
    client_link = ClientLink.create(uri)
    # assert await test(server_link, client_link)

    uri = f"unix://\0flow-transport-abstract-socket-{random.randint(1000, 9999)}"
    server_link = ServerLink.create(uri)
    client_link = ClientLink.create(uri)
    assert await test(server_link, client_link)
