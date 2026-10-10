"""IMSPI 8080 panel controller — schematic as code (SKiDL).

Emits a KiCad netlist (``imspi8080.net``) you import into the PCB editor to start
layout. This is the *complete, bootable* net definition: RP2040 + QSPI flash +
crystal + dual USB-C + 2x TLC5947 + 2x 74HC165 + microSD + switch headers, wired
per ``design-spec.md`` and ``bom.csv``. Reference designators match ``bom.csv`` so
the JLCPCB BOM/CPL match cleanly.

Run:

    pip install skidl
    # point SKiDL at your KiCad symbol libraries (KiCad 8/9/10 all live here on Linux):
    export KICAD7_SYMBOL_DIR=/usr/share/kicad/symbols
    export KICAD8_SYMBOL_DIR=/usr/share/kicad/symbols
    export KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols
    python imspi8080_skidl.py            # -> imspi8080.net

Verified against KiCad 10.0.4 stock libraries. Notable corrections vs. the original
scaffold, all confirmed against the actual symbols:
  * TLC5947 symbol is ``TLC5947DAP`` (HTSSOP) — plain "TLC5947" does not exist.
  * TLC5947 has NO GSCLK pin (internal grayscale oscillator). design-spec.md lists
    a TLC_GSCLK on GP2..? — that net is dropped; GPIO6 is left as a spare/testpoint.
  * TLC pins are SCLK/SIN/SOUT/XLAT/BLANK/VCC/GND/IREF/PowerPAD (not SCK/GSCLK).
  * 74HC165 pins are ~{PL}(SH/LD) / CP(CLK) / ~{CE} / DS(serial-in) / Q7 / D0..D7.
  * HTSSOP-32 footprint is Texas_DAD0032A_HTSSOP-32_...; JST is S6B (not S06B).

The tall/edge parts (USB-C, microSD, JST) sit at the board edges per the layout
plan so nothing but the LEDs exceeds the bezel standoff height.
"""
from skidl import Part, Net, generate_netlist, TEMPLATE

# ---------------------------------------------------------------------------
# Footprint shorthands
# ---------------------------------------------------------------------------
FP_R      = 'Resistor_SMD:R_0402_1005Metric'
FP_C      = 'Capacitor_SMD:C_0402_1005Metric'
FP_C0805  = 'Capacitor_SMD:C_0805_2012Metric'
FP_LED    = 'LED_SMD:LED_1206_3216Metric'


def R(ref, value):
    return Part('Device', 'R', ref=ref, value=value, footprint=FP_R)


def C(ref, value, fp=FP_C):
    return Part('Device', 'C', ref=ref, value=value, footprint=fp)


# ---------------------------------------------------------------------------
# Power nets
# ---------------------------------------------------------------------------
gnd     = Net('GND')
vbus_l  = Net('VBUS_LOGIC')   # USB-C J1 5V
vbus_d  = Net('VBUS_LED')     # USB-C J2 5V (LED anode supply)
v3_log  = Net('+3V3')         # logic rail
v3_led  = Net('+3V3_LED')     # LED anode rail
vcore   = Net('VCORE')        # RP2040 1.1V core (internal LDO output)

# ---------------------------------------------------------------------------
# Regulators (AMS1117-3.3): U8 logic rail, U9 LED rail
# ---------------------------------------------------------------------------
FP_SOT223 = 'Package_TO_SOT_SMD:SOT-223-3_TabPin2'
U8 = Part('Regulator_Linear', 'AMS1117-3.3', ref='U8', footprint=FP_SOT223)
U9 = Part('Regulator_Linear', 'AMS1117-3.3', ref='U9', footprint=FP_SOT223)
U8['VI'] += vbus_l; U8['VO'] += v3_log; U8['GND'] += gnd
U9['VI'] += vbus_d; U9['VO'] += v3_led; U9['GND'] += gnd

# ---------------------------------------------------------------------------
# MCU: RP2040 minimal reference design (U1)
# ---------------------------------------------------------------------------
mcu = Part('MCU_RaspberryPi', 'RP2040', ref='U1',
           footprint='Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm')
mcu['IOVDD']    += v3_log      # all six IOVDD pins
mcu['USB_VDD']  += v3_log
mcu['ADC_AVDD'] += v3_log      # tie to 3V3 (add ferrite in layout if you want a clean ADC)
mcu['VREG_VIN'] += v3_log      # feed the internal core LDO from 3V3
mcu['VREG_VOUT']+= vcore       # 1.1V core out
mcu['DVDD']     += vcore       # both DVDD (digital core) pins from the internal LDO
mcu['GND']      += gnd         # QFN exposed pad (pin 57)
mcu['TESTEN']   += gnd         # tie low (required)

