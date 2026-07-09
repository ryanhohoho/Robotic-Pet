"""entry point. wires everything together:
- sensor threads (camera, audio, imu) publish to the event queue
- eye renderer runs its own thread
- brain loop runs in the main thread until SHUTDOWN

run on the pi: python -m usagi.main [config.yaml]"""

import logging
import queue
import signal
import sys

from . import config
from .brain.state_machine import Brain
from .drive.calibration import CalibratedDrive, Calibration
from .drive.motors import Drive
from .events import Event, EventType
from .face.eyes import Eyes
from .senses.audio import AudioSense
from .senses.camera import CameraSense
from .senses.imu import ImuSense

log = logging.getLogger("usagi")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    cfg = config.load(sys.argv[1] if len(sys.argv) > 1 else None)
    for w in config.validate(cfg):
        log.warning("config: %s", w)

    events: queue.Queue = queue.Queue()

    # real motors, wrapped so config.yaml calibration knobs apply globally
    drive = CalibratedDrive(Drive(cfg), Calibration.from_cfg(cfg))
    eyes = Eyes(cfg)
    senses = [CameraSense(cfg, events), AudioSense(cfg, events), ImuSense(cfg, events)]
    brain = Brain(cfg, events, drive, eyes)

    # ctrl-c or systemd stop -> clean shutdown through the event queue
    def _shutdown(signum, frame):
        events.put(Event(EventType.SHUTDOWN))

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    eyes.start()
    started = []
    for s in senses:
        try:
            s.start()
            started.append(s)
        except Exception:
            # a dead sensor shouldn't brick the whole pet, run without it
            log.exception("failed to start %s, continuing without it", type(s).__name__)

    log.info("usagi is alive, state=%s", brain.state)
    try:
        brain.run()
    finally:
        log.info("shutting down")
        for s in started:
            s.stop()
        eyes.stop()
        drive.close()


if __name__ == "__main__":
    main()
