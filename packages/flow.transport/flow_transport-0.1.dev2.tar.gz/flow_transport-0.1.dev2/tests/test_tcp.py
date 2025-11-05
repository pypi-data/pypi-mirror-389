from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flow.transport.base import ClientLink, ServerLink

from ._util import TEST_PARAMS

if TYPE_CHECKING:
    from collections.abc import Coroutine


@pytest.mark.parametrize(
    "test",
    TEST_PARAMS,
)
@pytest.mark.asyncio
async def test_tcp(test: Coroutine[None, None, bool], unused_tcp_port: int) -> None:
    """Test TCP client and server links."""
    uri = "tcp://127.0.0.1"
    server_link = ServerLink.create(uri, port=unused_tcp_port)
    client_link = ClientLink.create(uri, port=unused_tcp_port)
    assert await test(server_link, client_link)
