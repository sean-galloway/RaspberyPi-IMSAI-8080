"""IMSPI 8080 panel controller — schematic as code (SKiDL).

This captures the full connectivity and emits a KiCad netlist you import into
pcbnew (File -> Import -> Netlist) to start layout. Run:

    pip install skidl
    python imspi8080_skidl.py        # -> imspi8080.net

HONEST CAVEATS (read before running):
- SKiDL resolves symbols from your local KiCad libraries. RP2040 (MCU_RaspberryPi),
  74HC165, R/C/LED, and Regulator_Linear:AMS1117 exist in stock libs. TLC5947, the
  USB-C receptacle, the microSD socket, and the JST S*B-XH-A headers may need a
  library path or a custom symbol — those Part() calls are flagged TODO.
- Footprints below are indicative; confirm each against bom.csv before netlisting.
- This is a scaffold: the power/MCU/shift-register/switch nets are wired; the 28
  LED-to-TLC channel nets are generated in a loop but assume TLC5947 pin names
  OUT0..OUT23 — adjust to your symbol.

Pin/GPIO assignment mirrors hardware/design-spec.md.
"""
from skidl import Part, Net, Bus, generate_netlist, TEMPLATE

# ---------------------------------------------------------------------------
# Power nets
# ---------------------------------------------------------------------------
gnd     = Net('GND')
v5_log  = Net('VBUS_LOGIC')   # USB-C #1 5V
v5_led  = Net('VBUS_LED')     # USB-C #2 5V (LED anodes)
v3_log  = Net('+3V3')         # logic rail
v3_led  = Net('+3V3_LED')     # LED anode rail

