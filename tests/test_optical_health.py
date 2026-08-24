"""Hardware-free checks for libsurvive optical-sync health monitoring."""

import ctypes
import threading
from types import SimpleNamespace

import pytest

from pika.sense import Sense
from pika.tracker import _optical_health_native
from pika.tracker.vive_tracker import (
    PoseData,
    ViveTracker,
    _LibsurviveOpticalHealthMonitor,
)


class _FakeNativeMonitor:
    def __init__(self, snapshot):
        self._snapshot = snapshot

    def snapshot(self, _window_s):
        return self._snapshot

    def scene_snapshot(self):
        return {
            "context_epoch": 3,
            "global_scene_generation": 7,
            "global_scene_count": 4,
            "lighthouses": {
                "LH0": {
                    "timestamp_s": 10.0,
                    "generation": 7,
                    "position": (1.0, 2.0, 3.0),
                    "rotation": (1.0, 0.0, 0.0, 0.0),
                }
            },
        }


class _SequencedNativeMonitor:
    def __init__(self, snapshots):
        self._snapshots = iter(snapshots)

    def snapshot(self, _window_s):
        return next(self._snapshots)


class _LiveHealthMonitor:
    def __init__(self):
        self._sequence = 100

    def scene_snapshot(self):
        return {
            "context_epoch": 1,
            "global_scene_generation": 2,
            "global_scene_count": 0,
            "lighthouses": {},
        }

    def snapshot(self, _device_name):
        self._sequence += 1
        return {
            "raw_optical_timestamp_s": 1.0,
            "raw_optical_age_s": 0.0,
            "raw_optical_measurement_count": 8,
            "raw_optical_event_sequence": self._sequence,
            "optical_timestamp_s": 1.0,
            "optical_age_s": 0.0,
            "optical_measurement_count": 8,
            "optical_lighthouse_count": 2,
            "optical_event_sequence": self._sequence,
            "pose_confidence": None,
        }


def test_native_seed_fills_only_a_missing_lighthouse_scene_slot() -> None:
    """The native bridge must preserve any newer callback-owned map entry."""
    installer_type = ctypes.CFUNCTYPE(
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
    )
    installers = [
        installer_type(lambda _context, _callback: None) for _ in range(5)
    ]
    addresses = [
        ctypes.cast(installer, ctypes.c_void_p).value for installer in installers
    ]
    context_address = 0x1234
    _optical_health_native.install(context_address, *addresses)
    try:
        assert _optical_health_native.seed_lighthouse_pose(
            0,
            (1.0, 2.0, 3.0),
            (1.0, 0.0, 0.0, 0.0),
        )
        assert not _optical_health_native.seed_lighthouse_pose(
            0,
            (9.0, 9.0, 9.0),
            (0.5, 0.5, 0.5, 0.5),
        )

        scene = _optical_health_native.scene_snapshot()
        assert scene["global_scene_generation"] == 1
        assert scene["lighthouses"]["LH0"]["position"] == (1.0, 2.0, 3.0)
    finally:
        _optical_health_native.release(context_address)


