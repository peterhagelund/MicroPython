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

from time import sleep_ms

from machine import I2C


class SHT31:
    """Encapsulation of I2C SHT31 device."""

    def __init__(self, bus: I2C, address: int = 68, use_celcius: bool = False):
        """Initializes a new `SHT31` device.

        :param bus: The I2C bus to use.
        :type bus: I2C.
        :param address: The I2C address, defaults to `68`.
        :type address: int, optional.
        :param use_celcius: Boolean flag indicating whether or not to use Celcius, defaults to `False`.
        :type use_celcius: bool.
        """
        self.bus = bus
        self.address = address
        self.use_celcius = use_celcius

    def take_measurement(self) -> tuple[float, float]:
        """Takes a measurement.

        :raises ValueError: If there is a data or CRC error.
        :return: The temperature (in Fahrenheit, by default) and relative humidity.
        :rtype: tuple[float, float].
        """
        buf = bytes([0x2C, 0x06])
        self.bus.writeto(self.address, buf)
        sleep_ms(100)
        buf = self.bus.readfrom(self.address, 6)
        temp_crc = self.calc_crc(buf[0:2])
        if temp_crc != buf[2]:
            raise ValueError("temp CRC mismatch")
        humidity_crc = self.calc_crc(buf[3:5])
        if humidity_crc != buf[5]:
            raise ValueError("humidity CRC mismatch")
        if self.use_celcius:
            temp = (((buf[0] << 8) + buf[1]) * 175.0) / 65535.0 - 45.0
        else:
            temp = (((buf[0] << 8) + buf[1]) * 315.0) / 65535.0 - 49.0
        humidity = (((buf[3] << 8) + buf[4])) * 100.0 / 65535.0
        return (temp, humidity)

    def calc_crc(self, buf: bytes) -> int:
        """Calculates the CRC.

        :param buf: The buffer,
        :type buf: bytes
        :return: The CRC.
        :rtype: int.
        """
        crc = 0xFF
        for b in buf:
            crc = (crc ^ b) & 0xFF
            for _ in range(8):
                if crc & 0x80 != 0:
                    crc = ((crc << 1) & 0xFF) ^ 0x31
                else:
                    crc = (crc << 1) & 0xFF
        return crc
