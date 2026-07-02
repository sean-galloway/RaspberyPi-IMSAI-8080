"""Bring-up tool: sweep every lamp, ramp brightness, and print switch reports.

Usage: python lamp_test.py [/dev/ttyACM0]
"""

import sys
import time

from imspi import Panel


def main(port: str) -> None:
    with Panel(port) as p:
        ver = p.ping()
        print(f"panel version: {ver}")

        print("all-on lamp test (2s)...")
        p.lamp_test(True)
        time.sleep(2.0)
        p.lamp_test(False)

        print("walking the address bus...")
        for i in range(16):
            p.set_bus(addr=(1 << i), data=0, status=0)
            time.sleep(0.08)

        print("walking the data bus...")
        for i in range(8):
            p.set_bus(addr=0, data=(1 << i), status=0)
            time.sleep(0.08)

        print("status lamps...")
        for i in range(4):
            p.set_bus(addr=0, data=0, status=(1 << i))
            time.sleep(0.2)

        print("brightness ramp...")
        p.set_bus(addr=0xFFFF, data=0xFF, status=0x0F)
        for level in list(range(0, 256, 8)) + list(range(255, -1, -8)):
            p.set_brightness(level)
            time.sleep(0.02)
        p.set_brightness(255)

        print("reading switches for 10s (flip toggles / press commands)...")
        end = time.monotonic() + 10
        last = None
        while time.monotonic() < end:
            rep = p.poll(timeout=0.1)
            if rep and rep != last:
                pressed = [
                    name
                    for name, hit in (
                        ("RUN/STOP", rep.run_stop),
                        ("STEP", rep.single_step),
                        ("EXAMINE", rep.examine),
                        ("DEPOSIT", rep.deposit),
                    )
                    if hit
                ]
                print(
                    f"data={rep.data:08b} cmd={rep.cmd:04b} "
                    f"events={pressed or '-'}"
                )
                last = rep


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/dev/ttyACM0")
