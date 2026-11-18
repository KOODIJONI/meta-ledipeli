"""
gpio_buttons.py - interrupt-driven GPIO button library for Raspberry Pi (libgpiod v2).

Buttons are assumed to be wired between the GPIO and GND (internal pull-up
enabled), so a falling edge = pressed and a rising edge = released.

A background thread sleeps in the kernel until an edge event arrives and then
calls your callbacks. No polling.
"""

import threading
from datetime import timedelta

import gpiod
from gpiod.line import Bias, Direction, Edge

PRESSED = "pressed"
RELEASED = "released"


class ButtonListener:
    def __init__(
        self,
        pins,
        chip_path="/dev/gpiochip0",
        pull_up=True,
        debounce_ms=20,
        consumer="button-listener",
    ):

        self.pins = list(pins)
        self.chip_path = chip_path
        self.pull_up = pull_up
        self.debounce_ms = debounce_ms
        self.consumer = consumer

        self._callbacks = {}
        self._request = None
        self._thread = None
        self._stop = threading.Event()

    def on(self, pin, callback, event=PRESSED):
        """Register callback(pin) for a pin. event is PRESSED or RELEASED."""
        if pin not in self.pins:
            raise ValueError(f"GPIO {pin} is not in the listener's pin list")
        self._add(pin, event, callback)

    def on_any(self, callback, event=PRESSED):
        """Register callback(pin) that fires for every pin."""
        self._add(None, event, callback)

    def pressed(self, pin):
        """Decorator form: @buttons.pressed(4)"""
        def deco(fn):
            self.on(pin, fn, PRESSED)
            return fn
        return deco

    def released(self, pin):
        """Decorator form: @buttons.released(4)"""
        def deco(fn):
            self.on(pin, fn, RELEASED)
            return fn
        return deco

    def _add(self, pin, event, callback):
        if event not in (PRESSED, RELEASED):
            raise ValueError("event must be PRESSED or RELEASED")
        self._callbacks.setdefault(pin, {}).setdefault(event, []).append(callback)

    def start(self):
        if self._thread is not None:
            return
        settings = gpiod.LineSettings(
            direction=Direction.INPUT,
            bias=Bias.PULL_UP if self.pull_up else Bias.PULL_DOWN,
            edge_detection=Edge.BOTH,
            debounce_period=timedelta(milliseconds=self.debounce_ms),
        )
        self._request = gpiod.request_lines(
            self.chip_path,
            consumer=self.consumer,
            config={pin: settings for pin in self.pins},
        )
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="gpio-buttons", daemon=True)
        self._thread.start()

    def stop(self):
        if self._thread is None:
            return
        self._stop.set()
        self._thread.join()
        self._thread = None
        self._request.release()
        self._request = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()

    def _run(self):
        while not self._stop.is_set():
            if not self._request.wait_edge_events(timedelta(milliseconds=200)):
                continue
            for ev in self._request.read_edge_events():
                pressed_edge = (
                    ev.event_type == ev.Type.FALLING_EDGE
                    if self.pull_up
                    else ev.event_type == ev.Type.RISING_EDGE
                )
                self._dispatch(ev.line_offset, PRESSED if pressed_edge else RELEASED)

    def _dispatch(self, pin, event):
        handlers = (
            self._callbacks.get(pin, {}).get(event, [])
            + self._callbacks.get(None, {}).get(event, [])
        )
        for cb in handlers:
            try:
                cb(pin)
            except Exception as exc: 
                print(f"[gpio_buttons] callback error on GPIO {pin}: {exc!r}")