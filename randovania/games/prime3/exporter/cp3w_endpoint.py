from __future__ import annotations

import importlib
import ipaddress
import socket
from dataclasses import dataclass
from ipaddress import IPv4Address
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

CP3W_SERVER_PORT = 43674
CP3W_SERVER_ADDRESS_ERROR = "Enter the IPv4 address of the computer running the CP3W tracker server."


@dataclass(frozen=True)
class IPv4InterfaceAddress:
    address: IPv4Address
    is_up: bool
    is_physical: bool


def parse_cp3w_server_ipv4(value: str) -> IPv4Address:
    try:
        address = ipaddress.IPv4Address(value.strip())
    except ipaddress.AddressValueError as error:
        raise ValueError(CP3W_SERVER_ADDRESS_ERROR) from error
    if (
        address.is_loopback
        or address.is_unspecified
        or address.is_link_local
        or address.is_multicast
        or address == IPv4Address("255.255.255.255")
    ):
        raise ValueError(CP3W_SERVER_ADDRESS_ERROR)
    return address


def preferred_cp3w_server_ipv4(
    *,
    default_route_ipv4: IPv4Address | None = None,
    interface_addresses: Iterable[IPv4InterfaceAddress] = (),
) -> IPv4Address | None:
    if default_route_ipv4 is not None and default_route_ipv4.is_private and _is_usable_default(default_route_ipv4):
        return default_route_ipv4

    active = [
        candidate for candidate in interface_addresses if candidate.is_up and _is_usable_default(candidate.address)
    ]
    for candidate in active:
        if candidate.is_physical and candidate.address.is_private:
            return candidate.address
    for candidate in active:
        if candidate.address.is_private:
            return candidate.address
    return None


def discover_cp3w_server_ipv4() -> IPv4Address | None:
    return preferred_cp3w_server_ipv4(
        default_route_ipv4=_default_route_ipv4(),
        interface_addresses=_interface_ipv4_addresses(),
    )


def _default_route_ipv4() -> IPv4Address | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("8.8.8.8", 80))
            return IPv4Address(probe.getsockname()[0])
    except OSError:
        return None


def _interface_ipv4_addresses() -> tuple[IPv4InterfaceAddress, ...]:
    try:
        psutil = importlib.import_module("psutil")
    except ModuleNotFoundError:
        return ()

    stats = psutil.net_if_stats()
    result: list[IPv4InterfaceAddress] = []
    for name, addresses in psutil.net_if_addrs().items():
        status = stats.get(name)
        if status is None or not status.isup:
            continue
        lowered_name = name.lower()
        physical = not any(token in lowered_name for token in ("vpn", "tunnel", "virtual", "vbox", "vmware", "wsl"))
        for address in addresses:
            if address.family != socket.AF_INET:
                continue
            try:
                result.append(IPv4InterfaceAddress(IPv4Address(address.address), True, physical))
            except ipaddress.AddressValueError:
                continue
    return tuple(result)


def _is_usable_default(address: IPv4Address) -> bool:
    try:
        parse_cp3w_server_ipv4(str(address))
    except ValueError:
        return False
    return True
