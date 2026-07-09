from usagi.brain.state_machine import Brain
from usagi.events import Event, EventType


def make_brain(cfg, events, drive, eyes):
    return Brain(cfg, events, drive, eyes)


def test_starts_sleeping_with_eyes_closed(cfg, events, drive, eyes):
    brain = make_brain(cfg, events, drive, eyes)
    assert brain.state == "sleeping"
    assert eyes.state == "closed"
    assert drive.stopped


def test_loud_sound_wakes_from_sleep(cfg, events, drive, eyes):
    brain = make_brain(cfg, events, drive, eyes)
    brain._dispatch(Event(EventType.LOUD_SOUND, {"level_db": -10}))
    assert brain.state == "idle"


def test_other_events_do_not_wake(cfg, events, drive, eyes):
    brain = make_brain(cfg, events, drive, eyes)
    brain._dispatch(Event(EventType.MOTION_DETECTED))
    brain._dispatch(Event(EventType.FACE_DETECTED, {"x_offset": 0.0}))
    assert brain.state == "sleeping"


def test_stimulus_in_idle_starts_reacting(cfg, events, drive, eyes):
    brain = make_brain(cfg, events, drive, eyes)
    brain.wake()
    brain._dispatch(Event(EventType.FACE_DETECTED, {"x_offset": 0.1}))
    assert brain.state == "reacting"


def test_react_routine_finishes_back_to_idle(cfg, events, drive, eyes):
    brain = make_brain(cfg, events, drive, eyes)
    brain.wake()
    brain._dispatch(Event(EventType.LOUD_SOUND, {"level_db": -5}))
    assert brain.state == "reacting"
    # tick past the whole routine
    for _ in range(200):
        brain._behavior.tick(0.05)
    assert brain._behavior.done
    brain.finished()
    assert brain.state == "idle"


def test_pickup_overrides_everything_and_stops_motors(cfg, events, drive, eyes):
    brain = make_brain(cfg, events, drive, eyes)
    brain.wake()
    brain.bored()
    assert brain.state == "exploring"
    drive.move(0.5, 0.5)
    brain._dispatch(Event(EventType.PICKED_UP))
    assert brain.state == "held"
    assert drive.stopped
    assert eyes.state == "react" and eyes.params["emotion"] == "worried"


def test_putdown_returns_to_idle(cfg, events, drive, eyes):
    brain = make_brain(cfg, events, drive, eyes)
    brain._dispatch(Event(EventType.PICKED_UP))
    brain._dispatch(Event(EventType.PUT_DOWN))
    assert brain.state == "idle"


def test_putdown_ignored_when_not_held(cfg, events, drive, eyes):
    brain = make_brain(cfg, events, drive, eyes)
    brain.wake()
    brain._dispatch(Event(EventType.PUT_DOWN))
    assert brain.state == "idle"


def test_bump_in_exploring_triggers_avoid_not_routine(cfg, events, drive, eyes):
    brain = make_brain(cfg, events, drive, eyes)
    brain.wake()
    brain.bored()
    brain._dispatch(Event(EventType.BUMP, {"g": 2.2}))
    assert brain.state == "exploring"   # stays exploring, avoid maneuver
    brain._behavior.tick(0.05)
    assert drive.speeds[0] < 0          # backing up


def test_shutdown_stops_loop_flag(cfg, events, drive, eyes):
    brain = make_brain(cfg, events, drive, eyes)
    brain._running = True
    brain._dispatch(Event(EventType.SHUTDOWN))
    assert brain._running is False
