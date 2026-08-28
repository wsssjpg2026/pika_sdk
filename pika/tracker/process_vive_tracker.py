"""Process-isolated Vive Tracker backend.

libsurvive owns native worker threads and, after some optical stalls,
``survive_simple_close`` can wait forever.  Python cannot safely stop a thread
blocked in that C call.  This module therefore makes the operating-system
process the lifetime boundary for a tracker context: normal calls use a small
Pipe RPC, while restart can always terminate the old worker and create a fresh
one without disturbing the Pika serial connection in the parent process.
"""

import logging
import multiprocessing
import threading
import time
from multiprocessing.connection import Connection
from typing import Any, Callable, Dict, List, Optional


logger = logging.getLogger("pika.process_vive_tracker")


class TrackerProcessError(RuntimeError):
    """The isolated tracker worker could not service a request."""


def _tracker_process_main(
    connection: Connection,
    tracker_kwargs: Dict[str, Any],
    backend_factory: Optional[Callable[..., Any]],
) -> None:
    """Own one libsurvive context and serve its small public API."""
    backend = None
    try:
        if backend_factory is None:
            # Import only in the child.  In particular, the parent never owns
            # a pysurvive context or a native libsurvive worker thread.
            from .vive_tracker import ViveTracker

            backend_factory = ViveTracker
        backend = backend_factory(**tracker_kwargs)
        connected = bool(backend.connect())
        connection.send(("ready", connected, None))
        if not connected:
            return

        while True:
            request_id, method, args, kwargs = connection.recv()
            if method == "__shutdown__":
                # Acknowledge before native shutdown.  If disconnect wedges,
                # the parent still owns a bounded grace period and can kill
                # this entire process.
                connection.send((request_id, True, True))
                break
            try:
                result = getattr(backend, method)(*args, **kwargs)
                connection.send((request_id, True, result))
            except BaseException as exc:
                connection.send(
                    (
                        request_id,
                        False,
                        f"{type(exc).__name__}: {exc}",
                    )
                )
    except EOFError:
        pass
    except BaseException as exc:
        try:
            connection.send(("ready", False, f"{type(exc).__name__}: {exc}"))
        except BaseException:
            pass
    finally:
        if backend is not None:
            try:
                backend.disconnect()
            except BaseException:
                logger.exception("Tracker backend shutdown failed")
        try:
            connection.close()
        except BaseException:
            pass


