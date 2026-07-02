#include "hc165.h"
#include "config.h"
#include "pico/stdlib.h"
#include "hardware/gpio.h"

void hc165_init(void) {
    gpio_init(PIN_HC_PLOAD); gpio_set_dir(PIN_HC_PLOAD, GPIO_OUT);
    gpio_init(PIN_HC_CLK);   gpio_set_dir(PIN_HC_CLK, GPIO_OUT);
    gpio_init(PIN_HC_DATA);  gpio_set_dir(PIN_HC_DATA, GPIO_IN);
    gpio_put(PIN_HC_PLOAD, 1);   // idle: not loading
    gpio_put(PIN_HC_CLK, 0);
}

uint16_t hc165_read(void) {
    // Parallel load: pulse SH/LD low to capture the inputs.
    gpio_put(PIN_HC_PLOAD, 0);
    sleep_us(1);
    gpio_put(PIN_HC_PLOAD, 1);
    sleep_us(1);

    uint16_t raw = 0;
    // The last device's QH presents first; shift MSB-first across the chain.
    for (int i = 0; i < HC165_BITS; i++) {
        raw <<= 1;
        if (gpio_get(PIN_HC_DATA)) raw |= 1;
        gpio_put(PIN_HC_CLK, 1);
        gpio_put(PIN_HC_CLK, 0);
    }

    if (HC165_REVERSE_BITS) {
        uint16_t r = 0;
        for (int i = 0; i < HC165_BITS; i++)
            if (raw & (1u << i)) r |= (1u << (HC165_BITS - 1 - i));
        raw = r;
    }
    return raw;
}
