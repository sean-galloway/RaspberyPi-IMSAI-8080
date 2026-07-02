"""Frame encode/decode for the IMSPI 8080 serial protocol.

Mirrors docs/protocol.md and the firmware in firmware/src/protocol.c.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional

from .crc8 import crc8

# Start-of-frame markers
SOF_HOST_TO_PANEL = 0xA5
SOF_PANEL_TO_HOST = 0x5A

# Host -> panel commands
CMD_LED = 0x01
CMD_LAMP_TEST = 0x02
CMD_BRIGHTNESS = 0x03
CMD_PING = 0x7F

# Panel -> host responses
RSP_SWITCH = 0x81
RSP_VERSION = 0xC0

# Fixed frame lengths for panel -> host frames, keyed by command byte.
_P2H_LEN = {RSP_SWITCH: 6, RSP_VERSION: 5}

# Command-switch bit positions within SW_CMD / EVENTS (see docs/protocol.md).
CMD_RUN_STOP = 0
CMD_SINGLE_STEP = 1
CMD_EXAMINE = 2
CMD_DEPOSIT = 3


def _framed(payload: bytes) -> bytes:
    """Append a CRC over the whole payload and return the complete frame."""
    return payload + bytes([crc8(payload)])


def encode_led(addr: int, data: int, status: int = 0, bright: int = 255) -> bytes:
    """LED update frame. addr is the full 16-bit address bus."""
    addr &= 0xFFFF
    payload = bytes(
        [
            SOF_HOST_TO_PANEL,
            CMD_LED,
            (addr >> 8) & 0xFF,  # addr_hi
            addr & 0xFF,         # addr_lo
            data & 0xFF,
            status & 0xFF,
            bright & 0xFF,
        ]
    )
    return _framed(payload)


def encode_lamp_test(on: bool) -> bytes:
    return _framed(bytes([SOF_HOST_TO_PANEL, CMD_LAMP_TEST, 1 if on else 0]))


def encode_brightness(level: int) -> bytes:
    return _framed(bytes([SOF_HOST_TO_PANEL, CMD_BRIGHTNESS, level & 0xFF]))


def encode_ping() -> bytes:
    return _framed(bytes([SOF_HOST_TO_PANEL, CMD_PING]))


@dataclass(frozen=True)
class SwitchReport:
    """Decoded panel -> host switch report."""

    data: int      # 8 data toggle levels (bit i = toggle i)
    cmd: int       # 4 command switch levels, bits 0..3
    events: int    # latched rising edges on command switches since last report

    # Convenience accessors for the momentary command switches (edge events).
    @property
    def run_stop(self) -> bool:
        return bool(self.events & (1 << CMD_RUN_STOP))

    @property
    def single_step(self) -> bool:
        return bool(self.events & (1 << CMD_SINGLE_STEP))

    @property
    def examine(self) -> bool:
        return bool(self.events & (1 << CMD_EXAMINE))

    @property
    def deposit(self) -> bool:
        return bool(self.events & (1 << CMD_DEPOSIT))


@dataclass(frozen=True)
class VersionReport:
    major: int
    minor: int


class FrameParser:
    """Incremental parser for panel -> host frames.

    Feed raw bytes; yields SwitchReport / VersionReport as complete, CRC-valid
    frames arrive. Invalid CRCs and unknown commands resync at the next SOF.
    """

    def __init__(self) -> None:
        self._buf = bytearray()

    def feed(self, chunk: bytes) -> Iterator[object]:
        for b in chunk:
            yield from self._feed_byte(b)

    def _feed_byte(self, b: int) -> Iterator[object]:
        buf = self._buf
        if not buf:
            if b == SOF_PANEL_TO_HOST:
                buf.append(b)
            return

        buf.append(b)

        if len(buf) == 2 and buf[1] not in _P2H_LEN:
            # Unknown command: drop the SOF and resync.
            buf.clear()
            return

        if len(buf) >= 2:
            need = _P2H_LEN[buf[1]]
            if len(buf) >= need:
                frame = bytes(buf[:need])
                del buf[:need]
                result = self._decode(frame)
                if result is not None:
                    yield result

    @staticmethod
    def _decode(frame: bytes) -> Optional[object]:
        if crc8(frame[:-1]) != frame[-1]:
            return None
        cmd = frame[1]
        if cmd == RSP_SWITCH:
            return SwitchReport(data=frame[2], cmd=frame[3], events=frame[4])
        if cmd == RSP_VERSION:
            return VersionReport(major=frame[2], minor=frame[3])
        return None
