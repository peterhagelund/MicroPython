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

from json import load
from time import localtime, sleep_ms, time

from machine import I2C, RTC, Pin
from network import WLAN

from lcd1602 import LCD1602
from ntp import Client
from sht31 import SHT31

with open('settings.json', 'r') as f:
    settings: dict[str, str | int] = load(f)

ssid: str = settings['wlan']['ssid']
key: str = settings['wlan']['key']
host: str = settings['ntp'].get('host', '0.north-america.pool.ntp.org')
port: int = settings['ntp'].get('port', 123)
interval: int = settings['ntp'].get('interval', 3600)
offset: int = settings['ntp'].get('offset', 0)
use_celcius: bool = settings['sht31'].get('unit', 'F') == 'C'
loops: int = settings['app'].get('loops', 100)
delay: int = settings['app'].get('delay', 5000)


blue = Pin(15, Pin.OUT)
green = Pin(14, Pin.OUT)
i2c0 = I2C(0, scl=Pin(17), sda=Pin(16), freq=100_000)
wlan = WLAN()
rtc = RTC()
ntp_time = 0
sht31 = SHT31(i2c0, use_celcius=use_celcius)
lcd1602 = LCD1602(i2c0)


def setup():
    """Performs initial setup."""
    blue.off()
    green.off()
    wlan.active(True)
    lcd1602.display_control(display_on=True, cursor_on=False, blink_on=False)
    lcd1602.clear_display()


def connect_to_wifi():
    """Connects to the configured Wi-Fi."""
    lcd1602.clear_display()
    lcd1602.return_home()
    lcd1602.write('Connecting...')
    wlan.connect(ssid, key)
    while not wlan.isconnected():
        sleep_ms(100)
    lcd1602.clear_display()
    lcd1602.return_home()
    lcd1602.write('Connected')
    sleep_ms(1000)
    lcd1602.clear_display()
    lcd1602.return_home()


def update_time():
    """Updates the time from the configured NTP server."""
    lcd1602.clear_display()
    lcd1602.return_home()
    lcd1602.write('Getting time...')
    client = Client(host=host, port=port)
    try:
        global ntp_time
        ntp_time = client.query_time() + offset * 3600
        lcd1602.clear_display()
        lcd1602.return_home()
        lcd1602.write('Got time')
        dt = localtime(ntp_time)
        rtc.datetime((dt[0], dt[1], dt[2], dt[6], dt[3], dt[4], dt[5], dt[7]))
    except Exception as e:
        lcd1602.clear_display()
        lcd1602.return_home()
        lcd1602.write('No time')
        lcd1602.move_cursor(0, 1)
        if isinstance(e, OSError):
            lcd1602.write('Timeout')
        else:
            lcd1602.write('Bad data')
    sleep_ms(1000)
    lcd1602.clear_display()
    lcd1602.return_home()


def run():
    """Runs the application."""
    green.on()
    show_dt = True
    for _ in range(loops):
        if not wlan.isconnected():
            connect_to_wifi()
        if ntp_time == 0 or time() - ntp_time > interval:
            update_time()
        lcd1602.clear_display()
        lcd1602.return_home()
        if show_dt is True:
            dt = rtc.datetime()
            lcd1602.write(f'D: {dt[0]:04}/{dt[1]:02}/{dt[2]:02}')
            lcd1602.move_cursor(0, 1)
            lcd1602.write(f'T: {dt[4]:02}:{dt[5]:02}:{dt[6]:02}')
        else:
            unit = 'C' if use_celcius else 'F'
            temp, humidity = sht31.take_measurement()
            lcd1602.write(f'T: {temp:.1f}{unit}')
            lcd1602.move_cursor(0, 1)
            lcd1602.write(f'H: {humidity:.1f}%')
        show_dt = not show_dt
        blue.toggle()
        green.toggle()
        sleep_ms(delay)


def teardown():
    """Tears down the various resources."""
    lcd1602.clear_display()
    lcd1602.display_control(display_on=False)
    blue.off()
    green.off()
    wlan.disconnect()
    wlan.active(False)


def main():
    """Application entry-point."""
    setup()
    run()
    teardown()


if __name__ == '__main__':
    main()
