"""IMSPI 8080 host driver."""

from .panel import Panel
from .protocol import (
    SwitchReport,
    FrameParser,
    encode_led,
    encode_lamp_test,
    encode_brightness,
    encode_ping,
)

__all__ = [
    "Panel",
    "SwitchReport",
    "FrameParser",
    "encode_led",
    "encode_lamp_test",
    "encode_brightness",
    "encode_ping",
]

__version__ = "0.1.0"
