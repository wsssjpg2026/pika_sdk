#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vive Tracker module - based on pysurvive library
Provides access interface for Vive Tracker device pose data
"""

import sys
import time
import os
import signal
import math
import threading
import queue
import logging
import numpy as np 
from .pose_utils import xyzQuaternion2matrix, xyzrpy2Mat, matrixToXYZQuaternion

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('pika.vive_tracker')

# Product-specific pose transforms applied after the raw tracker pose.
# Sense: rotate then translate to gripper center.
# Ego: translation only (+X 33.27 mm, -Z 39 mm).
PRODUCT_TRANSFORMS = {
    'sense': {
        'apply_rotation': True,
        'translation': (0.172, 0.0, -0.076),
    },
    'ego': {
        'apply_rotation': False,
        'translation': (0.03327, 0.0, -0.039),
    },
}

# Import pysurvive library
try:
    import pysurvive
except ImportError:
    logger.error("pysurvive library not found, please ensure it is properly installed")
    raise ImportError("pysurvive library not found, please ensure it is properly installed")

class PoseData:
    """Pose data structure for storing and formatting pose information"""
    def __init__(
        self,
        device_name,
        timestamp,
        position,
        rotation,
        *,
        optical_timestamp_s=None,
        optical_age_s=None,
        optical_measurement_count=None,
        optical_lighthouse_count=None,
        raw_optical_timestamp_s=None,
        raw_optical_age_s=None,
        raw_optical_measurement_count=None,
        raw_optical_event_sequence=None,
        optical_event_sequence=None,
        pose_confidence=None,
    ):
        self.device_name = device_name
        self.timestamp = timestamp
        self.position = position  # [x, y, z]
        self.rotation = rotation  # [x, y, z, w] quaternion
        # ``timestamp`` is the latest fused pose time and advances from IMU
        # reports even while the tracker is optically occluded.  These fields
        # are a snapshot of libsurvive's actual light observations, allowing
        # safety-critical consumers to distinguish optical tracking from
        # inertial prediction.
        self.optical_timestamp_s = optical_timestamp_s
        self.optical_age_s = optical_age_s
        self.optical_measurement_count = optical_measurement_count
        self.optical_lighthouse_count = optical_lighthouse_count
        # Raw lightcap hits prove that Tracker photodiodes can see Lighthouse
        # light even while Gen2 sync/sweep decoding is still reacquiring.
        self.raw_optical_timestamp_s = raw_optical_timestamp_s
        self.raw_optical_age_s = raw_optical_age_s
        self.raw_optical_measurement_count = raw_optical_measurement_count
        self.raw_optical_event_sequence = raw_optical_event_sequence
        self.optical_event_sequence = optical_event_sequence
        self.pose_confidence = pose_confidence

    def __str__(self):
        """Format and output pose information"""
        return f"{self.device_name}: T: {self.timestamp:.6f} P: {self.position[0]:9.6f}, {self.position[1]:9.6f}, {self.position[2]:9.6f} R: {self.rotation[0]:9.6f}, {self.rotation[1]:9.6f}, {self.rotation[2]:9.6f}, {self.rotation[3]:9.6f}"


class _LibsurviveOpticalHealthMonitor:
    """Observe raw lightcap and decoded sync/sweep callbacks through a C bridge.

    ``Pose()`` is fused IMU output, so its timestamp continues through an
    optical occlusion.  The bridge hooks libsurvive's public raw lightcap and
    decoded sync/sweep callbacks, chains their existing C handlers, and records
    only C11 atomics.  Raw lightcap hits expose physical reacquisition before
    the Gen2 decoder emits trustworthy sync/sweep events.  Python merely polls
    snapshots from its normal worker thread, avoiding callbacks from a native
    libsurvive thread into the Python interpreter.
    """

    _WINDOW_S = 0.1

    def __init__(self):
        self._installed = False
        self._get_context = None
        self._install_lightcap = None
        self._install_sync = None
        self._install_sweep = None
        self._install_lighthouse_pose = None
        self._get_lighthouse_bsd = None
        self._close_simple_context = None
        self._native = None
        self._error_reason = None
        self._had_recent_raw_optical_events = None
        self._had_recent_optical_events = None
        try:
            from . import _optical_health_native as native
            from pysurvive import pysurvive_generated as generated

            lib = generated._libs["survive"]
            get_context = lib.get("survive_simple_get_ctx", "cdecl")
            get_context.argtypes = [generated.POINTER(generated.SurviveSimpleContext)]
            get_context.restype = generated.POINTER(generated.SurviveContext)
            self._get_context = get_context
            self._install_lightcap = lib.get("survive_install_lightcap_fn", "cdecl")
            self._install_sync = lib.get("survive_install_sync_fn", "cdecl")
            self._install_sweep = lib.get("survive_install_sweep_fn", "cdecl")
            self._install_lighthouse_pose = lib.get(
                "survive_install_lighthouse_pose_fn", "cdecl"
            )
            get_lighthouse_bsd = lib.get("survive_simple_get_bsd", "cdecl")
            get_lighthouse_bsd.argtypes = [
                generated.POINTER(generated.SurviveSimpleObject)
            ]
            get_lighthouse_bsd.restype = generated.POINTER(
                generated.BaseStationData
            )
            self._get_lighthouse_bsd = get_lighthouse_bsd
            self._close_simple_context = generated.survive_simple_close
            if not hasattr(native, "seed_lighthouse_pose"):
                raise RuntimeError(
                    "outdated pika optical native extension; reinstall "
                    "agx-pypika to rebuild _optical_health_native"
                )
            self._native = native
        except Exception as exc:
            self._error_reason = str(exc)
            logger.error(
                "native libsurvive optical monitor unavailable; pose consumers "
                "must not treat fused timestamps as optical freshness: %s",
                exc,
            )

    @property
    def available(self):
        return (
            self._get_context is not None
            and self._install_lightcap is not None
            and self._install_sync is not None
            and self._install_sweep is not None
            and self._install_lighthouse_pose is not None
            and self._get_lighthouse_bsd is not None
            and self._close_simple_context is not None
            and self._native is not None
        )

    def install(self, simple_context):
        if os.environ.get("PIKA_DISABLE_OPTICAL_HEALTH") == "1":
            logger.warning("libsurvive optical monitor disabled by environment")
            return False
        if not self.available or simple_context is None:
            return False
        try:
            full_context = self._get_context(simple_context.ptr)
            if not full_context:
                return False
            import ctypes

            context_address = ctypes.cast(full_context, ctypes.c_void_p).value
            lightcap_installer_address = ctypes.cast(
                self._install_lightcap, ctypes.c_void_p
            ).value
            installer_address = ctypes.cast(
                self._install_sync, ctypes.c_void_p
            ).value
            sweep_installer_address = ctypes.cast(
                self._install_sweep, ctypes.c_void_p
            ).value
            lighthouse_pose_installer_address = ctypes.cast(
                self._install_lighthouse_pose, ctypes.c_void_p
            ).value
            self._native.install(
                context_address,
                lightcap_installer_address,
                installer_address,
                sweep_installer_address,
                lighthouse_pose_installer_address,
            )
            seeded_lighthouses = self._seed_existing_lighthouse_scene(
                simple_context
            )
            self._installed = True
            logger.info(
                "native libsurvive optical + global-scene monitor installed; "
                "seeded cached map=%s",
                seeded_lighthouses or "none",
            )
            return True
        except Exception as exc:
            self._error_reason = str(exc)
            logger.error("Failed to install libsurvive optical monitor: %s", exc)
            return False

    def _seed_existing_lighthouse_scene(self, simple_context):
        """Import valid map entries loaded before native hooks were installed.

        ``SimpleContext`` loads persisted Lighthouse poses during construction,
        before this monitor can register its callback.  Only ``PositionSet``
        entries are authoritative.  The native bridge fills an empty slot only,
        so a callback that races with this snapshot always wins.
        """
        seeded = []
        for simple_object in simple_context.Objects():
            name = str(simple_object.Name())
            if not name.startswith("LH") or not name[2:].isdigit():
                continue
            bsd_pointer = self._get_lighthouse_bsd(simple_object.ptr)
            if not bsd_pointer or not bool(bsd_pointer.contents.PositionSet):
                continue
            pose = bsd_pointer.contents.Pose
            position = tuple(float(value) for value in pose.Pos)
            rotation = tuple(float(value) for value in pose.Rot)
            if self._native.seed_lighthouse_pose(
                int(name[2:]), position, rotation
            ):
                seeded.append(name)
        return tuple(sorted(seeded))

    @property
    def error_reason(self):
        return self._error_reason

    def close(self, simple_context):
        """Stop/destroy a SimpleContext and release the native hook identity."""
        if simple_context is None:
            return
        full_context_address = None
        closed = False
        try:
            if self._get_context is not None:
                import ctypes

                full_context = self._get_context(simple_context.ptr)
                if full_context:
                    full_context_address = ctypes.cast(
                        full_context, ctypes.c_void_p
                    ).value
            if self._close_simple_context is None:
                raise RuntimeError("survive_simple_close is unavailable")
            self._close_simple_context(simple_context.ptr)
            closed = True
        finally:
            # release() is only safe after the context's own thread is gone.
            if (
                closed
                and full_context_address is not None
                and self._native is not None
                and hasattr(self._native, "release")
            ):
                self._native.release(full_context_address)
            if closed:
                self._installed = False
                self._had_recent_raw_optical_events = None
                self._had_recent_optical_events = None

    def snapshot(self, _device_name):
        if not self._installed:
            return None
        snapshot = self._native.snapshot(self._WINDOW_S)
        if len(snapshot) != 7:
            raise RuntimeError(
                "outdated pika optical native extension; reinstall agx-pypika "
                "to rebuild _optical_health_native"
            )
        (
            raw_latest_ns,
            raw_measurement_count,
            raw_event_sequence,
            latest_ns,
            measurement_count,
            lighthouse_count,
            optical_event_sequence,
        ) = snapshot
        now = time.monotonic()
        last_raw_s = raw_latest_ns / 1_000_000_000.0
        last_sync_s = latest_ns / 1_000_000_000.0
        has_recent_raw_events = raw_measurement_count > 0
        if has_recent_raw_events != self._had_recent_raw_optical_events:
            self._had_recent_raw_optical_events = has_recent_raw_events
            if has_recent_raw_events:
                logger.info(
                    "Lighthouse raw light available: events=%d",
                    raw_measurement_count,
                )
            elif raw_latest_ns > 0:
                logger.warning(
                    "Lighthouse raw light stopped; last sensor hit was %.0fms ago",
                    max(0.0, now - last_raw_s) * 1000.0,
                )
        has_recent_events = measurement_count > 0
        if has_recent_events != self._had_recent_optical_events:
            self._had_recent_optical_events = has_recent_events
            if has_recent_events:
                logger.info(
                    "Lighthouse optical measurements available: "
                    "events=%d channels=%d",
                    measurement_count,
                    lighthouse_count,
                )
            elif latest_ns > 0:
                logger.warning(
                    "Lighthouse optical measurements stopped; last event "
                    "was %.0fms ago",
                    max(0.0, now - last_sync_s) * 1000.0,
                )
        return {
            "raw_optical_timestamp_s": last_raw_s,
            "raw_optical_age_s": max(0.0, now - last_raw_s),
            "raw_optical_measurement_count": int(raw_measurement_count),
            "raw_optical_event_sequence": int(raw_event_sequence),
            "optical_timestamp_s": last_sync_s,
            "optical_age_s": max(0.0, now - last_sync_s),
            "optical_measurement_count": int(measurement_count),
            "optical_lighthouse_count": int(lighthouse_count),
            "optical_event_sequence": int(optical_event_sequence),
            # libsurvive's global-fit error/covariance is not exposed by
            # this stable callback API.  Do not invent a confidence value.
            "pose_confidence": None,
        }

    def scene_snapshot(self):
        """Return raw global-scene facts without applying readiness policy."""
        if not self._installed:
            return {
                "bridge_available": False,
                "bridge_error": self._error_reason
                or "native libsurvive monitor is not installed",
                "context_epoch": 0,
                "global_scene_generation": 0,
                "lighthouses": {},
            }
        snapshot = self._native.scene_snapshot()
        if not isinstance(snapshot, dict):
            raise RuntimeError(
                "outdated pika optical native extension; reinstall agx-pypika "
                "to rebuild _optical_health_native"
            )
        snapshot["bridge_available"] = True
        snapshot["bridge_error"] = None
        return snapshot

class ViveTracker:
    """
    Vive Tracker device class, provides access interface for Vive Tracker device pose data
    
    Args:
        config_path (str, optional): Configuration file path
        lh_config (str, optional): Lighthouse configuration
        args (list, optional): Additional pysurvive arguments
        product (str, optional): Product transform to apply, 'sense' or 'ego'. Default 'sense'
    """
    
    def __init__(self, config_path=None, lh_config=None, args=None, product='sense'):
        self.config_path = config_path
        self.lh_config = lh_config
        self.args = args if args else []
        
        if product not in PRODUCT_TRANSFORMS:
            raise ValueError(
                f"Unsupported product '{product}', expected one of: {list(PRODUCT_TRANSFORMS.keys())}"
            )
        self.product = product
        self._product_transform = PRODUCT_TRANSFORMS[product]
        tx, ty, tz = self._product_transform['translation']
        self._transform_matrix = xyzrpy2Mat(tx, ty, tz, 0, 0, 0)
        self._rotate_matrix = None
        if self._product_transform['apply_rotation']:
            # Initial rotation correction: rotate -20 degrees around X axis (roll)
            initial_rotation = xyzrpy2Mat(0, 0, 0, -(20.0 / 180.0 * math.pi), 0, 0)
            # Alignment rotation: -90 degrees around X axis, -90 degrees around Y axis
            alignment_rotation = xyzrpy2Mat(0, 0, 0, -90 / 180 * math.pi, -90 / 180 * math.pi, 0)
            self._rotate_matrix = np.dot(initial_rotation, alignment_rotation)
        
        # Initialize state variables
        self.running = False
        self.context = None
        self.pose_queue = queue.Queue(maxsize=100)  # Queue for storing latest poses
        self.devices_info = {}  # Dictionary for storing device information
        self.data_lock = threading.Lock()
        self.latest_poses = {}  # Store latest pose for each device
        self._optical_health_monitor = _LibsurviveOpticalHealthMonitor()
        self._lighthouse_discovered_at = {}
        self._lighthouse_cohort_generation = 0
        
        # Thread objects
        self.collector_thread = None
        self.processor_thread = None
        self.device_monitor_thread = None
    
    def connect(self):
        """
        Initialize and connect to Vive Tracker devices
        
        Returns:
            bool: Whether the connection succeeded
        """
        if self.running:
            logger.warning("Vive Tracker is already connected")
            return True
        
        try:
            logger.info("Initializing pysurvive...")
            
            # Build pysurvive arguments
            survive_args = sys.argv[:1]  # Keep program name
            
            # Add configuration file arguments
            if self.config_path:
                survive_args.extend(['--config', self.config_path])
            
            # Add lighthouse configuration arguments
            if self.lh_config:
                survive_args.extend(['--lh', self.lh_config])
            
            # Add other arguments
            survive_args.extend(self.args)
            
            # Initialize pysurvive context
            self.context = pysurvive.SimpleContext(survive_args)
            if not self.context:
                logger.error("Error: Failed to initialize pysurvive context")
                return False
            
            logger.info("pysurvive initialized successfully")
            logger.info(f"Using '{self.product}' pose transform")
            if not self._optical_health_monitor.install(self.context):
                logger.error(
                    "Optical monitoring is unavailable; tracker health "
                    "will fail closed."
                )
            
            # Mark as running
            self.running = True
            
            # Create and start pose collection thread
            self.collector_thread = threading.Thread(target=self._pose_collector)
            self.collector_thread.daemon = True
            self.collector_thread.start()
            
            # Create and start pose processing thread
            self.processor_thread = threading.Thread(target=self._pose_processor)
            self.processor_thread.daemon = True
            self.processor_thread.start()
            
            # Create and start device monitor thread
            self.device_monitor_thread = threading.Thread(target=self._device_monitor)
            self.device_monitor_thread.daemon = True
            self.device_monitor_thread.start()
            
            logger.info("Vive Tracker pose tracking started")
            
            # Wait for initial data
            time.sleep(0.5)
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Vive Tracker: {e}")
            self.running = False
            return False
    
    def disconnect(self):
        """
        Disconnect from Vive Tracker devices
        """
        if not self.running and self.context is None:
            return True
        
        logger.info("Stopping Vive Tracker pose tracking...")
        self.running = False
        
        # Wait for threads to finish
        if self.collector_thread:
            self.collector_thread.join(timeout=2.0)
        
        if self.processor_thread:
            self.processor_thread.join(timeout=2.0)
            
        if self.device_monitor_thread:
            self.device_monitor_thread.join(timeout=2.0)
        
        # Stop libsurvive's own thread and destroy the native context.  The
        # upstream Python wrapper does not expose this in SimpleContext, so a
        # plain ``self.context = None`` leaks the decoder and prevents a safe
        # in-process restart after optical reacquisition stalls.
        context = self.context
        context_closed = True
        if context is not None:
            try:
                self._optical_health_monitor.close(context)
            except Exception as exc:
                logger.error("Failed to close libsurvive context: %s", exc)
                context_closed = False
        self.context = None
        self.pose_queue = queue.Queue(maxsize=100)
        
        # Print statistics
        logger.info("Device statistics:")
        for device_name, info in self.devices_info.items():
            logger.info(f"  - {device_name}: update count {info['updates']}")

        with self.data_lock:
            self.latest_poses.clear()
            self.devices_info.clear()
            self._lighthouse_discovered_at.clear()
            self._lighthouse_cohort_generation = 0
        self.collector_thread = None
        self.processor_thread = None
        self.device_monitor_thread = None
        
        logger.info("Vive Tracker disconnected")
        return context_closed
    
    def _device_monitor(self):
        """
        Device monitor thread function
        Periodically checks for new devices and updates device list
        """
        logger.info("Device monitor thread started")
        
        # Initialize device list
        self._update_device_list()
        
        # Periodically check for new devices
        while self.running and self.context.Running():
            # Update device list
            self._update_device_list()
            
            # Check once per second
            time.sleep(1.0)
    
    def _update_device_list(self):
        """
        Update device list
        """
        try:
            # Get all current devices
            devices = list(self.context.Objects())
            
            # Update device info dictionary
            with self.data_lock:
                for device in devices:
                    device_name = str(device.Name(), 'utf-8')
                    if device_name not in self.devices_info:
                        logger.info(f"Detected new device: {device_name}")
                        self.devices_info[device_name] = {"updates": 0, "last_update": 0}
                        if device_name.startswith("LH"):
                            self._lighthouse_discovered_at[device_name] = time.monotonic()
                            self._lighthouse_cohort_generation += 1
        except Exception as e:
            logger.error(f"Error updating device list: {e}")
    
    def _pose_collector(self):
        """
        Pose collection thread function
        Continuously gets latest pose data from pysurvive and puts it in the queue
        """
        logger.info("Pose collection thread started")
        
        # Get and print all available devices
        devices = list(self.context.Objects())
        if not devices:
            logger.warning("Warning: No devices detected")
        else:
            logger.info(f"Detected {len(devices)} device(s):")
            with self.data_lock:
                for device in devices:
                    device_name = str(device.Name(), 'utf-8')
                    logger.info(f"  - {device_name}")
                    if device_name not in self.devices_info:
                        self.devices_info[device_name] = {
                            "updates": 0,
                            "last_update": 0,
                        }
                        if device_name.startswith("LH"):
                            self._lighthouse_discovered_at[device_name] = (
                                time.monotonic()
                            )
                            self._lighthouse_cohort_generation += 1
        
        # Continuously get latest poses
        while self.running and self.context.Running():
            updated = self.context.NextUpdated()
            if updated:
                # Get device name
                device_name = str(updated.Name(), 'utf-8')
                
                # If new device, add to device info dictionary
                with self.data_lock:
                    if device_name not in self.devices_info:
                        logger.info(f"Detected new device update: {device_name}")
                        self.devices_info[device_name] = {"updates": 0, "last_update": 0}
                        if device_name.startswith("LH"):
                            self._lighthouse_discovered_at[device_name] = time.monotonic()
                            self._lighthouse_cohort_generation += 1
                
                # Get pose data
                pose_obj = updated.Pose()
                pose_data = pose_obj[0]  # Pose data
                timestamp = pose_obj[1]  # Timestamp
                
                # Convert pose data to matrix
                # Note: quaternion order from pysurvive is [w,x,y,z]; converted to [x,y,z,w] below
                origin_mat = xyzQuaternion2matrix(
                                pose_data.Pos[0], pose_data.Pos[1], pose_data.Pos[2],
                                pose_data.Rot[1], pose_data.Rot[2], pose_data.Rot[3], pose_data.Rot[0]
                            )
                
                # Apply product-specific pose transform:
                # Sense: rotation then translation to gripper center
                # Ego: translation only
                if self._rotate_matrix is not None:
                    result_mat = np.matmul(np.matmul(origin_mat, self._rotate_matrix), self._transform_matrix)
                else:
                    result_mat = np.matmul(origin_mat, self._transform_matrix)
                # Extract position and quaternion from result matrix
                x, y, z, qx, qy, qz, qw = matrixToXYZQuaternion(result_mat)
                
                # Extract position and rotation information
                position = [x, y, z]
                rotation = [qx, qy, qz, qw]
                    
                # Snapshot lighthouse support separately from the fused pose.
                # During occlusion ``timestamp`` continues from IMU reports,
                # while ``optical_timestamp_s`` correctly stops advancing.
                optical_health = self._optical_health_monitor.snapshot(device_name) or {}

                # Create pose data object
                pose = PoseData(
                    device_name,
                    timestamp,
                    position,
                    rotation,
                    **optical_health,
                )
                
                # Update device info
                with self.data_lock:
                    if device_name in self.devices_info:
                        self.devices_info[device_name]["updates"] += 1
                        self.devices_info[device_name]["last_update"] = time.time()
                
                # Put pose data in queue; discard old data if queue is full
                try:
                    self.pose_queue.put_nowait(pose)
                except queue.Full:
                    try:
                        self.pose_queue.get_nowait()  # Discard oldest data
                        self.pose_queue.put_nowait(pose)
                    except:
                        pass  # Ignore possible errors
    
    def _pose_processor(self):
        """
        Pose processing thread function
        Gets and processes pose data from queue, updates latest pose dictionary
        """
        logger.info("Pose processing thread started")
        
        while self.running:
            try:
                # Try to get pose data from queue with timeout to periodically check running state
                pose = self.pose_queue.get(timeout=0.1)
                
                # Update latest pose dictionary
                with self.data_lock:
                    self.latest_poses[pose.device_name] = pose
                
                # Custom pose processing logic can be added here
                # e.g.: send to other applications, log to file, perform analysis, etc.
                
            except queue.Empty:
                # Queue empty, continue waiting
                continue
            except Exception as e:
                logger.error(f"Error processing pose data: {e}")
    
    def get_pose(self, device_name=None):
        """
        Get latest pose data for specified device
        
        Args:
            device_name (str, optional): Device name; if None, returns pose data for all devices
        
        Returns: 
            PoseData or dict: If device_name is specified, returns that device's PoseData object;
                          otherwise returns a dict of all device poses {device_name: PoseData}
        """
        if not self.running:
            logger.warning("Vive Tracker not connected, returning empty pose data")
            return None if device_name else {}
        
        # Force update device list once to ensure latest added devices are available
        self._update_device_list()
        
        with self.data_lock:
            if device_name:
                return self.latest_poses.get(device_name)
            else:
                return self.latest_poses.copy()
    
    def get_devices(self):
        """
        Get list of all detected devices
        
        Returns:
            list: Device name list
        """
        # Force update device list once to ensure latest added devices are available
        self._update_device_list()
        
        with self.data_lock:
            return list(self.devices_info.keys())

    def get_tracking_health(self, device_name=None):
        """Return optical and global-scene facts for higher-level policy.

        This method intentionally does not decide whether tracking is ready.
        It reports the native context epoch, global-scene events, discovered
        Lighthouse cohort, and the latest real optical measurements.  A robot
        integration can then apply policy appropriate to its safety envelope.
        """
        self._update_device_list()
        scene = self._optical_health_monitor.scene_snapshot()
        # Optical events are independent of fused pose callbacks.  A tracker
        # can remain perfectly still while its photodiodes continue receiving
        # Lighthouse sweeps, so health must be sampled at query time instead
        # of being copied from the last cached PoseData object.
        optical = self._optical_health_monitor.snapshot(device_name)
        if optical is not None:
            scene.update(optical)
        with self.data_lock:
            discovered = tuple(
                sorted(name for name in self.devices_info if name.startswith("LH"))
            )
            discovered_at = {
                name: self._lighthouse_discovered_at.get(name, 0.0)
                for name in discovered
            }
            cohort_generation = self._lighthouse_cohort_generation
            pose = self.latest_poses.get(device_name) if device_name else None
            if pose is None:
                pose = next(
                    (
                        value
                        for name, value in self.latest_poses.items()
                        if not name.startswith("LH")
                    ),
                    None,
                )
        scene.update(
            {
                "discovered_lighthouses": discovered,
                "lighthouse_discovered_at": discovered_at,
                "lighthouse_cohort_generation": cohort_generation,
            }
        )
        if pose is not None:
            scene["tracker_device"] = pose.device_name
            scene["tracker_pose_timestamp_s"] = pose.timestamp
            scene["tracker_position"] = tuple(float(v) for v in pose.position)
            scene["tracker_rotation"] = tuple(float(v) for v in pose.rotation)
        return scene
    
    def get_device_info(self, device_name=None):
        """
        Get device information
        
        Args:
            device_name (str, optional): Device name; if None, returns info for all devices
        
        Returns:
            dict: Device information dictionary
        """
        # Force update device list once to ensure latest added devices are available
        self._update_device_list()
        
        with self.data_lock:
            if device_name:
                return self.devices_info.get(device_name)
            else:
                return self.devices_info.copy()
    
    def __del__(self):
        """
        Destructor to ensure resources are released
        """
        self.disconnect()