class IsolatedViveTracker:
    """A :class:`ViveTracker`-compatible proxy backed by a child process."""

    def __init__(
        self,
        config_path: Optional[str] = None,
        lh_config: Optional[str] = None,
        args: Optional[List[str]] = None,
        product: str = "sense",
        *,
        backend_factory: Optional[Callable[..., Any]] = None,
        process_context=None,
        startup_timeout_s: float = 10.0,
        rpc_timeout_s: float = 0.5,
        shutdown_grace_s: float = 0.5,
    ) -> None:
        self._tracker_kwargs = {
            "config_path": config_path,
            "lh_config": lh_config,
            "args": args,
            "product": product,
        }
        self._backend_factory = backend_factory
        self._process_context = process_context or multiprocessing.get_context(
            "spawn"
        )
        self._startup_timeout_s = float(startup_timeout_s)
        self._rpc_timeout_s = float(rpc_timeout_s)
        self._shutdown_grace_s = float(shutdown_grace_s)
        self._lock = threading.RLock()
        self._process = None
        self._connection = None  # type: Optional[Connection]
        self._next_request_id = 1
        self._last_error_log_monotonic = 0.0

    @property
    def worker_pid(self) -> Optional[int]:
        with self._lock:
            return None if self._process is None else self._process.pid

    @property
    def running(self) -> bool:
        with self._lock:
            return bool(self._process is not None and self._process.is_alive())

    def connect(self) -> bool:
        with self._lock:
            if self._process is not None and self._process.is_alive():
                return True
            self._stop_worker_locked(graceful=False)
            return self._start_worker_locked()

    def restart(self) -> bool:
        """Replace the tracker process without trusting native teardown."""
        with self._lock:
            if not self._stop_worker_locked(graceful=True):
                return False
            restarted = self._start_worker_locked()
            if restarted:
                logger.warning(
                    "Vive Tracker decoder worker process restarted (pid=%s)",
                    self._process.pid,
                )
            return restarted

    def disconnect(self) -> bool:
        with self._lock:
            return self._stop_worker_locked(graceful=True)

    def get_pose(self, device_name=None):
        try:
            return self._request("get_pose", device_name)
        except TrackerProcessError as exc:
            self._log_request_error(exc)
            return None if device_name else {}

    def get_devices(self) -> List[str]:
        try:
            return list(self._request("get_devices"))
        except TrackerProcessError as exc:
            self._log_request_error(exc)
            return []

    def get_tracking_health(self, device_name=None) -> Dict[str, Any]:
        try:
            result = self._request("get_tracking_health", device_name)
            return result if isinstance(result, dict) else self._unavailable_health(
                "tracker worker returned invalid health data"
            )
        except TrackerProcessError as exc:
            self._log_request_error(exc)
            return self._unavailable_health(str(exc))

    def lock_global_scene(self) -> bool:
        try:
            return bool(self._request("lock_global_scene"))
        except TrackerProcessError as exc:
            self._log_request_error(exc)
            return False

    def _start_worker_locked(self) -> bool:
        parent_connection, child_connection = self._process_context.Pipe(
            duplex=True
        )
        process = self._process_context.Process(
            target=_tracker_process_main,
            args=(
                child_connection,
                self._tracker_kwargs,
                self._backend_factory,
            ),
            name="pika-vive-tracker",
            daemon=True,
        )
        self._connection = parent_connection
        self._process = process
        try:
            process.start()
        except BaseException:
            logger.exception("Failed to start Vive Tracker worker process")
            self._close_parent_connection_locked()
            self._process = None
            return False
        finally:
            child_connection.close()

        if not parent_connection.poll(self._startup_timeout_s):
            logger.error(
                "Vive Tracker worker did not initialize within %.1fs",
                self._startup_timeout_s,
            )
            self._stop_worker_locked(graceful=False)
            return False
        try:
            kind, ready, detail = parent_connection.recv()
        except (EOFError, OSError):
            logger.exception("Vive Tracker worker exited during initialization")
            self._stop_worker_locked(graceful=False)
            return False
        if kind != "ready" or not ready:
            logger.error("Vive Tracker worker initialization failed: %s", detail)
            self._stop_worker_locked(graceful=False)
            return False
        logger.info("Vive Tracker worker process ready (pid=%s)", process.pid)
        return True

    def _stop_worker_locked(self, *, graceful: bool) -> bool:
        process = self._process
        connection = self._connection
        if process is None:
            self._close_parent_connection_locked()
            return True

        if process.is_alive() and graceful and connection is not None:
            request_id = self._next_request_id
            self._next_request_id += 1
            try:
                connection.send((request_id, "__shutdown__", (), {}))
                # The acknowledgement precedes native teardown.  Receiving it
                # is useful diagnostics, but process exit remains authoritative.
                if connection.poll(min(0.2, self._shutdown_grace_s)):
                    connection.recv()
            except (EOFError, OSError, BrokenPipeError):
                pass

        if process.is_alive():
            process.join(timeout=self._shutdown_grace_s if graceful else 0.0)
        if process.is_alive():
            logger.warning(
                "Terminating unresponsive Vive Tracker worker process (pid=%s)",
                process.pid,
            )
            process.terminate()
            process.join(timeout=1.0)
        if process.is_alive() and hasattr(process, "kill"):
            logger.error(
                "Killing Vive Tracker worker process that ignored SIGTERM "
                "(pid=%s)",
                process.pid,
            )
            process.kill()
            process.join(timeout=1.0)

        stopped = not process.is_alive()
        if not stopped:
            logger.error(
                "Unable to stop Vive Tracker worker process pid=%s", process.pid
            )
        self._close_parent_connection_locked()
        if stopped:
            try:
                process.close()
            except (ValueError, OSError):
                pass
            self._process = None
        return stopped

    def _request(self, method: str, *args, **kwargs):
        with self._lock:
            process = self._process
            connection = self._connection
            if (
                process is None
                or connection is None
                or not process.is_alive()
            ):
                raise TrackerProcessError("tracker worker process is unavailable")
            request_id = self._next_request_id
            self._next_request_id += 1
            try:
                connection.send((request_id, method, args, kwargs))
            except (EOFError, OSError, BrokenPipeError) as exc:
                raise TrackerProcessError(
                    f"failed to send {method} to tracker worker: {exc}"
                ) from exc

            deadline = time.monotonic() + self._rpc_timeout_s
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0.0 or not connection.poll(remaining):
                    raise TrackerProcessError(
                        f"tracker worker {method} timed out after "
                        f"{self._rpc_timeout_s:.1f}s"
                    )
                try:
                    response_id, succeeded, payload = connection.recv()
                except (EOFError, OSError) as exc:
                    raise TrackerProcessError(
                        f"tracker worker exited during {method}: {exc}"
                    ) from exc
                # Discard a late response from a previously timed-out request.
                if response_id != request_id:
                    continue
                if not succeeded:
                    raise TrackerProcessError(
                        f"tracker worker {method} failed: {payload}"
                    )
                return payload

    def _close_parent_connection_locked(self) -> None:
        connection = self._connection
        self._connection = None
        if connection is not None:
            try:
                connection.close()
            except OSError:
                pass

    def _log_request_error(self, exc: BaseException) -> None:
        now = time.monotonic()
        if now - self._last_error_log_monotonic >= 1.0:
            self._last_error_log_monotonic = now
            logger.error("Vive Tracker worker request failed: %s", exc)

    @staticmethod
    def _unavailable_health(reason: str) -> Dict[str, Any]:
        return {
            "bridge_available": False,
            "bridge_error": reason,
            "context_epoch": 0,
            "global_scene_generation": 0,
            "global_scene_count": 0,
            "cached_map_lighthouses": (),
            "lighthouses": {},
            "discovered_lighthouses": (),
        }

    def __del__(self):
        try:
            self.disconnect()
        except BaseException:
            pass
