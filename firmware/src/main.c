#include "config.h"
#include "crc8.h"
#include "tlc5947.h"
#include "hc165.h"
#include "protocol.h"

#include "pico/stdlib.h"
#include <stdio.h>
#include <string.h>

// --- lamp state ------------------------------------------------------------
static led_state_t g_led;        // last commanded lamp state
static bool g_lamp_test = false; // lamp-test override active

// Map a byte register onto 8 consecutive TLC channels, MSB (bit7) -> base+0.
// A set data bit lights that lamp at the current brightness.
static void map_byte(uint8_t base, uint8_t value, uint16_t on_gs) {
    for (int i = 0; i < 8; i++) {
        int bit = (value >> (7 - i)) & 1;
        tlc_set(base + i, bit ? on_gs : 0);
    }
}

static void render(void) {
    if (g_lamp_test) {
        tlc_set_all(TLC_GS_MAX);
        tlc_show();
        return;
    }
    // brightness 0..255 -> 12-bit grayscale
    uint16_t on = (uint16_t)((g_led.bright << 4) | (g_led.bright >> 4));
    map_byte(CH_ADDR_HI_BASE, g_led.addr_hi, on);
    map_byte(CH_ADDR_LO_BASE, g_led.addr_lo, on);
    map_byte(CH_DATA_BASE,    g_led.data,    on);
    for (int i = 0; i < 4; i++) {
        int bit = (g_led.status >> i) & 1;
        tlc_set(CH_STATUS_BASE + i, bit ? on : 0);
    }
    tlc_show();
}

// --- protocol handlers -----------------------------------------------------
static void on_led(const led_state_t *s)      { g_led = *s; render(); }
static void on_lamp_test(bool on)             { g_lamp_test = on; render(); }
static void on_brightness(uint8_t level)      { g_led.bright = level; render(); }

static void send_frame(const uint8_t *f, int n) {
    for (int i = 0; i < n; i++) putchar_raw(f[i]);
}

static void on_ping(void) {
    uint8_t f[5];
    int n = proto_build_version(f);
    send_frame(f, n);
}

// --- switch debounce + edge latch ------------------------------------------
static uint16_t sw_stable;        // debounced switch word
static uint16_t sw_candidate;     // last raw sample
static int      sw_count;         // consecutive matching samples
static uint8_t  cmd_prev;         // previous command-switch nibble
static uint8_t  events_latched;   // rising edges since last report

static void sample_switches(void) {
    uint16_t raw = hc165_read();
    if (raw == sw_candidate) {
        if (sw_count < DEBOUNCE_STABLE) sw_count++;
    } else {
        sw_candidate = raw;
        sw_count = 0;
    }
    if (sw_count >= DEBOUNCE_STABLE && raw != sw_stable) {
        sw_stable = raw;
        uint8_t cmd = (uint8_t)((sw_stable >> SW_CMD_BASE) & 0x0F);
        uint8_t rising = (uint8_t)(cmd & ~cmd_prev);   // 0->1 transitions
        events_latched |= rising;
        cmd_prev = cmd;
    }
}

static void send_switch_report(void) {
    uint8_t sw_data = (uint8_t)((sw_stable >> SW_DATA_BASE) & 0xFF);
    uint8_t sw_cmd  = (uint8_t)((sw_stable >> SW_CMD_BASE) & 0x0F);
    uint8_t f[6];
    int n = proto_build_switch(f, sw_data, sw_cmd, events_latched);
    send_frame(f, n);
    events_latched = 0;   // consumed
}

int main(void) {
    stdio_init_all();
    stdio_set_translate_crlf(&stdio_usb, false);   // binary-clean CDC

    tlc_init();
    hc165_init();

    proto_handlers_t h = {
        .on_led = on_led,
        .on_lamp_test = on_lamp_test,
        .on_brightness = on_brightness,
        .on_ping = on_ping,
    };
    proto_init(&h);

    g_led.bright = 255;
    render();

    absolute_time_t next_debounce = get_absolute_time();
    absolute_time_t next_heartbeat = get_absolute_time();
    uint16_t last_reported = 0xFFFF;

    for (;;) {
        // Drain incoming host bytes without blocking.
        int c;
        while ((c = getchar_timeout_us(0)) != PICO_ERROR_TIMEOUT) {
            proto_feed((uint8_t)c);
        }

        if (absolute_time_diff_us(get_absolute_time(), next_debounce) <= 0) {
            sample_switches();
            next_debounce = delayed_by_ms(get_absolute_time(), DEBOUNCE_MS);

            bool changed = (sw_stable != last_reported) || (events_latched != 0);
            if (changed) {
                send_switch_report();
                last_reported = sw_stable;
                next_heartbeat = delayed_by_ms(get_absolute_time(), HEARTBEAT_MS);
            }
        }

        if (absolute_time_diff_us(get_absolute_time(), next_heartbeat) <= 0) {
            send_switch_report();
            last_reported = sw_stable;
            next_heartbeat = delayed_by_ms(get_absolute_time(), HEARTBEAT_MS);
        }
    }
}
