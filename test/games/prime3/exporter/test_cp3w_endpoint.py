from __future__ import annotations

from ipaddress import IPv4Address

import pytest

from randovania.games.prime3.exporter.cp3w_endpoint import (
    CP3W_SERVER_ADDRESS_ERROR,
    CP3W_SERVER_PORT,
    IPv4InterfaceAddress,
    parse_cp3w_server_ipv4,
    preferred_cp3w_server_ipv4,
)


def test_cp3w_server_port_is_fixed() -> None:
    assert CP3W_SERVER_PORT == 43674


def test_preferred_cp3w_server_ipv4_prefers_default_route() -> None:
    assert preferred_cp3w_server_ipv4(
        default_route_ipv4=IPv4Address("192.168.50.248"),
        interface_addresses=(IPv4InterfaceAddress(IPv4Address("10.0.0.4"), True, True),),
    ) == IPv4Address("192.168.50.248")


def test_preferred_cp3w_server_ipv4_prefers_active_physical_private_address() -> None:
    assert preferred_cp3w_server_ipv4(
        interface_addresses=(
            IPv4InterfaceAddress(IPv4Address("10.0.0.4"), True, False),
            IPv4InterfaceAddress(IPv4Address("192.168.50.248"), True, True),
        )
    ) == IPv4Address("192.168.50.248")


def test_preferred_cp3w_server_ipv4_returns_none_without_usable_address() -> None:
    assert (
        preferred_cp3w_server_ipv4(
            interface_addresses=(
                IPv4InterfaceAddress(IPv4Address("127.0.0.1"), True, True),
                IPv4InterfaceAddress(IPv4Address("169.254.1.1"), True, True),
            )
        )
        is None
    )


@pytest.mark.parametrize(
    "value",
    ["", "hostname", "127.0.0.1", "0.0.0.0", "169.254.1.1", "224.0.0.1", "255.255.255.255"],
)
def test_parse_cp3w_server_ipv4_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError, match=CP3W_SERVER_ADDRESS_ERROR):
        parse_cp3w_server_ipv4(value)


def test_parse_cp3w_server_ipv4_accepts_numeric_address() -> None:
    assert parse_cp3w_server_ipv4("192.168.50.248") == IPv4Address("192.168.50.248")
