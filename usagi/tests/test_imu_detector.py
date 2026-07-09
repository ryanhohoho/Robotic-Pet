from usagi.events import EventType
from usagi.senses.imu import ImuDetector


def _types(events):
    return [e.type for e in events]


def test_steady_1g_is_quiet(cfg):
    d = ImuDetector(cfg)
    t = 0.0
    for _ in range(100):
        assert d.update(1.0, t) == []
        t += 0.02


def test_spike_fires_bump_once(cfg):
    d = ImuDetector(cfg)
    d.update(1.0, 0.0)
    assert _types(d.update(2.5, 0.02)) == [EventType.BUMP]
    # second spike inside cooldown is swallowed
    assert d.update(2.5, 0.04) == []


def test_pickup_then_putdown(cfg):
    d = ImuDetector(cfg)
    t = 0.0
    d.update(1.0, t)
    # sustained low g -> picked up
    events = []
    for _ in range(20):
        t += 0.02
        events += d.update(0.2, t)
    assert EventType.PICKED_UP in _types(events)
    # steady 1g for a while -> put down
    events = []
    for _ in range(60):
        t += 0.02
        events += d.update(1.0, t)
    assert EventType.PUT_DOWN in _types(events)


def test_brief_dip_does_not_trigger_pickup(cfg):
    d = ImuDetector(cfg)
    d.update(1.0, 0.0)
    events = d.update(0.2, 0.02)       # one low sample only
    events += d.update(1.0, 0.04)
    assert EventType.PICKED_UP not in _types(events)


def test_no_bump_while_held(cfg):
    d = ImuDetector(cfg)
    t = 0.0
    for _ in range(20):
        t += 0.02
        d.update(0.2, t)   # get into held state
    # jostling while carried shouldn't fire bump
    t += 0.02
    assert d.update(2.5, t) == []