# ---------------------------------------------------------------------------
# Regulators (AMS1117-3.3): logic and LED rails
# ---------------------------------------------------------------------------
reg_l = Part('Regulator_Linear', 'AMS1117-3.3', footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
reg_d = Part('Regulator_Linear', 'AMS1117-3.3', footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2')
reg_l['VI'] += v5_log; reg_l['VO'] += v3_log; reg_l['GND'] += gnd
reg_d['VI'] += v5_led; reg_d['VO'] += v3_led; reg_d['GND'] += gnd

# ---------------------------------------------------------------------------
# MCU: RP2040 minimal design (copy the reference schematic for flash/xtal/USB)
# ---------------------------------------------------------------------------
mcu = Part('MCU_RaspberryPi', 'RP2040', footprint='Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm')
# Power the IO/USB banks and ground; core 1.1V is internal (decouple DVDD).
for p in ('IOVDD', 'USB_VDD', 'ADC_AVDD', 'VREG_VIN'):
    mcu[p] += v3_log
mcu['GND'] += gnd

# Peripheral GPIO -> named nets (see design-spec.md)
nets = {n: Net(n) for n in (
    'TLC_SCLK','TLC_SIN','TLC_XLAT','TLC_BLANK','TLC_GSCLK',
    'HC_PLOAD','HC_CLK','HC_QH',
    'SD_SCK','SD_MOSI','SD_MISO','SD_CS')}
gpio = {'GPIO2':'TLC_SCLK','GPIO3':'TLC_SIN','GPIO4':'TLC_XLAT','GPIO5':'TLC_BLANK',
        'GPIO6':'TLC_GSCLK','GPIO7':'HC_PLOAD','GPIO8':'HC_CLK','GPIO9':'HC_QH',
        'GPIO10':'SD_SCK','GPIO11':'SD_MOSI','GPIO12':'SD_MISO','GPIO13':'SD_CS'}
for pin, net in gpio.items():
    mcu[pin] += nets[net]

# ---------------------------------------------------------------------------
# LED drivers: 2x TLC5947 daisy-chained on SPI0        (TODO: symbol/lib)
# ---------------------------------------------------------------------------
tlc0 = Part('Driver_LED', 'TLC5947', footprint='Package_SO:HTSSOP-32_6.1x11mm_P0.65mm', dest=TEMPLATE)
U3 = tlc0(); U4 = tlc0()
for u in (U3, U4):
    u['VCC'] += v3_log; u['GND'] += gnd
    u['SCK'] += nets['TLC_SCLK']; u['XLAT'] += nets['TLC_XLAT']
    u['BLANK'] += nets['TLC_BLANK']; u['GSCLK'] += nets['TLC_GSCLK']
U3['SIN'] += nets['TLC_SIN']
chain = Net('TLC_CHAIN'); U3['SOUT'] += chain; U4['SIN'] += chain
# IREF resistors set per-channel current
for u in (U3, U4):
    r = Part('Device','R', value='2.4k', footprint='Resistor_SMD:R_0402_1005Metric')
    u['IREF'] += r[1]; r[2] += gnd

# 28 LEDs: anodes on the LED rail, cathodes sink into TLC channels.
# Channel map: U3 OUT0..23 = addr hi/lo/data (D1..D24); U4 OUT0..3 = status (D25..28)
for i in range(24):
    d = Part('Device','LED', ref=f'D{i+1}', footprint='LED_SMD:LED_1206_3216Metric')
    d['A'] += v3_led; d['K'] += U3[f'OUT{i}']
for i in range(4):
    d = Part('Device','LED', ref=f'D{25+i}', footprint='LED_SMD:LED_1206_3216Metric')
    d['A'] += v3_led; d['K'] += U4[f'OUT{i}']

# ---------------------------------------------------------------------------
# Switch inputs: 2x 74HC165 daisy-chained
# ---------------------------------------------------------------------------
hc = Part('74xx','74HC165', footprint='Package_SO:TSSOP-16_4.4x5mm_P0.65mm', dest=TEMPLATE)
U5 = hc(); U6 = hc()
for u in (U5, U6):
    u['VCC'] += v3_log; u['GND'] += gnd
    u['SH_LD'] += nets['HC_PLOAD']; u['CLK'] += nets['HC_CLK']
hc_chain = Net('HC_CHAIN'); U5['QH'] += hc_chain; U6['SER'] += hc_chain
U6['QH'] += nets['HC_QH']

# ---------------------------------------------------------------------------
# Switch bank headers: right-angle JST-XH               (TODO: symbol/lib)
# J3 data bank (S10B-XH-A): 3V3, SW0..7, GND
# J4 command bank (S6B-XH-A): GND, CMD0..3, spare  (+ on-board pull-ups)
# ---------------------------------------------------------------------------
J3 = Part('Connector','Conn_01x10', footprint='Connector_JST:JST_XH_S10B-XH-A_1x10_P2.50mm_Horizontal')
J4 = Part('Connector','Conn_01x06', footprint='Connector_JST:JST_XH_S06B-XH-A_1x06_P2.50mm_Horizontal')
J3[1] += v3_log; J3[10] += gnd
for k in range(8):
    J3[k+2] += U5['A'] if k == 0 else Net(f'SW{k}')   # wire to HC165 inputs A..H
J4[1] += gnd; J4[6] += Net('SW_SPARE')
for k in range(4):
    sig = Net(f'CMD{k}')
    J4[k+2] += sig
    pu = Part('Device','R', value='10k', footprint='Resistor_SMD:R_0402_1005Metric')
    pu[1] += v3_log; pu[2] += sig       # released-state pull-up for momentary switch

# ---------------------------------------------------------------------------
# microSD (SPI1) + USB-C x2                              (TODO: symbols/lib)
# ---------------------------------------------------------------------------
sd = Part('Connector','microSD_card_socket', footprint='TODO:microSD_push_pull')
sd['CLK'] += nets['SD_SCK']; sd['CMD'] += nets['SD_MOSI']
sd['DAT0'] += nets['SD_MISO']; sd['DAT3'] += nets['SD_CS']
sd['VDD'] += v3_log; sd['VSS'] += gnd

# USB-C #1: power + data. #2: power only. Both need 5.1k CC pulldowns.
# (Instantiate your USB-C symbol here; wire VBUS, GND, CC1/CC2->5.1k, and for #1
#  the D+/D- pair through 27R series to the RP2040 USB pins.)

generate_netlist(file_='imspi8080.net')