def test_native_monitor_reports_successful_global_scene_count_before_map_callback() -> None:
    """GSS progress must not disappear while map application is still pending."""
    installer_type = ctypes.CFUNCTYPE(
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p
    )
    log_callback_type = ctypes.CFUNCTYPE(
        None, ctypes.c_void_p, ctypes.c_int, ctypes.c_char_p
    )
    lighthouse_callback_type = ctypes.CFUNCTYPE(
        None, ctypes.c_void_p, ctypes.c_uint8, ctypes.c_void_p
    )
    installed_log_callback = {}
    installed_lighthouse_callback = {}

    installers = [
        installer_type(lambda _context, _callback: None) for _ in range(3)
    ]

    @installer_type
    def install_lighthouse(_context, callback):
        installed_lighthouse_callback["address"] = callback
        return None

    @installer_type
    def install_log(_context, callback):
        installed_log_callback["address"] = callback
        return None

    addresses = [
        ctypes.cast(installer, ctypes.c_void_p).value for installer in installers
    ]
    addresses.append(ctypes.cast(install_lighthouse, ctypes.c_void_p).value)
    addresses.append(ctypes.cast(install_log, ctypes.c_void_p).value)
    context_address = 0x2345

    _optical_health_native.install(context_address, *addresses)
    try:
        callback = log_callback_type(installed_log_callback["address"])
        callback(
            context_address,
            2,
            b"Global solve with 3 scenes for 0 with error of 1.0/0.1",
        )
        callback(
            context_address,
            2,
            b"Global solve with 4 scenes for 1 with error of 1.0/0.1",
        )
        pending = _optical_health_native.scene_snapshot()
        assert pending["global_scene_count"] == 4
        assert pending["applied_global_scene_count"] == 0

        lighthouse_callback = lighthouse_callback_type(
            installed_lighthouse_callback["address"]
        )
        pose = (ctypes.c_double * 7)(0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0)
        lighthouse_callback(
            context_address,
            0,
            ctypes.cast(pose, ctypes.c_void_p),
        )

        scene = _optical_health_native.scene_snapshot()
        assert scene["global_scene_count"] == 4
        assert scene["applied_global_scene_count"] == 4
    finally:
        _optical_health_native.release(context_address)


def test_snapshot_uses_sync_receipt_not_fused_pose_timestamp(monkeypatch) -> None:
    monitor = _LibsurviveOpticalHealthMonitor()
    monitor._installed = True
    monitor._native = _FakeNativeMonitor(
        (10_090_000_000, 4, 10, 10_080_000_000, 3, 2, 9)
    )
    monkeypatch.setattr("pika.tracker.vive_tracker.time.monotonic", lambda: 10.10)

    health = monitor.snapshot("T20")

    assert health is not None
    assert health["optical_timestamp_s"] == pytest.approx(10.08)
    assert health["optical_age_s"] == pytest.approx(0.02)
    assert health["optical_measurement_count"] == 3
    assert health["optical_lighthouse_count"] == 2
    assert health["pose_confidence"] is None


def test_snapshot_reports_explicit_stale_health_when_optical_events_stop(
    monkeypatch,
) -> None:
    monitor = _LibsurviveOpticalHealthMonitor()
    monitor._installed = True
    monitor._native = _FakeNativeMonitor(
        (10_080_000_000, 0, 10, 10_080_000_000, 0, 0, 9)
    )
    monkeypatch.setattr("pika.tracker.vive_tracker.time.monotonic", lambda: 10.20)

    health = monitor.snapshot("T20")

    assert health is not None
    assert health["optical_timestamp_s"] == pytest.approx(10.08)
    assert health["optical_age_s"] == pytest.approx(0.12)
    assert health["optical_measurement_count"] == 0
    assert health["optical_lighthouse_count"] == 0


def test_snapshot_keeps_stale_health_and_recovers_after_occlusion(monkeypatch) -> None:
    """A temporary optical gap must not erase the monitor's health contract."""
    monitor = _LibsurviveOpticalHealthMonitor()
    monitor._installed = True
    monitor._native = _SequencedNativeMonitor(
        [
            (10_090_000_000, 14, 20, 10_080_000_000, 12, 2, 18),
            (10_090_000_000, 0, 20, 10_080_000_000, 0, 0, 18),
            (10_315_000_000, 10, 30, 10_310_000_000, 8, 2, 26),
        ]
    )
    monotonic_times = iter([10.10, 10.20, 10.32])
    monkeypatch.setattr(
        "pika.tracker.vive_tracker.time.monotonic",
        lambda: next(monotonic_times),
    )

    healthy = monitor.snapshot("T20")
    occluded = monitor.snapshot("T20")
    recovered = monitor.snapshot("T20")

    assert healthy is not None
    assert occluded is not None
    assert occluded["optical_timestamp_s"] == pytest.approx(10.08)
    assert occluded["optical_age_s"] == pytest.approx(0.12)
    assert occluded["optical_measurement_count"] == 0
    assert occluded["optical_lighthouse_count"] == 0
    assert recovered is not None
    assert recovered["optical_timestamp_s"] == pytest.approx(10.31)
    assert recovered["optical_age_s"] == pytest.approx(0.01)
    assert recovered["optical_measurement_count"] == 8
    assert recovered["optical_lighthouse_count"] == 2


