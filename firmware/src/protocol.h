#ifndef IMSPI_PROTOCOL_H
#define IMSPI_PROTOCOL_H
#include <stdint.h>
#include <stdbool.h>

// Decoded LED state written by a host CMD_LED frame.
typedef struct {
    uint8_t addr_hi;
    uint8_t addr_lo;
    uint8_t data;
    uint8_t status;
    uint8_t bright;
} led_state_t;

// Callbacks the parser invokes on a valid, CRC-checked frame.
typedef struct {
    void (*on_led)(const led_state_t *s);
    void (*on_lamp_test)(bool on);
    void (*on_brightness)(uint8_t level);
    void (*on_ping)(void);
} proto_handlers_t;

void proto_init(const proto_handlers_t *h);

// Feed one received byte from the host link.
void proto_feed(uint8_t byte);

// Build a switch report frame into out[6]. Returns bytes written (6).
int proto_build_switch(uint8_t *out, uint8_t sw_data, uint8_t sw_cmd, uint8_t events);

// Build a version reply into out[5]. Returns bytes written (5).
int proto_build_version(uint8_t *out);

#endif // IMSPI_PROTOCOL_H
