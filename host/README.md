# IMSPI 8080 host driver

Python driver for the Pi side of the panel. Talks the serial protocol in
`../docs/protocol.md` to the RP2040 over USB CDC (`/dev/ttyACM0`).

## Install

```bash
cd host
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Use

```python
from imspi import Panel

with Panel("/dev/ttyACM0") as p:
    print(p.ping())                       # (major, minor)
    p.set_bus(addr=0x1234, data=0x76, status=0b0001)  # RUN lamp on
    rep = p.poll(timeout=1.0)             # latest SwitchReport, or None
    if rep and rep.examine:               # command switch 2 (EXAMINE) pressed
        print("examine, data toggles =", hex(rep.data))
```

## Examples

```bash
python examples/lamp_test.py /dev/ttyACM0     # bring-up: sweep lamps, print switches
python examples/panel_demo.py /dev/ttyACM0    # synthetic bus + live switch echo
```

`panel_demo.py` drives the panel with a fake address/data bus and mirrors the data
toggles onto the data lamps, so you can validate the whole panel before wiring an
emulator. For z80pack/SIMH, replace the synthetic loop with the emulator's CPU
state and feed switch events back into its I/O hook.