# --- QSPI boot flash: W25Q128 (U2) ----------------------------------------
qspi_ss   = Net('QSPI_SS')
qspi_sclk = Net('QSPI_SCLK')
qspi_sd0  = Net('QSPI_SD0'); qspi_sd1 = Net('QSPI_SD1')
qspi_sd2  = Net('QSPI_SD2'); qspi_sd3 = Net('QSPI_SD3')
mcu['~{QSPI_SS}'] += qspi_ss
mcu['QSPI_SCLK']  += qspi_sclk
mcu['QSPI_SD0']   += qspi_sd0; mcu['QSPI_SD1'] += qspi_sd1
mcu['QSPI_SD2']   += qspi_sd2; mcu['QSPI_SD3'] += qspi_sd3

U2 = Part('Memory_Flash', 'W25Q128JVS', ref='U2',
          footprint='Package_SO:SOIC-8_3.9x4.9mm_P1.27mm')
U2[1] += qspi_ss     # ~CS
U2[6] += qspi_sclk   # CLK
U2[5] += qspi_sd0    # DI/IO0
U2[2] += qspi_sd1    # DO/IO1
U2[3] += qspi_sd2    # ~WP/IO2
U2[7] += qspi_sd3    # ~HOLD/IO3
U2[8] += v3_log; U2[4] += gnd

# BOOTSEL button (SW1): grounds flash CS at power-up to force USB bootrom mode.
SW1 = Part('Switch', 'SW_Push', ref='SW1',
           footprint='Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2')
SW1[1] += qspi_ss; SW1[2] += gnd

# --- Crystal: 12 MHz, 4-pin (Y1) with case pads grounded -------------------
xin  = Net('XIN'); xout = Net('XOUT')
mcu['XIN'] += xin; mcu['XOUT'] += xout
Y1 = Part('Device', 'Crystal_GND24', ref='Y1', value='12MHz',
          footprint='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm')
Y1[1] += xin; Y1[3] += xout; Y1['G'] += gnd   # pins 2 & 4 are the grounded case
C('C23', '15pF')[1, 2] += xin, gnd
C('C24', '15pF')[1, 2] += xout, gnd

# --- Reset button (SW2) on RUN --------------------------------------------
run = Net('RUN'); mcu['RUN'] += run           # RP2040 has an internal pull-up on RUN
SW2 = Part('Switch', 'SW_Push', ref='SW2',
           footprint='Button_Switch_SMD:SW_Push_1P1T_NO_CK_KMR2')
SW2[1] += run; SW2[2] += gnd

# --- SWD debug/reflash header (J5) ----------------------------------------
J5 = Part('Connector', 'Conn_01x03_Pin', ref='J5',
          footprint='Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical')
J5[1] += mcu['SWCLK']; J5[2] += mcu['SWDIO']; J5[3] += gnd

# ---------------------------------------------------------------------------
# Peripheral GPIO nets (see design-spec.md). GP6 (was TLC_GSCLK) is unused:
# the TLC5947 clocks grayscale off its own internal oscillator.
# ---------------------------------------------------------------------------
tlc_sclk = Net('TLC_SCLK'); tlc_sin = Net('TLC_SIN')
tlc_xlat = Net('TLC_XLAT'); tlc_blank = Net('TLC_BLANK')
hc_pload = Net('HC_PLOAD'); hc_clk = Net('HC_CLK'); hc_qh = Net('HC_QH')
sd_sck = Net('SD_SCK'); sd_mosi = Net('SD_MOSI'); sd_miso = Net('SD_MISO'); sd_cs = Net('SD_CS')
mcu['GPIO2'] += tlc_sclk; mcu['GPIO3'] += tlc_sin
mcu['GPIO4'] += tlc_xlat; mcu['GPIO5'] += tlc_blank
mcu['GPIO7'] += hc_pload; mcu['GPIO8'] += hc_clk; mcu['GPIO9'] += hc_qh
mcu['GPIO10'] += sd_sck; mcu['GPIO11'] += sd_mosi
mcu['GPIO12'] += sd_miso; mcu['GPIO13'] += sd_cs

