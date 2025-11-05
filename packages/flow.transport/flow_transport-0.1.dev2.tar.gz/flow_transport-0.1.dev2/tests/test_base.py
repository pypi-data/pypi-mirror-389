from typing import Any

import pytest

from flow.transport import base
from flow.transport.exception import LinkError
from flow.transport.links import tcp, tls


@pytest.mark.parametrize(
    ("uri", "kwargs", "expected"),
    [
        (
            "tcp",
            {},
            ("tcp", [], {}),
        ),
        (
            "tcp://",
            {},
            ("tcp", [], {}),
        ),
        (
            "tcp://127.0.0.1",
            {},
            ("tcp", [], {"address": "127.0.0.1"}),
        ),
        (
            "tcp://127.0.0.1:1337",
            {},
            ("tcp", [], {"address": "127.0.0.1", "port": 1337}),
        ),
        (
            "tcp://127.0.0.1",
            {"port": 1337},
            ("tcp", [], {"address": "127.0.0.1", "port": 1337}),
        ),
        (
            "tcp://",
            {"address": "127.0.0.1", "port": 1337},
            ("tcp", [], {"address": "127.0.0.1", "port": 1337}),
        ),
        (
            "tcp://127.0.0.1:1337?asdf=value",
            {},
            ("tcp", [], {"address": "127.0.0.1", "port": 1337, "asdf": "value"}),
        ),
        (
            "unix://test",
            {},
            ("unix", [], {"address": "test"}),
        ),
        (
            "unix:///path/to/test",
            {},
            ("unix", [], {"address": "/path/to/test"}),
        ),
        (
            "tcp+tls",
            {},
            ("tcp", ["tls"], {}),
        ),
        (
            "tcp+tls://",
            {},
            ("tcp", ["tls"], {}),
        ),
        (
            "tcp+tls://127.0.0.1",
            {},
            ("tcp", ["tls"], {"address": "127.0.0.1"}),
        ),
        (
            "tcp+tls://127.0.0.1:1337",
            {},
            ("tcp", ["tls"], {"address": "127.0.0.1", "port": 1337}),
        ),
        (
            "tcp+tls+xor://127.0.0.1:1337",
            {},
            ("tcp", ["tls", "xor"], {"address": "127.0.0.1", "port": 1337}),
        ),
    ],
)
def test_parse_uri(uri: str, kwargs: dict, expected: tuple[str, str, list[str], dict[str, Any]]) -> None:
    """Test various link URI parsing scenarios."""
    assert base._parse_link_uri(uri, **kwargs) == expected


def test_load_link() -> None:
    """Test loading link implementations."""
    assert base._load_link("tcp", "client") == tcp.TcpClientLink
    assert base._load_link("tcp", "server") == tcp.TcpServerLink

    with pytest.raises(LinkError):
        base._load_link("tcp", "nope")

    with pytest.raises(LinkError):
        base._load_link("nope", "client")


def test_create_link() -> None:
    """Test creating link instances from URIs."""
    link = base.create_link("tcp://127.0.0.1:1337")

    assert isinstance(link, tcp.TcpClientLink)
    assert link.address == "127.0.0.1"
    assert link.port == 1337


def test_create_link_layers() -> None:
    """Test creating link instances with layers from URIs."""
    link = base.create_link("tcp+tls://127.0.0.1:1337?cafile=ca.pem&certfile=crt.pem&keyfile=key.pem")

    assert isinstance(link, tls.TlsClientLink)
    assert isinstance(link.uplink, tcp.TcpClientLink)
