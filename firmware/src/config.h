#ifndef IMSPI_CONFIG_H
#define IMSPI_CONFIG_H

// ---------------------------------------------------------------------------
// IMSPI 8080 panel firmware configuration
//
// GPIO numbers below apply to the RP2350A rework (rev6). Several nets keep
// the same RP2040 GPIO numbers because the board wiring is unchanged.
// ---------------------------------------------------------------------------

// --- TLC5947 LED driver chain ----------------------------------------------
#define TLC_COUNT        2          // number of daisy-chained TLC5947s
#define TLC_CHANNELS     24         // channels per device
#define TLC_TOTAL_CH     (TLC_COUNT * TLC_CHANNELS)   // 48
#define TLC_GS_MAX       4095       // 12-bit grayscale

#define PIN_TLC_SIN      3          // serial data in  (SPI TX / bit-bang)
#define PIN_TLC_SCLK     2          // serial clock    (SPI SCK)
#define PIN_TLC_XLAT     4          // latch pulse
#define PIN_TLC_BLANK    5          // blank / GS counter reset (active high)

// Set to 1 if your physical cascade wiring clocks device 0 first instead of
// the last device first (flip if the wrong chip lights up).
#define TLC_REVERSE_DEVICE_ORDER 0

// --- 74HC165 switch chain --------------------------------------------------
#define HC165_COUNT      2          // daisy-chained 74HC165s -> 16 inputs
#define HC165_BITS       (HC165_COUNT * 8)            // 16

#define PIN_HC_PLOAD     7          // SH/LD  (active low parallel load)
#define PIN_HC_CLK       8          // CLK
#define PIN_HC_DATA      9          // QH from the last device in the chain

// --- SD card (SPI1) --------------------------------------------------------
#define PIN_SD_SCK       10
#define PIN_SD_MOSI      11
#define PIN_SD_MISO      12
#define PIN_SD_CS        13

// Set to 1 to reverse bit order if switches map backwards.
#define HC165_REVERSE_BITS 0

// --- Lamp channel map (index into the TLC grayscale buffer) ----------------
// Left block rows + right status row. bit i of each register -> a channel.
#define CH_ADDR_HI_BASE  0          // A15..A8  -> ch 0..7   (bit7=A15 -> ch0)
#define CH_ADDR_LO_BASE  8          // A7..A0   -> ch 8..15
#define CH_DATA_BASE     16         // D7..D0   -> ch 16..23
#define CH_STATUS_BASE   24         // status0..3 -> ch 24..27

// --- Switch bit map (index into the 16-bit HC165 word) ---------------------
#define SW_DATA_BASE     0          // data toggles 0..7 -> bits 0..7
#define SW_CMD_BASE      8          // command switches 0..3 -> bits 8..11
#define SW_CMD_COUNT     4

// --- Timing ----------------------------------------------------------------
#define DEBOUNCE_MS      5          // switch sample interval
#define DEBOUNCE_STABLE  3          // stable samples required to accept a change
#define HEARTBEAT_MS     250        // periodic switch report even if unchanged

// --- Protocol --------------------------------------------------------------
#define SOF_HOST_TO_PANEL 0xA5
#define SOF_PANEL_TO_HOST 0x5A

#define CMD_LED           0x01      // 8-byte LED update
#define CMD_LAMP_TEST     0x02      // 4-byte lamp test
#define CMD_BRIGHTNESS    0x03      // 4-byte set brightness
#define CMD_PING          0x7F      // 3-byte ping

#define RSP_SWITCH        0x81      // 6-byte switch report
#define RSP_VERSION       0xC0      // 5-byte version

#define VERSION_MAJOR     0
#define VERSION_MINOR     1

#endif // IMSPI_CONFIG_H
