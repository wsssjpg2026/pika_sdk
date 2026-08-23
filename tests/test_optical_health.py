"""Hardware-free checks for libsurvive optical-sync health monitoring."""

import ctypes
import threading

import pytest

from pika.sense import Sense
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
