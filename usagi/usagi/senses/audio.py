"""usb mic listener using a sounddevice callback stream.
rms loudness gate -> LOUD_SOUND event with level in db, debounced so a
sustained noise fires once. sounddevice import is inside start()."""

import math
import threading
import time

import numpy as np

from ..events import Event, EventType


class AudioSense:
    def __init__(self, cfg: dict, event_queue):
        a = cfg["audio"]
        self._rate = int(a.get("sample_rate", 16000))
        self._block = int(a.get("block_size", 1024))
        self._threshold_db = float(a.get("loudness_threshold_db", -20))
        self._cooldown = float(a.get("cooldown_s", 1.5))
        self._device = a.get("device")  # None = system default
        self._queue = event_queue
        self._last_fire = 0.0
        self._stream = None
        self._lock = threading.Lock()

    def _callback(self, indata, frames, t, status):
        # runs on portaudio's thread, keep it tiny
        rms = float(np.sqrt(np.mean(np.square(indata[:, 0]))))
        if rms <= 0:
            return
        db = 20 * math.log10(rms)
        now = time.monotonic()
        if db > self._threshold_db:
            with self._lock:
                if now - self._last_fire >= self._cooldown:
                    self._last_fire = now
                    self._queue.put(Event(EventType.LOUD_SOUND, {"level_db": db}))

    def start(self):
        import sounddevice as sd

        self._stream = sd.InputStream(
            samplerate=self._rate,
            blocksize=self._block,
            channels=1,
            dtype="float32",
            device=self._device,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self):
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
