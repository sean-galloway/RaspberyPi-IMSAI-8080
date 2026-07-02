#ifndef IMSPI_HC165_H
#define IMSPI_HC165_H
#include <stdint.h>

// Initialize the 74HC165 control pins.
void hc165_init(void);

// Latch + shift the whole chain, returning up to 16 switch bits.
// A set bit means the switch is closed (pulled to the active level).
uint16_t hc165_read(void);

#endif // IMSPI_HC165_H
