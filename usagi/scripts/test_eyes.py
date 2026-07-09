#!/usr/bin/env python3
"""eye bring-up: init both oleds, cycle through every animation state.
run from repo root: python scripts/test_eyes.py"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from usagi import config
from usagi.face.eyes import Eyes


def main():
    eyes = Eyes(config.load())
    eyes.start()
    try:
        for state, params, hold in [
            ("idle", {}, 5.0),
            ("blink", {}, 1.0),
            ("look", {"direction": -0.8}, 2.0),
            ("look", {"direction": 0.8}, 2.0),
            ("react", {"emotion": "happy"}, 2.0),
            ("react", {"emotion": "surprised"}, 2.0),
            ("react", {"emotion": "worried"}, 3.0),
            ("closed", {}, 2.0),
        ]:
            print(f"state: {state} {params}")
            eyes.set_state(state, **params)
            time.sleep(hold)
        print("done")
    finally:
        eyes.stop()


if __name__ == "__main__":
    main()
