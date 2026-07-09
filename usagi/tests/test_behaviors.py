from usagi.brain.behaviors import ExploreBehavior, IdleBehavior, ReactBehavior
from usagi.brain.behaviors.react import ROUTINES
from usagi.events import Event, EventType


def test_react_routine_runs_all_frames_then_done(cfg, drive, eyes):
    b = ReactBehavior(drive, eyes, cfg)
    b.enter(routine="face")
    total = sum(f[0] for f in ROUTINES["face"])
    # extra margin for float residue on frame boundaries
    steps = int(total / 0.05) + 10
    for _ in range(steps):
        b.tick(0.05)
    assert b.done
    assert drive.stopped


def test_react_unknown_routine_falls_back(cfg, drive, eyes):
    b = ReactBehavior(drive, eyes, cfg)
    b.enter(routine="nope")
    assert not b.done   # running the fallback, not crashed


def test_idle_glances_at_motion_then_returns(cfg, drive, eyes):
    b = IdleBehavior(drive, eyes, cfg)
    b.enter()
    assert eyes.state == "idle"
    b.handle_event(Event(EventType.MOTION_DETECTED))
    assert eyes.state == "look"
    for _ in range(40):
        b.tick(0.05)
    assert eyes.state == "idle"


def test_explore_cruises_forward_and_avoids(cfg, drive, eyes):
    b = ExploreBehavior(drive, eyes, cfg)
    b.enter()
    b.tick(0.05)
    assert drive.speeds[0] > 0 and drive.speeds[1] > 0
    b.handle_event(Event(EventType.OBSTACLE_NEAR, {"density": 0.5}))
    b.tick(0.05)
    assert drive.speeds[0] < 0 and drive.speeds[1] < 0   # backing
    b.exit()
    assert drive.stopped
