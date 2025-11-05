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
    sys.platform != "win32",
    reason="Pipe link is only available on win32",
)
@pytest.mark.parametrize(
    "test",
    TEST_PARAMS,
)
@pytest.mark.asyncio
async def test_pipe(test: Coroutine[None, None, bool]) -> None:
    """Test pipe client and server links."""
    uri = f"pipe://pipe-{random.randint(1000, 9999)}"
    server_link = ServerLink.create(uri)
    client_link = ClientLink.create(uri)
    assert await test(server_link, client_link)