def test_snapshot_distinguishes_raw_reacquisition_from_decoded_tracking(
    monkeypatch,
) -> None:
    """Raw sensor hits must be visible before Gen2 decoding has relocked."""
    monitor = _LibsurviveOpticalHealthMonitor()
    monitor._installed = True
    monitor._native = _FakeNativeMonitor(
        (
            10_310_000_000,  # latest raw lightcap receipt
            8,               # recent raw lightcap events
            42,              # raw event sequence
            10_080_000_000,  # latest decoded sync/sweep receipt
            0,               # no recent decoded events
            0,               # no decoded Lighthouse channel yet
            27,              # decoded event sequence
        )
    )
    monkeypatch.setattr("pika.tracker.vive_tracker.time.monotonic", lambda: 10.32)

    health = monitor.snapshot("T20")

    assert health is not None
    assert health["raw_optical_timestamp_s"] == pytest.approx(10.31)
    assert health["raw_optical_age_s"] == pytest.approx(0.01)
    assert health["raw_optical_measurement_count"] == 8
    assert health["raw_optical_event_sequence"] == 42
    assert health["optical_timestamp_s"] == pytest.approx(10.08)
    assert health["optical_age_s"] == pytest.approx(0.24)
    assert health["optical_measurement_count"] == 0
    assert health["optical_lighthouse_count"] == 0
    assert health["optical_event_sequence"] == 27


def test_scene_snapshot_exposes_context_and_solved_lighthouse_facts() -> None:
    monitor = _LibsurviveOpticalHealthMonitor()
    monitor._installed = True
    monitor._native = _FakeNativeMonitor((0, 0, 0, 0, 0, 0, 0))

    scene = monitor.scene_snapshot()

    assert scene["bridge_available"] is True
    assert scene["context_epoch"] == 3
    assert scene["global_scene_generation"] == 7
    assert scene["global_scene_count"] == 4
    assert scene["lighthouses"]["LH0"]["position"] == (1.0, 2.0, 3.0)


def test_install_seeds_preloaded_lighthouse_map_without_a_new_callback() -> None:
    """A cached valid map must not depend on a post-install pose callback."""

    class _Object:
        def __init__(self, name):
            self.ptr = object()
            self._name = name

        def Name(self):
            # pysurvive declares this C API as ``c_char_p`` and therefore
            # returns bytes at the real integration boundary.
            return self._name.encode("utf-8")

    class _Native:
        def __init__(self):
            # Simulate a live callback winning the race between native hook
            # installation and cached BSD seeding for LH0.
            self.generation = 1
            self.lighthouses = {
                "LH0": {
                    "timestamp_s": 10.0,
                    "generation": 1,
                    "position": (9.0, 9.0, 9.0),
                    "rotation": (1.0, 0.0, 0.0, 0.0),
                }
            }

        def install(self, *_addresses):
            return True

        def seed_lighthouse_pose(self, index, position, rotation):
            name = f"LH{index}"
            if name in self.lighthouses:
                return False
            self.generation += 1
            self.lighthouses[name] = {
                "timestamp_s": 10.0,
                "generation": self.generation,
                "position": tuple(position),
                "rotation": tuple(rotation),
            }
            return True

        def scene_snapshot(self):
            return {
                "context_epoch": 1,
                "global_scene_generation": self.generation,
                "global_scene_count": 0,
                "lighthouses": dict(self.lighthouses),
            }

    lh0 = _Object("LH0")
    lh1 = _Object("LH1")
    lh2_unsolved = _Object("LH2")
    tracker = _Object("T20")

    def _bsd(position, rotation, *, valid=True):
        return SimpleNamespace(
            contents=SimpleNamespace(
                PositionSet=int(valid),
                Pose=SimpleNamespace(Pos=position, Rot=rotation),
            )
        )

    bsd_by_ptr = {
        lh0.ptr: _bsd((1.0, 2.0, 3.0), (1.0, 0.0, 0.0, 0.0)),
        lh1.ptr: _bsd((-1.0, 0.5, 2.0), (0.5, 0.5, 0.5, 0.5)),
        lh2_unsolved.ptr: _bsd(
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0, 0.0),
            valid=False,
        ),
    }
    native = _Native()
    monitor = _LibsurviveOpticalHealthMonitor()
    monitor._get_context = lambda _ptr: ctypes.c_void_p(0x1000)
    monitor._install_lightcap = ctypes.c_void_p(0x1001)
    monitor._install_sync = ctypes.c_void_p(0x1002)
    monitor._install_sweep = ctypes.c_void_p(0x1003)
    monitor._install_lighthouse_pose = ctypes.c_void_p(0x1004)
    monitor._install_log = ctypes.c_void_p(0x1005)
    monitor._get_lighthouse_bsd = lambda ptr: bsd_by_ptr.get(ptr)
    monitor._get_context_lock = lambda _context: None
    monitor._release_context_lock = lambda _context: None
    monitor._close_simple_context = lambda _ptr: None
    monitor._native = native
    context = type(
        "Context",
        (),
        {
            "ptr": object(),
            "Objects": lambda _self: [lh0, lh1, lh2_unsolved, tracker],
        },
    )()

    assert monitor.install(context) is True

    scene = monitor.scene_snapshot()
    assert scene["global_scene_generation"] == 2
    assert scene["global_scene_count"] == 0
    assert scene["cached_map_lighthouses"] == ("LH0", "LH1")
    assert scene["lighthouses"]["LH0"]["position"] == (9.0, 9.0, 9.0)
    assert set(scene["lighthouses"]) == {"LH0", "LH1"}
    assert scene["lighthouses"]["LH1"]["rotation"] == (0.5, 0.5, 0.5, 0.5)


