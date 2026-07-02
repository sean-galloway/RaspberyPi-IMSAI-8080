#include "protocol.h"
#include "config.h"
#include "crc8.h"
#include <string.h>

static proto_handlers_t H;

// Incremental frame assembly.
static uint8_t buf[8];
static int idx;
static int need;   // total frame length once CMD is known, 0 = waiting for SOF

void proto_init(const proto_handlers_t *h) {
    H = *h;
    idx = 0;
    need = 0;
}

static int frame_len_for_cmd(uint8_t cmd) {
    switch (cmd) {
        case CMD_LED:        return 8;
        case CMD_LAMP_TEST:  return 4;
        case CMD_BRIGHTNESS: return 4;
        case CMD_PING:       return 3;
        default:             return -1;
    }
}

static void dispatch(void) {
    // CRC over every byte except the final one.
    if (crc8(buf, need - 1) != buf[need - 1]) return;

    switch (buf[1]) {
        case CMD_LED: {
            led_state_t s = {
                .addr_hi = buf[2], .addr_lo = buf[3], .data = buf[4],
                .status = buf[5], .bright = buf[6],
            };
            if (H.on_led) H.on_led(&s);
            break;
        }
        case CMD_LAMP_TEST:
            if (H.on_lamp_test) H.on_lamp_test(buf[2] != 0);
            break;
        case CMD_BRIGHTNESS:
            if (H.on_brightness) H.on_brightness(buf[2]);
            break;
        case CMD_PING:
            if (H.on_ping) H.on_ping();
            break;
        default:
            break;
    }
}

void proto_feed(uint8_t byte) {
    if (need == 0) {
        // Hunting for SOF.
        if (byte == SOF_HOST_TO_PANEL) {
            buf[0] = byte;
            idx = 1;
            need = -1;   // next byte is CMD
        }
        return;
    }

    if (need == -1) {
        // This byte is CMD; resolve the frame length.
        int len = frame_len_for_cmd(byte);
        if (len < 0) { need = 0; idx = 0; return; }   // unknown -> resync
        buf[1] = byte;
        idx = 2;
        need = len;
        return;
    }

    buf[idx++] = byte;
    if (idx >= need) {
        dispatch();
        need = 0;
        idx = 0;
    }
}

int proto_build_switch(uint8_t *out, uint8_t sw_data, uint8_t sw_cmd, uint8_t events) {
    out[0] = SOF_PANEL_TO_HOST;
    out[1] = RSP_SWITCH;
    out[2] = sw_data;
    out[3] = sw_cmd;
    out[4] = events;
    out[5] = crc8(out, 5);
    return 6;
}

int proto_build_version(uint8_t *out) {
    out[0] = SOF_PANEL_TO_HOST;
    out[1] = RSP_VERSION;
    out[2] = VERSION_MAJOR;
    out[3] = VERSION_MINOR;
    out[4] = crc8(out, 4);
    return 5;
}
