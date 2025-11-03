from __future__ import annotations

import ipaddress

import pytest

from ipaddons import IPv4Allocation, IPv6Allocation, ip_allocation, tools

v4_supernet_string = "10.0.0.0/8"
v4_supernet = ipaddress.IPv4Network(v4_supernet_string)

v4_subnet_strings = [
    "10.0.0.0/16",
    "10.1.1.0/24",
    "10.1.1.16/29",
    "10.1.2.0/25",
    "10.1.2.0/24",
    "10.1.3.0/25",
    "10.1.3.64/26",
    "10.1.3.128/26",
]
v4_subnets = [ipaddress.IPv4Network(n) for n in v4_subnet_strings]
v4_subnet_ranges = [(int(n[0]), int(n[-1])) for n in v4_subnets]

v6_supernet_string = "fc00::/32"
v6_supernet = ipaddress.IPv6Network(v6_supernet_string)


v6_subnet_strings = [
    "fc00::/48",
    "fc00:a::/56",
    "fc00:b::/56",
    "fc00:b:0:100::/56",
    "fc00:b:0:200::/64",
    "fc00:b:0:100::/56",
    "fc00:c::/44",
]
v6_subnets = [ipaddress.IPv6Network(n) for n in v6_subnet_strings]
v6_subnet_ranges = [(int(n[0]), int(n[-1])) for n in v6_subnets]

mergeable_subnets = [
    [
        (int(ipaddress.IPv4Network(n)[0]), int(ipaddress.IPv4Network(n)[-1]))
        for n in ["192.168.0.0/24", "192.168.0.0/25", "192.168.0.128/25", "192.168.0.64/29"]
    ],
    [
        (int(ipaddress.IPv6Network(n)[0]), int(ipaddress.IPv6Network(n)[-1]))
        for n in ["fc01::/32", "fc01::/64", "fc01:0:ffff::/48", "fc01:0:cafe::/64"]
    ],
]


@pytest.mark.parametrize(
    ("supernet", "subnets", "allocation_class", "network_class"),
    [
        (v4_supernet, v4_subnets, IPv4Allocation, ipaddress.IPv4Network),
        (v4_supernet_string, v4_subnet_strings, IPv4Allocation, ipaddress.IPv4Network),
        (v6_supernet, v6_subnets, IPv6Allocation, ipaddress.IPv6Network),
        (v6_supernet_string, v6_subnet_strings, IPv6Allocation, ipaddress.IPv6Network),
    ],
)
def test_allocation_classes(supernet, subnets, allocation_class, network_class):
    a = ip_allocation(supernet, used_networks=subnets)
    assert isinstance(a, allocation_class)
    assert all(isinstance(n, network_class) for n in a.used_subnets)


@pytest.mark.parametrize(
    ("subnet", "subnet_range"),
    zip(v4_subnets + v6_subnets, v4_subnet_ranges + v6_subnet_ranges, strict=True),
)
def test_netrange(subnet, subnet_range):
    assert tools.netrange(subnet) == subnet_range


@pytest.mark.parametrize(
    ("supernet", "subnets", "subnet_ranges"),
    [
        (v4_supernet, v4_subnets, v4_subnet_ranges),
        (v6_supernet, v6_subnets, v6_subnet_ranges),
    ],
)
def test_allocation_ranges(supernet, subnets, subnet_ranges):
    a = ip_allocation(supernet, used_networks=subnets)
    a._update_used_subnet_ranges(merge=False)
    assert sorted(a._used_network_ranges) == sorted(subnet_ranges)


@pytest.mark.parametrize("subnets", mergeable_subnets)
def test_merge(subnets):
    covering_prefix = subnets[0]
    assert tools.merge_ranges(subnets) == [covering_prefix]
