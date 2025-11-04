# SPDX-FileCopyrightText: 2023 CELESTIFYX Team
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import random
import select
import signal
import socket
import ssl
import struct
import time

from typing import (Self, Any)
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen
from ssl import SSLContext
from http.client import HTTPResponse

from nerve.lib.exceptions import DownloadTimeout
from nerve.lib.output import debug

class DownloadTimer:
    """
    Context manager for timing downloads with timeouts.
    """
    def __init__(self, timeout: int = 5) -> None:
        self.time: float | None = None
        self.start_time: float | None = None
        self.timeout = timeout
        self.previous_handler = None
        self.previous_timer: int | None = None

    def raise_timeout(self, *_: Any) -> None:
        """
        Raise the DownloadTimeout exception.
        """
        raise DownloadTimeout('Download timed out after ' + str(self.timeout) + ' second(s).')

    def __enter__(self) -> Self:
        if self.timeout > 0:
            self.previous_handler = signal.signal(signal.SIGALRM, self.raise_timeout)  # type: ignore[assignment]
            self.previous_timer   = signal.alarm(self.timeout)

        self.start_time = time.time()
        return self

    def __exit__(self, *_: Any) -> None:
        if self.start_time:
            time_delta: float = time.time() - self.start_time

            signal.alarm(0)
            self.time = time_delta

            if self.timeout > 0:
                signal.signal(signal.SIGALRM, self.previous_handler)
                previous_timer: int | None = self.previous_timer

                if previous_timer and (previous_timer > 0):
                    remaining_time: int = int(previous_timer - time_delta)

                    # The alarm should have been raised during the download.
                    signal.raise_signal(signal.SIGALRM) if remaining_time <= 0 else signal.alarm(remaining_time)

        self.start_time = None

def get_hw_addr(ifname: str) -> str:
    import fcntl

    s: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ret: bytes = fcntl.ioctl(s.fileno(), 0x8927, struct.pack('256s', bytes(ifname, 'utf-8')[:15]))

    return ':'.join('{:02x}'.format(b) for b in ret[18:24])

def list_interfaces(skip_loopback: bool = True) -> dict[str, str]:
    interfaces: dict[str, str] = {}

    for (_, iface) in socket.if_nameindex():
        if skip_loopback and (iface == "lo"):
            continue

        mac: str = get_hw_addr(iface).replace(':', '-').lower()
        interfaces[mac] = iface

    return interfaces

def enrich_iface_types(interfaces: list[str]) -> dict[str, str]:
    return {
        iface: 'BRIDGE' if os.path.isdir("/sys/class/net/" + iface + "/bridge/") else
        'TUN/TAP' if os.path.isfile("/sys/class/net/" + iface + "/tun_flags") else
        'WIRELESS' if os.path.isdir("/sys/class/net/" + iface + "/device") and os.path.isdir("/sys/class/net/" + iface + "/wireless/") else
        'PHYSICAL' if os.path.isdir("/sys/class/net/" + iface + "/device") else 'UNKNOWN' for iface in interfaces
    }

def fetch_data_from_url(url: str, params: dict[str, str] | None = None) -> str:
    ssl_context: SSLContext    = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode    = ssl.CERT_NONE

    try:
        response: HTTPResponse = urlopen(url=(url + '?' + urlencode(params)) if params else url, context=ssl_context)
        data: str = response.read().decode('UTF-8')

        return data
    except URLError as e:
        raise ValueError('Unable to fetch data from url: ' + url + '\n' + str(e))
    except Exception as e:
        raise ValueError('Unexpected error when parsing response: ' + str(e))

def calc_checksum(icmp_packet: bytes) -> int:
    # Calculate the ICMP checksum
    checksum: int = 0

    for i in range(0, len(icmp_packet), 2):
        checksum += (icmp_packet[i] << 8) + (struct.unpack('B', icmp_packet[i + 1:i + 2])[0] if len(icmp_packet[i + 1:i + 2]) else 0)

    checksum = (checksum >> 16) + (checksum & 0xFFFF)
    checksum = ~checksum & 0xFFFF

    return checksum

def build_icmp(payload: bytes) -> bytes:
    # Define the ICMP Echo Request packet
    icmp_packet: bytes = struct.pack('!BBHHH', 8, 0, 0, 0, 1) + payload
    checksum: int = calc_checksum(icmp_packet)

    return struct.pack('!BBHHH', 8, 0, checksum, 0, 1) + payload

def ping(hostname: str, timeout: int = 5) -> int:
    watchdog: select.epoll = select.epoll()
    started: float = time.time()
    random_identifier: bytes = ('nerve-' + str(random.randint(1000, 9999))).encode()

    # Create a raw socket (requires root, which should be fine on archiso)
    icmp_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    watchdog.register(icmp_socket, select.EPOLLIN | select.EPOLLHUP)

    icmp_packet: bytes = build_icmp(random_identifier)

    # Send the ICMP packet
    icmp_socket.sendto(icmp_packet, (hostname, 0))
    latency: int = -1

    # Gracefully wait for X amount of time
    # for an ICMP response or exit with no latency
    while (latency == -1) and ((time.time() - started) < timeout):
        try:
            for (_, _) in watchdog.poll(0.1):
                (response, _) = icmp_socket.recvfrom(1024)
                icmp_type: int = struct.unpack('!B', response[20:21])[0]

                # Check if it's an Echo Reply (ICMP type 0)
                if (icmp_type == 0) and (response[-len(random_identifier):] == random_identifier):
                    latency = round((time.time() - started) * 1000)
                    break

        except OSError as e:
            debug("Error: " + str(e))
            break

    icmp_socket.close()
    return latency