def test_scene_snapshot_reconciles_map_that_becomes_valid_without_callback() -> None:
    """A delayed PositionSet update must not leave readiness at solved=[]."""

    class _Object:
        def __init__(self, name):
            self.ptr = object()
            self._name = name

        def Name(self):
            # Match the bytes returned by the real pysurvive wrapper.
            return self._name.encode("utf-8")

    class _Native:
        def __init__(self):
            self.generation = 0
            self.lighthouses = {}

        def install(self, *_addresses):
            return True

        def seed_lighthouse_pose(self, index, position, rotation):
            name = f"LH{index}"
            if name in self.lighthouses:
                return False
            self.generation += 1
            self.lighthouses[name] = {
                "timestamp_s": 10.0,
                "generation": self.generation,
                "position": tuple(position),
                "rotation": tuple(rotation),
            }
            return True

        def scene_snapshot(self):
            return {
                "context_epoch": 1,
                "global_scene_generation": self.generation,
                "global_scene_count": 3,
                "applied_global_scene_count": 0,
                "lighthouses": dict(self.lighthouses),
            }

    lighthouse = _Object("LH0")
    tracker = _Object("T20")
    bsd = SimpleNamespace(
        PositionSet=0,
        Pose=SimpleNamespace(
            Pos=(1.0, 2.0, 3.0),
            Rot=(1.0, 0.0, 0.0, 0.0),
        ),
    )
    native = _Native()
    monitor = _LibsurviveOpticalHealthMonitor()
    monitor._get_context = lambda _ptr: ctypes.c_void_p(0x2000)
    monitor._install_lightcap = ctypes.c_void_p(0x2001)
    monitor._install_sync = ctypes.c_void_p(0x2002)
    monitor._install_sweep = ctypes.c_void_p(0x2003)
    monitor._install_lighthouse_pose = ctypes.c_void_p(0x2004)
    monitor._install_log = ctypes.c_void_p(0x2005)
    monitor._get_lighthouse_bsd = lambda ptr: (
        SimpleNamespace(contents=bsd) if ptr is lighthouse.ptr else None
    )
    monitor._get_context_lock = lambda _context: None
    monitor._release_context_lock = lambda _context: None
    monitor._close_simple_context = lambda _ptr: None
    monitor._native = native
    context = type(
        "Context",
        (),
        {
            "ptr": object(),
            "Objects": lambda _self: [lighthouse, tracker],
        },
    )()

    assert monitor.install(context) is True
    assert monitor.scene_snapshot()["lighthouses"] == {}

    bsd.PositionSet = 1
    scene = monitor.scene_snapshot()

    assert scene["global_scene_count"] == 3
    assert scene["cached_map_lighthouses"] == ()
    assert scene["lighthouses"]["LH0"]["position"] == (1.0, 2.0, 3.0)