# ---------------------------------------------------------------------------
# USB-C receptacles (J1 data+power, J2 power-only). Both TYPE-C-31-M-12 (16P).
# ---------------------------------------------------------------------------
FP_USBC = 'Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12'


def usb_power(J, vbus_net):
    """Wire the VBUS/GND/shield pins common to both connectors."""
    for p in ('A4', 'A9', 'B4', 'B9'):
        J[p] += vbus_net
    for p in ('A1', 'A12', 'B1', 'B12', 'SH'):
        J[p] += gnd


J1 = Part('Connector', 'USB_C_Receptacle_USB2.0_16P', ref='J1', footprint=FP_USBC)
J2 = Part('Connector', 'USB_C_Receptacle_USB2.0_16P', ref='J2', footprint=FP_USBC)
usb_power(J1, vbus_l)
usb_power(J2, vbus_d)

# CC pull-downs mark both connectors as sink (UFP). 5.1k each, one per CC line.
R('R1', '5.1k')[1, 2] += J1['A5'], gnd     # J1 CC1
R('R2', '5.1k')[1, 2] += J1['B5'], gnd     # J1 CC2
R('R3', '5.1k')[1, 2] += J2['A5'], gnd     # J2 CC1
R('R4', '5.1k')[1, 2] += J2['B5'], gnd     # J2 CC2

# J1 USB2 data: tie the A/B D+ and D- lanes, then 27R series to the RP2040.
dpj = Net('USB_DP_CONN'); dnj = Net('USB_DM_CONN')
J1['A6'] += dpj; J1['B6'] += dpj
J1['A7'] += dnj; J1['B7'] += dnj
R('R5', '27')[1, 2] += dpj, mcu['USB_DP']
R('R6', '27')[1, 2] += dnj, mcu['USB_DM']

# ---------------------------------------------------------------------------
# LED drivers: 2x TLC5947 daisy-chained on SPI0 (U3, U4)
# ---------------------------------------------------------------------------
FP_TLC = 'Package_SO:Texas_DAD0032A_HTSSOP-32_6.1x11mm_P0.65mm_TopEP3.71x3.81mm'
U3 = Part('Driver_LED', 'TLC5947DAP', ref='U3', footprint=FP_TLC)
U4 = Part('Driver_LED', 'TLC5947DAP', ref='U4', footprint=FP_TLC)
for u in (U3, U4):
    u['VCC'] += v3_log; u['GND'] += gnd; u['PowerPAD'] += gnd
    u['SCLK'] += tlc_sclk; u['XLAT'] += tlc_xlat; u['BLANK'] += tlc_blank
U3['SIN'] += tlc_sin
tlc_chain = Net('TLC_CHAIN'); U3['SOUT'] += tlc_chain; U4['SIN'] += tlc_chain
# U4['SOUT'] left open (chain end / optional test point)
R('R7', '2.4k')[1, 2] += U3['IREF'], gnd   # sets ~15mA/channel; raise R to dim
R('R8', '2.4k')[1, 2] += U4['IREF'], gnd

# 28 LEDs: anodes on the LED rail, cathodes sink into TLC channels.
#   U3 OUT0..23 = addr hi/lo/data (D1..D24); U4 OUT0..3 = status (D25..D28)
for i in range(24):
    d = Part('Device', 'LED', ref=f'D{i+1}', footprint=FP_LED)
    d['A'] += v3_led; d['K'] += U3[f'OUT{i}']
for i in range(4):
    d = Part('Device', 'LED', ref=f'D{25+i}', footprint=FP_LED)
    d['A'] += v3_led; d['K'] += U4[f'OUT{i}']

# ---------------------------------------------------------------------------
# Switch inputs: 2x 74HC165 daisy-chained (U5 data bank, U6 command bank)
# ---------------------------------------------------------------------------
FP_HC = 'Package_SO:TSSOP-16_4.4x5mm_P0.65mm'
U5 = Part('74xx', '74HC165', ref='U5', footprint=FP_HC)
U6 = Part('74xx', '74HC165', ref='U6', footprint=FP_HC)
for u in (U5, U6):
    u['VCC'] += v3_log; u['GND'] += gnd
    u['~{PL}'] += hc_pload; u['CP'] += hc_clk; u['~{CE}'] += gnd
U5['DS'] += gnd                                   # first stage serial-in unused
hc_chain = Net('HC_CHAIN'); U5['Q7'] += hc_chain; U6['DS'] += hc_chain
U6['Q7'] += hc_qh                                 # MCU reads the chain here

