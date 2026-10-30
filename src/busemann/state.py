"""Single application state: inputs, latest results, and the debounced recompute pipeline.

Views change inputs through AppState.update() and listen to its signals; they never call
the core. Freestream is cheap (< 1 ms) and computed on the UI thread; design (~13 ms for the
Oswatitsch optimiser) and the optional off-design point run on a worker thread so the UI
never blocks. Only the newest request's result is used (generation counter).
"""
import dataclasses
import time
from dataclasses import dataclass

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal

from inletdesign import api

from .theme import tokens


@dataclass(frozen=True)
class Inputs:
    mach: float = 3.0
    atmosphere_mode: str = "altitude"   # "altitude" | "manual"
    altitude_m: float = 20000.0
    p_pa: float = 10000.0
    T_k: float = 220.0
    gamma: float = 1.4
    n_ramps: int = 2
    method: str = "oswatitsch"          # "oswatitsch" | "custom"
    custom_angles: tuple = ()
    capture_height_m: float = 0.1
    units: str = "SI"                   # "SI" | "Imperial"
    preset: str = None                  # name of the applied preset, None once edited
    off_design_mach: float = None       # evaluate the frozen design at this Mach (M4 slider)
    max_cowl_enabled: bool = False      # limit the Oswatitsch optimum's cowl angle
    max_cowl_deg: float = 30.0


# Fields that do not change any computed result.
_DISPLAY_ONLY = {"units", "preset"}


class _WorkerSignals(QObject):
    # generation, DesignResult|None, error|None, OffDesignResult|None, off error|None, ms
    done = Signal(int, object, object, object, object, float)


class _DesignJob(QRunnable):
    def __init__(self, generation, state, inputs):
        super().__init__()
        self.generation, self.state, self.inputs = generation, state, inputs
        self.signals = _WorkerSignals()

    def run(self):
        if self.generation != self.state._generation:   # superseded while queued: skip work
            self.signals.done.emit(self.generation, None, None, None, None, 0.0)
            return
        i = self.inputs
        t0 = time.perf_counter()
        try:
            result = api.design(
                i.mach, i.n_ramps, capture_height=i.capture_height_m, gamma=i.gamma,
                ramp_angles=list(i.custom_angles) if i.method == "custom" else None,
                max_cowl_angle=(i.max_cowl_deg if i.max_cowl_enabled and i.method != "custom"
                                else None),
            )
            error = None
        except ValueError as exc:
            result, error = None, str(exc)
        off, off_error = None, None
        if result is not None and i.off_design_mach is not None:
            try:
                off = api.off_design_point(result, i.off_design_mach)
            except ValueError as exc:
                off_error = str(exc)
        self.signals.done.emit(self.generation, result, error, off, off_error,
                               (time.perf_counter() - t0) * 1000.0)


class AppState(QObject):
    inputs_changed = Signal(object)            # Inputs
    freestream_ready = Signal(object, object)  # Freestream|None, error|None
    design_ready = Signal(object, object)      # DesignResult|None, error|None
    busy_changed = Signal(bool)
    compute_time_changed = Signal(float)       # ms, freestream + design of the last result

    def __init__(self, inputs=None, parent=None):
        super().__init__(parent)
        self._inputs = inputs or Inputs()
        self.freestream = None
        self.freestream_error = None
        self.design = None
        self.design_error = None
        self.off_design = None
        self.off_design_error = None
        self.compute_ms = None
        self._fs_ms = 0.0
        self._generation = 0
        self._busy = False
        self._jobs = {}

        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(tokens.DEBOUNCE_MS)
        self._timer.timeout.connect(self.recompute_now)

    # --- inputs ---------------------------------------------------------
    @property
    def inputs(self):
        return self._inputs

    def update(self, **changes):
        """Change inputs; schedules a debounced recompute unless only display fields changed."""
        new = dataclasses.replace(self._inputs, **changes)
        if new == self._inputs:
            return
        self._inputs = new
        self.inputs_changed.emit(new)
        if set(changes) - _DISPLAY_ONLY:
            self._timer.start()

    # --- derived quantities ---------------------------------------------
    def captured_mass_flow(self):
        if self.freestream is None or self.design is None:
            return None
        return api.captured_mass_flow(self.freestream, self._inputs.capture_height_m,
                                      self.design.mass_capture)

    def notices(self):
        """(level, text) for every current model-limit message: "warn" or "error"."""
        out = []
        if self.freestream is not None:
            out.extend(("warn", w) for w in self.freestream.warnings)
        for result in (self.design, self.off_design):
            if result is not None:
                out.extend((n.level, n.text) for n in result.notices)
        return out

    def warnings(self):
        out = []
        if self.freestream is not None:
            out.extend(self.freestream.warnings)
        if self.design is not None:
            out.extend(self.design.warnings)
        return out

    def is_busy(self):
        return self._busy

    # --- pipeline -------------------------------------------------------
    def recompute_now(self):
        self._timer.stop()
        i = self._inputs
        t0 = time.perf_counter()
        try:
            if i.atmosphere_mode == "altitude":
                fs = api.freestream(i.mach, altitude_m=i.altitude_m, gamma=i.gamma)
            else:
                fs = api.freestream(i.mach, p=i.p_pa, T=i.T_k, gamma=i.gamma)
            self.freestream, self.freestream_error = fs, None
        except ValueError as exc:
            self.freestream, self.freestream_error = None, str(exc)
        self._fs_ms = (time.perf_counter() - t0) * 1000.0
        self.freestream_ready.emit(self.freestream, self.freestream_error)

        self._generation += 1
        job = _DesignJob(self._generation, self, i)
        job.signals.done.connect(self._on_design_done)
        self._jobs[self._generation] = job   # keep signals alive until delivered
        self._set_busy(True)
        self._pool.start(job)

    def _on_design_done(self, generation, result, error, off, off_error, ms):
        self._jobs.pop(generation, None)
        if generation != self._generation:
            return
        self.design, self.design_error = result, error
        self.off_design, self.off_design_error = off, off_error
        self.compute_ms = self._fs_ms + ms
        self._set_busy(False)
        self.design_ready.emit(result, error)
        self.compute_time_changed.emit(self.compute_ms)

    def _set_busy(self, busy):
        if busy != self._busy:
            self._busy = busy
            self.busy_changed.emit(busy)

    def shutdown(self):
        self._timer.stop()
        self._generation += 1
        self._pool.waitForDone(2000)
