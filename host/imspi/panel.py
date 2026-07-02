"""High-level Panel interface over a serial link to the RP2040."""

from __future__ import annotations

import time
from typing import Optional

import serial  # pyserial

from .protocol import (
    FrameParser,
    SwitchReport,
    VersionReport,
    encode_brightness,
    encode_lamp_test,
    encode_led,
    encode_ping,
)


class Panel:
    """Connect to an IMSPI 8080 panel.

    Example:
        with Panel("/dev/ttyACM0") as p:
            p.set_bus(addr=0x1234, data=0x76, status=0b0001)
            rep = p.poll(timeout=1.0)
    """

    def __init__(self, port: str, baud: int = 115200, timeout: float = 0.05) -> None:
        # Baud is nominal over USB CDC but pyserial requires a value.
        self._ser = serial.Serial(port, baud, timeout=timeout)
        self._parser = FrameParser()
        self._last_switch: Optional[SwitchReport] = None

    # --- lifecycle ---------------------------------------------------------
    def close(self) -> None:
        self._ser.close()

    def __enter__(self) -> "Panel":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # --- writes ------------------------------------------------------------
    def set_bus(self, addr: int, data: int, status: int = 0, bright: int = 255) -> None:
        """Write the full lamp state: 16-bit address, 8-bit data, status nibble."""
        self._ser.write(encode_led(addr, data, status, bright))

    def set_brightness(self, level: int) -> None:
        self._ser.write(encode_brightness(level))

    def lamp_test(self, on: bool) -> None:
        self._ser.write(encode_lamp_test(on))

    # --- reads -------------------------------------------------------------
    def _pump(self) -> None:
        """Read whatever is waiting and update state from any complete frames."""
        n = self._ser.in_waiting
        chunk = self._ser.read(n if n else 1)
        if not chunk:
            return
        for frame in self._parser.feed(chunk):
            if isinstance(frame, SwitchReport):
                self._last_switch = frame

    def poll(self, timeout: float = 0.0) -> Optional[SwitchReport]:
        """Return the most recent SwitchReport seen within `timeout` seconds.

        With timeout=0 this does a single non-blocking pump and returns the last
        known report (or None if none seen yet).
        """
        deadline = time.monotonic() + timeout
        self._pump()
        while timeout > 0 and time.monotonic() < deadline:
            self._pump()
            time.sleep(0.005)
        return self._last_switch

    def ping(self, timeout: float = 1.0) -> Optional[tuple]:
        """Send a ping and return (major, minor) version, or None on timeout."""
        self._ser.write(encode_ping())
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            chunk = self._ser.read(self._ser.in_waiting or 1)
            for frame in self._parser.feed(chunk):
                if isinstance(frame, VersionReport):
                    return (frame.major, frame.minor)
            time.sleep(0.005)
        return None
