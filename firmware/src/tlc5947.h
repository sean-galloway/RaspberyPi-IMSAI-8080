#ifndef IMSPI_TLC5947_H
#define IMSPI_TLC5947_H
#include <stdint.h>

// Initialize GPIO, SPI/bit-bang lines, and the free-running GSCLK.
void tlc_init(void);

// Set one channel's 12-bit grayscale value in the local buffer (not yet shown).
void tlc_set(int channel, uint16_t gs);

// Set every channel to the same value (used by lamp test / blank).
void tlc_set_all(uint16_t gs);

// Shift the local buffer out to the chain and pulse XLAT to latch it.
void tlc_show(void);

#endif // IMSPI_TLC5947_H
