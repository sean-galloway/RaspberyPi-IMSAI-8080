"""CRC-8/SMBUS: poly 0x07, init 0x00, no reflection, no final xor.

Byte-for-byte identical to firmware/src/crc8.c.
"""


def crc8(data: bytes) -> int:
    crc = 0x00
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) & 0xFF if (crc & 0x80) else (crc << 1) & 0xFF
    return crc
