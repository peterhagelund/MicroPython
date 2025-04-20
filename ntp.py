"""
Copyright (c) 2025 Peter Hagelund

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import socket
import struct


class Client:
    """
    Encapsulation of a Network Time Protocol (NTP) client.

    See: https://en.wikipedia.org/wiki/Network_Time_Protocol


    This implementation acts as a client, so `mode` is `3`, with a version number, `vn`,  of `3`.
    """

    _PACKET_FORMAT = '!bbbbIIIQQQQ'
    """The NTP version 3 packet format."""
    _EPOCH_DELTA = 2208988800
    """The pre-computed epoch delta, in seconds, between NTP (1/1/1900) and Unix/system (1/1/1970) epochs."""

    def __init__(self, host: str = '0.north-america.pool.ntp.org', port: int = 123, timeout: int = 5):
        """Initializes a new `NTP` instance.

        :param host: NTP host, defaults to '0.north-america.pool.ntp.org'.
        :type host: str, optional
        :param port: NTP port, defaults to `123`.
        :type port: int, optional
        :param timeout: timeout, in seconds, for receiving a time packet, defaults to `5`.
        :type timeout: int, optional
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.li = 0
        self.vn = 3
        self.mode = 3
        self.stratum = 0
        self.poll = 0
        self.precision = 0
        self.root_delay = 0
        self.root_dispersion = 0
        self.reference_id = 0
        self.reference_timestamp = 0
        self.origin_timestamp = 0
        self.receive_timestamp = 0
        self.transmit_timestamp = 0

    def query_time(self) -> int:
        """Queries the configured NTP server for the current time.

        The time that is returned is the NTP server's transmit time. This timestamp will be - at least - some milliseconds old.

        :raises OSError: If the NTP network request fails or times out.
        :raises ValueError: If the received response data is invalid.
        :return: The current time in seconds since the Unix epoch (1/1/1970).
        :rtype: int
        """
        dest_addr = socket.getaddrinfo(self.host, self.port, socket.AF_INET)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(self.timeout)
        data = self.pack_request()
        s.sendto(data, dest_addr)
        while True:
            data, src_addr = s.recvfrom(256)
            if src_addr == dest_addr:
                break
        s.close()
        self.unpack_response(data)
        return self.transmit_timestamp

    def pack_request(self, origin_timestamp: int = 0):
        """Packs the request.

        :param origin_timestamp: The origin timestamp, defaults to `0`.
        :type origin_timestamp: int, optional.
        :return: The 48-byte request data.
        :rtype: bytes
        """
        self.vn = 3
        self.mode = 3
        return struct.pack(
            Client._PACKET_FORMAT,
            ((self.vn & 0b00000111) << 3 | self.mode & 0b00000111),
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            (origin_timestamp + Client._EPOCH_DELTA) << 32,
            0,
            0,
        )

    def unpack_response(self, data: bytes):
        """Unpacks the response.

        The unpacked values are set on `self`.

        :param data: The 48-byte response data.
        :type data: bytes
        :raises ValueError: If the response data is invalid.
        """
        values = struct.unpack(Client._PACKET_FORMAT, data)
        self.li = (values[0] >> 6) & 0b00000011
        self.vn = (values[0] >> 3) & 0b00000111
        self.mode = values[0] & 0b00000111
        self.stratum = values[1]
        self.poll = values[2]
        self.precision = values[3]
        self.root_delay = values[4]
        self.root_dispersion = values[5]
        fields = (values[6] >> 24 & 0xFF, values[6] >> 16 & 0xFF, values[6] >> 8 & 0xFF, values[6] & 0xFF)
        if 0 <= self.stratum <= 1:
            self.reference_id = ("%c%c%c%c" % fields).rstrip('\0')
        elif 2 <= self.stratum <= 15:
            self.reference_id = "%d.%d.%d.%d" % fields
        else:
            self.reference_id = 'INVALID'
        self.reference_timestamp = (values[7] >> 32) - Client._EPOCH_DELTA
        self.origin_timestamp = (values[8] >> 32) - Client._EPOCH_DELTA
        self.receive_timestamp = (values[9] >> 32) - Client._EPOCH_DELTA
        self.transmit_timestamp = (values[10] >> 32) - Client._EPOCH_DELTA