def test_scene_snapshot_fails_closed_when_native_bridge_is_not_installed() -> None:
    monitor = _LibsurviveOpticalHealthMonitor()
    monitor._installed = False
    monitor._error_reason = "missing required hook"

    scene = monitor.scene_snapshot()

    assert scene["bridge_available"] is False
    assert scene["bridge_error"] == "missing required hook"
    assert scene["context_epoch"] == 0


def test_tracking_health_refreshes_optical_facts_without_a_new_pose() -> None:
    """Health queries must not reuse optical facts frozen in cached PoseData."""
    tracker = ViveTracker.__new__(ViveTracker)
    tracker._update_device_list = lambda: None
    tracker._optical_health_monitor = _LiveHealthMonitor()
    tracker.data_lock = threading.Lock()
    tracker.devices_info = {"LH0": {}, "LH1": {}, "T20": {}}
    tracker._lighthouse_discovered_at = {"LH0": 1.0, "LH1": 1.0}
    tracker._lighthouse_cohort_generation = 2
    tracker.latest_poses = {
        "T20": PoseData(
            "T20",
            1.0,
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
            raw_optical_timestamp_s=1.0,
            raw_optical_age_s=0.0,
            raw_optical_measurement_count=1,
            raw_optical_event_sequence=7,
            optical_timestamp_s=1.0,
            optical_age_s=0.0,
            optical_measurement_count=1,
            optical_lighthouse_count=2,
            optical_event_sequence=7,
            pose_confidence=None,
        )
    }
    # This hardware-free instance is intentionally not connected.  Suppress
    # the production destructor, which owns fields irrelevant to this test.
    tracker.running = False
    tracker.context = None

    first = tracker.get_tracking_health("T20")
    second = tracker.get_tracking_health("T20")

    assert first["optical_event_sequence"] == 101
    assert second["optical_event_sequence"] == 102
    assert first["tracker_pose_timestamp_s"] == second["tracker_pose_timestamp_s"]


def test_close_releases_destroyed_context_for_a_clean_decoder_restart() -> None:
    """A new context may reuse the old address and must reinstall callbacks."""
    monitor = _LibsurviveOpticalHealthMonitor()
    monitor._installed = True
    monitor._get_context = lambda _ptr: ctypes.c_void_p(0x1234)
    closed = []
    monitor._close_simple_context = lambda ptr: closed.append(ptr)

    class _Native:
        def __init__(self):
            self.released = []

        def release(self, address):
            self.released.append(address)

    native = _Native()
    monitor._native = native
    context = type("Context", (), {"ptr": object()})()

    monitor.close(context)

    assert closed == [context.ptr]
    assert native.released == [0x1234]
    assert monitor._installed is False


def test_sense_restarts_only_the_vive_tracker_context(monkeypatch) -> None:
    sense = Sense(port="/dev/null")

    class _OldTracker:
        def __init__(self):
            self.disconnect_calls = 0

        def disconnect(self):
            self.disconnect_calls += 1
            return True

    class _NewTracker:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.connect_calls = 0

        def connect(self):
            self.connect_calls += 1
            return True

    old_tracker = _OldTracker()
    sense._vive_tracker = old_tracker
    monkeypatch.setattr("pika.tracker.vive_tracker.ViveTracker", _NewTracker)

    assert sense.restart_vive_tracker() is True
    assert old_tracker.disconnect_calls == 1
    assert isinstance(sense._vive_tracker, _NewTracker)
    assert sense._vive_tracker.connect_calls == 1
