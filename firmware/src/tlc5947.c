#include "tlc5947.h"
#include "config.h"
#include "pico/stdlib.h"
#include "hardware/pwm.h"
#include "hardware/gpio.h"

// Local grayscale buffer, one 12-bit value per channel across the whole chain.
static uint16_t gs_buf[TLC_TOTAL_CH];

void tlc_set(int channel, uint16_t gs) {
    if (channel < 0 || channel >= TLC_TOTAL_CH) return;
    if (gs > TLC_GS_MAX) gs = TLC_GS_MAX;
    gs_buf[channel] = gs;
}

void tlc_set_all(uint16_t gs) {
    if (gs > TLC_GS_MAX) gs = TLC_GS_MAX;
    for (int i = 0; i < TLC_TOTAL_CH; i++) gs_buf[i] = gs;
}

// Bit-bang one bit MSB-first. The TLC5947 clocks in on the rising edge of SCLK.
static inline void shift_bit(int bit) {
    gpio_put(PIN_TLC_SIN, bit & 1);
    gpio_put(PIN_TLC_SCLK, 1);
    gpio_put(PIN_TLC_SCLK, 0);
}

// Serialize the buffer to the chain.
//
// TLC5947 expects, per device, channel 23 first down to channel 0, each as a
// 12-bit value MSB-first. In a cascade the *last* physical device must receive
// its data first. We map buffer index = device*24 + channel, so the highest
// device index is the one furthest from SIN unless the wiring is reversed.
static void shift_out(void) {
    for (int d = 0; d < TLC_COUNT; d++) {
        int dev = TLC_REVERSE_DEVICE_ORDER ? d : (TLC_COUNT - 1 - d);
        for (int ch = TLC_CHANNELS - 1; ch >= 0; ch--) {
            uint16_t v = gs_buf[dev * TLC_CHANNELS + ch] & 0x0FFF;
            for (int b = 11; b >= 0; b--) shift_bit((v >> b) & 1);
        }
    }
}

void tlc_show(void) {
    shift_out();
    // Latch: XLAT high pulse copies the shift register into the PWM comparators.
    gpio_put(PIN_TLC_XLAT, 1);
    sleep_us(1);
    gpio_put(PIN_TLC_XLAT, 0);
}

// Free-running grayscale clock on PIN_TLC_GSCLK via a PWM slice at ~50% duty.
static void start_gsclk(void) {
    gpio_set_function(PIN_TLC_GSCLK, GPIO_FUNC_PWM);
    uint slice = pwm_gpio_to_slice_num(PIN_TLC_GSCLK);
    // 125 MHz sys clock / TLC_GSCLK_HZ = wrap count for a full period.
    uint32_t wrap = (125000000u / TLC_GSCLK_HZ);
    if (wrap < 2) wrap = 2;
    pwm_set_wrap(slice, wrap - 1);
    pwm_set_gpio_level(PIN_TLC_GSCLK, wrap / 2);
    pwm_set_enabled(slice, true);
}

void tlc_init(void) {
    gpio_init(PIN_TLC_SIN);   gpio_set_dir(PIN_TLC_SIN, GPIO_OUT);
    gpio_init(PIN_TLC_SCLK);  gpio_set_dir(PIN_TLC_SCLK, GPIO_OUT);
    gpio_init(PIN_TLC_XLAT);  gpio_set_dir(PIN_TLC_XLAT, GPIO_OUT);
    gpio_init(PIN_TLC_BLANK); gpio_set_dir(PIN_TLC_BLANK, GPIO_OUT);
    gpio_put(PIN_TLC_SIN, 0);
    gpio_put(PIN_TLC_SCLK, 0);
    gpio_put(PIN_TLC_XLAT, 0);

    // Hold BLANK high while we prime the chain, then release to enable outputs.
    gpio_put(PIN_TLC_BLANK, 1);
    start_gsclk();
    tlc_set_all(0);
    tlc_show();
    gpio_put(PIN_TLC_BLANK, 0);   // outputs enabled; GS counter free-runs
}
