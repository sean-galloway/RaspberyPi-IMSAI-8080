#ifndef IMSPI_CRC8_H
#define IMSPI_CRC8_H
#include <stddef.h>
#include <stdint.h>

// CRC-8/SMBUS: poly 0x07, init 0x00, no reflection, no final xor.
// Must match host/imspi/crc8.py byte-for-byte.
uint8_t crc8(const uint8_t *data, size_t len);

#endif // IMSPI_CRC8_H
