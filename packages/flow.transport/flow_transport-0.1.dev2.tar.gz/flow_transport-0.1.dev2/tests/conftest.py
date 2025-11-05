from __future__ import annotations

from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent / "_data"

pytest.register_assert_rewrite("tests._util")


@pytest.fixture
def cafile() -> Path:
    return DATA_DIR / "ca.crt"


@pytest.fixture
def server_certfile() -> Path:
    return DATA_DIR / "server.crt"


@pytest.fixture
def server_keyfile() -> Path:
    return DATA_DIR / "server.key"


@pytest.fixture
def client_certfile() -> Path:
    return DATA_DIR / "client.crt"


@pytest.fixture
def client_keyfile() -> Path:
    return DATA_DIR / "client.key"
