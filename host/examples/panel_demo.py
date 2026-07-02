"""Synthetic-bus demo: proves the whole panel without an emulator.

Runs a fake CPU: an address counter advances while "running", the data lamps
mirror the 8 data toggles, and the RUN/STOP command switch toggles run state.
EXAMINE loads the data toggles into the low address byte.

Usage: python panel_demo.py [/dev/ttyACM0]
"""

import sys
import time

from imspi import Panel

STATUS_RUN = 0b0001
STATUS_WAIT = 0b0010


def main(port: str) -> None:
    with Panel(port) as p:
        print(f"panel version: {p.ping()}")
        addr = 0x0000
        data = 0x00
        running = True

        while True:
            rep = p.poll(timeout=0.0)
            if rep is not None:
                data = rep.data                 # data lamps follow data toggles
                if rep.run_stop:
                    running = not running
                if rep.examine:
                    addr = (addr & 0xFF00) | rep.data
                if rep.single_step and not running:
                    addr = (addr + 1) & 0xFFFF

            if running:
                addr = (addr + 1) & 0xFFFF

            status = STATUS_RUN if running else STATUS_WAIT
            p.set_bus(addr=addr, data=data, status=status)
            time.sleep(0.03)


if __name__ == "__main__":
    try:
        main(sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0")
    except KeyboardInterrupt:
        print("\nbye")
