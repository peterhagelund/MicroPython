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

INSTR_CLEAR_DISPLAY = 0x01
INSTR_RETURN_HOME = 0x02
INSTR_ENTRY_MODE_SET = 0x04
INSTR_DISPLAY_CONTROL = 0x08
INSTR_CURSOR_OR_DISPLAY_SHIFT = 0x10
INSTR_FUNCTION_SET = 0x20
INSTR_SET_CGRAM_ADDRESS = 0x40
INSTR_SET_DDRAM_ADDRESS = 0x80


DIR_LEFT = 0x00
DIR_RIGHT = 0x02


SHIFT_NONE = 0x00
SHIFT_DIRECTION = 0x01


DISPLAY_OFF = 0x00
DISPLAY_ON = 0x04
CURSOR_OFF = 0x00
CURSOR_ON = 0x02
BLINK_OFF = 0x00
BLINK_ON = 0x01


MOVE_RIGHT = 0x04
MOVE_LEFT = 0x00
MOVE_CURSOR = 0x00
MOVE_DISPLAY = 0x08


MODE_4BIT = 0x00
MODE_8BIT = 0x10
MODE_1LINE = 0x00
MODE_2LINE = 0x08
MODE_8DOTS = 0x00
MODE_11DOTS = 0x04


class LCD1602:
    """Encapsulation of I2C LCD1602 device."""

    def __init__(self, bus: I2C, address: int = 62, cursor_on: bool = False, blink_on=False):
        """Initializes a new `LCD1602` instance.

        :param bus: The I2C bus to use.
        :type bus: I2C
        :param address: I2C device address, defaults to `62`.
        :type address: int, optional
        :param cursor_on: Boolean flag indicating whether or not the cursor should be on, defaults to False.
        :type cursor_on: bool, optional
        :param blink_on: Boolean flag indicating whether or not the cursor (if on) should blink., defaults to False.
        :type blink_on: bool, optional
        """
        self.bus = bus
        self.address = address
        for _ in range(4):
            self.function_set()
            sleep_ms(5)
        self.display_control(cursor_on=cursor_on, blink_on=blink_on)
        self.entry_mode_set()

    def write_to_ir(self, instr: int):
        """Write to Instruction Register (IR).

        Sends the specified command to the Instruction Register (IR) at address `0x80`.

        :param instr: The instruction.
        :type instr: int
        """
        self.bus.writeto_mem(self.address, 0x80, chr(instr))

    def write_to_dr(self, data: int):
        """Write to Data Register (DR).

        Sends the specified command to the Data Register (DR) at address `0x40`.

        :param data: The data.
        :type data: int
        """
        self.bus.writeto_mem(self.address, 0x40, chr(data))

    def clear_display(self):
        """Clears the display."""
        self.write_to_ir(INSTR_CLEAR_DISPLAY)
        sleep_ms(2)

    def return_home(self):
        """Return Home

        Moves the cursor to its home location `(0, 0)`.
        """
        self.write_to_ir(INSTR_RETURN_HOME)
        sleep_ms(2)

    def entry_mode_set(self, increment: bool = True, shift: bool = False):
        """Entry Mode Set.

        :param increment: Boolean flag indicating whether or not direction is to increment, defaults to True.
        :type increment: bool, optional.
        :param shift: Boolean flag indicating whether or not to shift, defaults to False.
        :type shift: bool, optional.
        """
        instr = INSTR_ENTRY_MODE_SET
        if increment:
            instr |= DIR_RIGHT
        else:
            instr |= DIR_LEFT
        if shift:
            instr |= SHIFT_DIRECTION
        else:
            instr |= SHIFT_NONE
        self.write_to_ir(instr)

    def display_control(self, display_on=True, cursor_on=True, blink_on=True):
        """Display Control.

        :param display_on: Boolean flag indicating whether or not the display should be on, defaults to True.
        :type display_on: bool, optional.
        :param cursor_on: Boolean flag indicating whether or not the cursor should be on, defaults to True.
        :type cursor_on: bool, optional.
        :param blink_on: Boolean flag indicating whether or not the cursor (if on) should blink, defaults to True.
        :type blink_on: bool, optional.
        """
        instr = INSTR_DISPLAY_CONTROL
        if display_on:
            instr |= DISPLAY_ON
        else:
            instr |= DISPLAY_OFF
        if cursor_on:
            instr |= CURSOR_ON
        else:
            instr |= CURSOR_OFF
        if blink_on:
            instr |= BLINK_ON
        else:
            instr |= BLINK_OFF
        self.write_to_ir(instr)

    def cursor_or_display_shift(self, move_display: bool = False, move_right: bool = False):
        """Cursor or Display Shift.

        :param move_display: Boolean flag indicating whether or not the display should move, defaults to False.
        :type move_display: bool, optional.
        :param move_right: Boolean flag indicating whether or not to move right, defaults to False.
        :type move_right: bool, optional.
        """
        cmd = INSTR_CURSOR_OR_DISPLAY_SHIFT
        if move_display:
            cmd |= MOVE_DISPLAY
        else:
            cmd |= MOVE_CURSOR
        if move_right:
            cmd |= MOVE_RIGHT
        else:
            cmd |= MOVE_LEFT
        self.write_to_ir(cmd)

    def function_set(self, mode_8bit: bool = False, two_lines: bool = True, mode_11dots: bool = False):
        """Function Set.

        :param mode_8bit: Boolean flag indicating whether or not to use 8-bit mode, defaults to False.
        :type mode_8bit: bool, optional.
        :param two_lines: Boolean flag indicating whether or not to use two lines for the display, defaults to True.
        :type two_lines: bool, optional.
        :param mode_11dots: Boolean flag indicating whether or not to use 11-dot mode, defaults to False.
        :type mode_11dots: bool, optional.
        """
        instr = INSTR_FUNCTION_SET
        if mode_8bit:
            instr |= MODE_8BIT
        else:
            instr |= MODE_4BIT
        if two_lines:
            instr |= MODE_2LINE
        else:
            instr |= MODE_1LINE
        if mode_11dots:
            instr |= MODE_11DOTS
        else:
            instr |= MODE_8DOTS
        self.write_to_ir(instr)

    def set_cgram_address(self, address: int):
        """Set CGRAM in address counter (AC).

        :param address: The address.
        :type address: int
        """
        instr = INSTR_SET_CGRAM_ADDRESS | (address & 0b00111111)
        self.write_to_ir(instr)

    def set_ddram_address(self, address: int):
        """Set DDRAM in address counter (AC).

        :param address: The address.
        :type address: int
        """
        instr = INSTR_SET_DDRAM_ADDRESS | (address & 0b01111111)
        self.write_to_ir(instr)

    def move_cursor(self, col: int, row: int):
        """Moves the cursor.

        :param col: The column.
        :type col: int
        :param row: The row (`0` or `1`).
        :type row: int
        """
        if row == 0:
            col |= 0x80
        else:
            col |= 0xC0
        self.bus.writeto(self.address, bytearray([0x80, col]))

    def write(self, s: str):
        """Writes a string to the display.

        The string will be decoded using `UTF-8`.

        :param s: The string.
        :type s: str
        """
        for x in bytearray(s, "utf-8"):
            self.write_to_dr(x)