# ---------------------------------------------------------------------------
# Switch bank headers (right-angle JST-XH along the bezel edge)
# J3 data bank:    1:3V3 2:SW0 .. 9:SW7 10:GND      -> U5 D0..D7
# J4 command bank: 1:GND 2:CMD0 .. 5:CMD3 6:spare   -> U6 D0..D3 (+ on-board pull-ups)
# ---------------------------------------------------------------------------
J3 = Part('Connector', 'Conn_01x10_Pin', ref='J3',
          footprint='Connector_JST:JST_XH_S10B-XH-A_1x10_P2.50mm_Horizontal')
J3[1] += v3_log; J3[10] += gnd
for k in range(8):
    sw = Net(f'SW{k}')
    J3[k + 2] += sw
    U5[f'D{k}'] += sw

J4 = Part('Connector', 'Conn_01x06_Pin', ref='J4',
          footprint='Connector_JST:JST_XH_S6B-XH-A_1x06_P2.50mm_Horizontal')
J4[1] += gnd; J4[6] += Net('SW_SPARE')
cmd_pu = ['R13', 'R14', 'R15', 'R16']
for k in range(4):
    cmd = Net(f'CMD{k}')
    J4[k + 2] += cmd
    U6[f'D{k}'] += cmd
    R(cmd_pu[k], '10k')[1, 2] += v3_log, cmd     # released-state pull-up (momentary)
for k in range(4, 8):
    U6[f'D{k}'] += gnd                            # tie unused 165 inputs low

# ---------------------------------------------------------------------------
# microSD (SPI1) — U7
# ---------------------------------------------------------------------------
U7 = Part('Connector', 'Micro_SD_Card', ref='U7',
          footprint='Connector_Card:microSD_HC_Hirose_DM3AT-SF-PEJM5')
U7['CLK'] += sd_sck; U7['CMD'] += sd_mosi
U7['DAT0'] += sd_miso; U7['DAT3/CD'] += sd_cs
U7['VDD'] += v3_log; U7['VSS'] += gnd; U7['SHIELD'] += gnd
# Pull-ups (SPI mode): CS, DAT0/MISO, and the unused DAT1/DAT2 held high.
R('R9',  '10k')[1, 2] += v3_log, sd_cs
R('R10', '10k')[1, 2] += v3_log, sd_miso
R('R11', '10k')[1, 2] += v3_log, U7['DAT1']
R('R12', '10k')[1, 2] += v3_log, U7['DAT2']

# ---------------------------------------------------------------------------
# Decoupling & bulk (refs per bom.csv)
# ---------------------------------------------------------------------------
# RP2040: several 100nF on IOVDD/USB_VDD/ADC_AVDD/VREG_VIN, 1uF on the core.
for ref in ('C1', 'C2', 'C3', 'C4', 'C5', 'C15'):
    C(ref, '100nF')[1, 2] += v3_log, gnd
C('C6', '100nF')[1, 2] += mcu['ADC_AVDD'], gnd      # sits at the ADC pin
C('C16', '1uF')[1, 2] += vcore, gnd                 # VREG_VOUT core decoupling
C('C17', '1uF')[1, 2] += vcore, gnd
# Per-IC 100nF
C('C7', '100nF')[1, 2] += v3_log, gnd     # U3
C('C8', '100nF')[1, 2] += v3_log, gnd     # U4
C('C9', '100nF')[1, 2] += v3_log, gnd     # U5
C('C10', '100nF')[1, 2] += v3_log, gnd    # U6
C('C11', '100nF')[1, 2] += v3_log, gnd    # U2 flash
C('C12', '100nF')[1, 2] += v3_log, gnd    # U7 SD
C('C13', '100nF')[1, 2] += v3_log, gnd    # U8 out
C('C14', '100nF')[1, 2] += v3_led, gnd    # U9 out
C('C18', '1uF')[1, 2] += v3_log, gnd      # SD local bulk
C('C19', '1uF')[1, 2] += v3_log, gnd      # spare local bulk
# Bulk
C('C20', '10uF', FP_C0805)[1, 2] += v3_log, gnd
C('C21', '10uF', FP_C0805)[1, 2] += v3_led, gnd
C('C22', '10uF', FP_C0805)[1, 2] += vbus_l, gnd

# R17/R18 (spare 10k in the BOM) are intentionally not placed in the netlist.

generate_netlist(file_='imspi8080.net')
