#!/usr/bin/env python3
"""battery runtime + current draw estimate for the v2 power tree.

models the two rails from the schematic:
- Pi rail:   2S -> UBEC (5V) -> Pi 3 B+ + camera + usb mic
- motor rail: 2S -> TB6612 VM -> 2x N20

all numbers are typical estimates, tweak the constants to your parts.
usage: python scripts/power_budget.py [--mah 1500] [--cells 2]"""

import argparse

# --- assumptions (edit to match your measured parts) ---------------------
CELL_NOMINAL_V = 3.7          # per-cell nominal
USABLE_FRACTION = 0.8         # don't drain a lipo below ~20%
UBEC_EFF = 0.85               # switching regulator efficiency

# 5V rail current draw (amps at 5V)
PI_IDLE_A = 0.45              # pi 3 b+ mostly idle
PI_BUSY_A = 0.85             # opencv + camera working
CAMERA_A = 0.25
USB_MIC_A = 0.05

# motor rail, per N20 at 7.4V (amps). running != stall.
N20_RUN_A = 0.15             # light load, cruising
N20_COUNT = 2
MOTOR_DUTY = 0.6            # fraction of time actually driving while awake


def rail_current_from_battery(power_w: float, batt_v: float) -> float:
    # amps pulled from the battery to deliver power_w through the ubec
    return power_w / UBEC_EFF / batt_v


def estimate(mah: int, cells: int) -> dict:
    batt_v = CELL_NOMINAL_V * cells
    cap_ah = mah / 1000.0

    # 5V rail: convert 5V load to battery-side amps through the ubec
    five_v_amps_busy = PI_BUSY_A + CAMERA_A + USB_MIC_A
    five_v_amps_idle = PI_IDLE_A + CAMERA_A + USB_MIC_A
    pi_batt_a_busy = rail_current_from_battery(5.0 * five_v_amps_busy, batt_v)
    pi_batt_a_idle = rail_current_from_battery(5.0 * five_v_amps_idle, batt_v)

    # motor rail is battery-direct, no regulator
    motor_a_active = N20_RUN_A * N20_COUNT
    motor_a_avg = motor_a_active * MOTOR_DUTY

    # scenarios
    draw_idle = pi_batt_a_idle                      # parked, no driving
    draw_explore = pi_batt_a_busy + motor_a_avg     # wandering + vision
    draw_peak = pi_batt_a_busy + motor_a_active     # vision + both motors

    usable_ah = cap_ah * USABLE_FRACTION
    return {
        "batt_v": batt_v,
        "usable_ah": usable_ah,
        "draw_idle_a": draw_idle,
        "draw_explore_a": draw_explore,
        "draw_peak_a": draw_peak,
        "runtime_idle_h": usable_ah / draw_idle,
        "runtime_explore_h": usable_ah / draw_explore,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mah", type=int, default=1500, help="pack capacity in mAh")
    ap.add_argument("--cells", type=int, default=2, help="lipo cell count (2S = 2)")
    args = ap.parse_args()

    e = estimate(args.mah, args.cells)
    print(f"pack: {args.mah} mAh {args.cells}S  ({e['batt_v']:.1f}V nominal, "
          f"{e['usable_ah']*1000:.0f} mAh usable)\n")
    print(f"  parked (idle):     {e['draw_idle_a']:.2f} A  ->  "
          f"{e['runtime_idle_h']*60:.0f} min")
    print(f"  exploring (avg):   {e['draw_explore_a']:.2f} A  ->  "
          f"{e['runtime_explore_h']*60:.0f} min")
    print(f"  peak (both motors + vision): {e['draw_peak_a']:.2f} A")
    print()
    print("  UBEC must supply the Pi rail continuously: "
          f"{(5.0*(PI_BUSY_A+CAMERA_A+USB_MIC_A)):.1f} W "
          f"(a 5V/3A UBEC = 15W, comfortable).")
    print("  sanity: keep peak well under your pack's C-rating; any 1300+ mAh")
    print("  2S pack handles these currents easily.")


if __name__ == "__main__":
    main()
