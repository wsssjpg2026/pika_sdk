#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#include <time.h>

/*
 * Keep this bridge independent of libsurvive's private structure layout.
 * The function-pointer signatures below are part of libsurvive's public
 * hook API.  Python supplies the already-loaded install function address, so
 * the extension cannot accidentally bind a second libsurvive instance.
 */
typedef struct SurviveObject SurviveObject;
typedef struct SurviveContext SurviveContext;
typedef void LightcapElement;
typedef struct {
    double Pos[3];
    double Rot[4];
} SurvivePose;
typedef uint8_t survive_channel;
typedef uint32_t survive_timecode;
typedef void (*lightcap_process_func)(SurviveObject *, const LightcapElement *);
typedef lightcap_process_func (*install_lightcap_func)(SurviveContext *,
                                                       lightcap_process_func);
typedef void (*sync_process_func)(SurviveObject *, survive_channel,
                                  survive_timecode, bool, bool);
typedef sync_process_func (*install_sync_func)(SurviveContext *,
                                               sync_process_func);
typedef void (*sweep_process_func)(SurviveObject *, survive_channel, int,
                                   survive_timecode, bool);
typedef sweep_process_func (*install_sweep_func)(SurviveContext *,
                                                 sweep_process_func);
typedef void (*lighthouse_pose_process_func)(SurviveContext *, uint8_t,
                                             const SurvivePose *);
typedef lighthouse_pose_process_func (*install_lighthouse_pose_func)(
    SurviveContext *, lighthouse_pose_process_func);

#define EVENT_CAPACITY 2048u
#define CHANNEL_CAPACITY 16u
#define LIGHTHOUSE_CAPACITY 16u

typedef struct {
    _Atomic uint64_t timestamp_ns;
    _Atomic uint8_t channel;
} OpticalEvent;

typedef struct {
    _Atomic uint64_t timestamp_ns;
    _Atomic uint64_t generation;
    _Atomic uint64_t pose_bits[7];
} LighthouseSceneEvent;

static OpticalEvent raw_events[EVENT_CAPACITY];
static OpticalEvent decoded_events[EVENT_CAPACITY];
static _Atomic uint64_t raw_write_sequence;
static _Atomic uint64_t decoded_write_sequence;
static lightcap_process_func prior_lightcap_process;
static sync_process_func prior_sync_process;
static sweep_process_func prior_sweep_process;
static lighthouse_pose_process_func prior_lighthouse_pose_process;
static SurviveContext *installed_context;
static LighthouseSceneEvent lighthouse_scene[LIGHTHOUSE_CAPACITY];
static _Atomic uint64_t context_epoch_sequence;
static _Atomic uint64_t installed_context_epoch;
static _Atomic uint64_t global_scene_generation;

static uint64_t monotonic_ns(void) {
    struct timespec ts;
    if (clock_gettime(CLOCK_MONOTONIC, &ts) != 0) {
        return 0;
    }
    return (uint64_t)ts.tv_sec * UINT64_C(1000000000) + (uint64_t)ts.tv_nsec;
}

static uint64_t double_to_bits(double value) {
    union {
        double value;
        uint64_t bits;
    } converted = {.value = value};
    return converted.bits;
}

static double bits_to_double(uint64_t bits) {
    union {
        double value;
        uint64_t bits;
    } converted = {.bits = bits};
    return converted.value;
}

static void record_optical_event(OpticalEvent *buffer,
                                 _Atomic uint64_t *write_sequence,
                                 survive_channel channel) {
    uint64_t now = monotonic_ns();
    uint64_t sequence = atomic_fetch_add_explicit(
        write_sequence, UINT64_C(1), memory_order_relaxed);
    OpticalEvent *event = &buffer[sequence % EVENT_CAPACITY];
    atomic_store_explicit(&event->channel, channel, memory_order_relaxed);
    atomic_store_explicit(&event->timestamp_ns, now, memory_order_release);
}

static void optical_health_lightcap(SurviveObject *object,
                                    const LightcapElement *element) {
    /* lightcap is the earliest public callback after a Tracker photodiode hit.
     * Record it before downstream Gen2 disambiguation so physical visibility
     * remains observable while sync/sweep decoding is reacquiring. */
    if (element != NULL) {
        record_optical_event(raw_events, &raw_write_sequence, 0);
    }
    lightcap_process_func prior = prior_lightcap_process;
    if (prior != NULL) {
        prior(object, element);
    }
}

static void optical_health_sync(SurviveObject *object, survive_channel channel,
                                survive_timecode timecode, bool ootx,
                                bool generation) {
    record_optical_event(decoded_events, &decoded_write_sequence, channel);
    sync_process_func prior = prior_sync_process;
    if (prior != NULL) {
        prior(object, channel, timecode, ootx, generation);
    }
}

static void optical_health_sweep(SurviveObject *object, survive_channel channel,
                                 int sensor_id, survive_timecode timecode,
                                 bool half_clock_flag) {
    record_optical_event(decoded_events, &decoded_write_sequence, channel);
    sweep_process_func prior = prior_sweep_process;
    if (prior != NULL) {
        prior(object, channel, sensor_id, timecode, half_clock_flag);
    }
}

static void optical_health_lighthouse_pose(SurviveContext *context,
                                           uint8_t lighthouse_index,
                                           const SurvivePose *pose) {
    if (pose != NULL && lighthouse_index < LIGHTHOUSE_CAPACITY) {
        LighthouseSceneEvent *event = &lighthouse_scene[lighthouse_index];
        for (unsigned i = 0; i < 3; ++i) {
            atomic_store_explicit(&event->pose_bits[i],
                                  double_to_bits(pose->Pos[i]),
                                  memory_order_relaxed);
        }
        for (unsigned i = 0; i < 4; ++i) {
            atomic_store_explicit(&event->pose_bits[i + 3],
                                  double_to_bits(pose->Rot[i]),
                                  memory_order_relaxed);
        }
        uint64_t generation = atomic_fetch_add_explicit(
                                  &global_scene_generation, UINT64_C(1),
                                  memory_order_relaxed) +
                              UINT64_C(1);
        atomic_store_explicit(&event->generation, generation,
                              memory_order_relaxed);
        atomic_store_explicit(&event->timestamp_ns, monotonic_ns(),
                              memory_order_release);
    }
    lighthouse_pose_process_func prior = prior_lighthouse_pose_process;
    if (prior != NULL) {
        prior(context, lighthouse_index, pose);
    }
}

static void reset_events(void) {
    atomic_store_explicit(&raw_write_sequence, UINT64_C(0), memory_order_relaxed);
    atomic_store_explicit(&decoded_write_sequence, UINT64_C(0), memory_order_relaxed);
    for (unsigned i = 0; i < EVENT_CAPACITY; ++i) {
        atomic_store_explicit(&raw_events[i].channel, 0, memory_order_relaxed);
        atomic_store_explicit(&raw_events[i].timestamp_ns, UINT64_C(0),
                              memory_order_relaxed);
        atomic_store_explicit(&decoded_events[i].channel, 0, memory_order_relaxed);
        atomic_store_explicit(&decoded_events[i].timestamp_ns, UINT64_C(0),
                              memory_order_relaxed);
    }
    atomic_store_explicit(&global_scene_generation, UINT64_C(0),
                          memory_order_relaxed);
    for (unsigned i = 0; i < LIGHTHOUSE_CAPACITY; ++i) {
        atomic_store_explicit(&lighthouse_scene[i].timestamp_ns, UINT64_C(0),
                              memory_order_relaxed);
        atomic_store_explicit(&lighthouse_scene[i].generation, UINT64_C(0),
                              memory_order_relaxed);
        for (unsigned j = 0; j < 7; ++j) {
            atomic_store_explicit(&lighthouse_scene[i].pose_bits[j], UINT64_C(0),
                                  memory_order_relaxed);
        }
    }
}

static PyObject *install_monitor(PyObject *self, PyObject *args) {
    (void)self;
    unsigned long long context_address = 0;
    unsigned long long lightcap_installer_address = 0;
    unsigned long long sync_installer_address = 0;
    unsigned long long sweep_installer_address = 0;
    unsigned long long lighthouse_pose_installer_address = 0;
    if (!PyArg_ParseTuple(args, "KKKKK", &context_address,
                          &lightcap_installer_address,
                          &sync_installer_address,
                          &sweep_installer_address,
                          &lighthouse_pose_installer_address)) {
        return NULL;
    }
    if (context_address == 0 || lightcap_installer_address == 0 ||
        sync_installer_address == 0 ||
        sweep_installer_address == 0 ||
        lighthouse_pose_installer_address == 0) {
        PyErr_SetString(PyExc_ValueError,
                        "libsurvive context and installer addresses must be non-zero");
        return NULL;
    }

    SurviveContext *context = (SurviveContext *)(uintptr_t)context_address;
    if (installed_context == context) {
        Py_RETURN_TRUE;
    }

    install_lightcap_func lightcap_installer =
        (install_lightcap_func)(uintptr_t)lightcap_installer_address;
    install_sync_func sync_installer =
        (install_sync_func)(uintptr_t)sync_installer_address;
    install_sweep_func sweep_installer =
        (install_sweep_func)(uintptr_t)sweep_installer_address;
    install_lighthouse_pose_func lighthouse_pose_installer =
        (install_lighthouse_pose_func)(uintptr_t)lighthouse_pose_installer_address;
    reset_events();
    lightcap_process_func prior_lightcap =
        lightcap_installer(context, optical_health_lightcap);
    sync_process_func prior_sync = sync_installer(context, optical_health_sync);
    sweep_process_func prior_sweep =
        sweep_installer(context, optical_health_sweep);
    lighthouse_pose_process_func prior_lighthouse_pose =
        lighthouse_pose_installer(context, optical_health_lighthouse_pose);
    if (prior_lightcap == optical_health_lightcap ||
        prior_sync == optical_health_sync ||
        prior_sweep == optical_health_sweep ||
        prior_lighthouse_pose == optical_health_lighthouse_pose) {
        PyErr_SetString(PyExc_RuntimeError,
                        "optical health callback is already in the libsurvive chain");
        return NULL;
    }
    prior_lightcap_process = prior_lightcap;
    prior_sync_process = prior_sync;
    prior_sweep_process = prior_sweep;
    prior_lighthouse_pose_process = prior_lighthouse_pose;
    installed_context = context;
    uint64_t context_epoch = atomic_fetch_add_explicit(
                                 &context_epoch_sequence, UINT64_C(1),
                                 memory_order_relaxed) +
                             UINT64_C(1);
    atomic_store_explicit(&installed_context_epoch, context_epoch,
                          memory_order_release);
    Py_RETURN_TRUE;
}

static PyObject *release_monitor(PyObject *self, PyObject *args) {
    (void)self;
    unsigned long long context_address = 0;
    if (!PyArg_ParseTuple(args, "K", &context_address)) {
        return NULL;
    }
    SurviveContext *context = (SurviveContext *)(uintptr_t)context_address;
    if (installed_context != NULL && installed_context != context) {
        PyErr_SetString(PyExc_ValueError,
                        "cannot release a different libsurvive context");
        return NULL;
    }

    /* The caller invokes this only after survive_simple_close has stopped all
     * libsurvive threads and destroyed the context.  Forget the stale pointer
     * so a replacement context may reuse the same address and still install
     * a fresh callback chain. */
    installed_context = NULL;
    prior_lightcap_process = NULL;
    prior_sync_process = NULL;
    prior_sweep_process = NULL;
    prior_lighthouse_pose_process = NULL;
    atomic_store_explicit(&installed_context_epoch, UINT64_C(0),
                          memory_order_release);
    reset_events();
    Py_RETURN_NONE;
}

static PyObject *scene_snapshot(PyObject *self, PyObject *args) {
    (void)self;
    (void)args;
    PyObject *result = PyDict_New();
    PyObject *lighthouses = PyDict_New();
    if (result == NULL || lighthouses == NULL) {
        Py_XDECREF(result);
        Py_XDECREF(lighthouses);
        return NULL;
    }

    uint64_t epoch = atomic_load_explicit(&installed_context_epoch,
                                          memory_order_acquire);
    uint64_t scene_generation = atomic_load_explicit(
        &global_scene_generation, memory_order_acquire);
    PyObject *epoch_value = PyLong_FromUnsignedLongLong(epoch);
    PyObject *generation_value = PyLong_FromUnsignedLongLong(scene_generation);
    if (epoch_value == NULL || generation_value == NULL ||
        PyDict_SetItemString(result, "context_epoch", epoch_value) < 0 ||
        PyDict_SetItemString(result, "global_scene_generation",
                             generation_value) < 0) {
        Py_XDECREF(epoch_value);
        Py_XDECREF(generation_value);
        Py_DECREF(lighthouses);
        Py_DECREF(result);
        return NULL;
    }
    Py_DECREF(epoch_value);
    Py_DECREF(generation_value);

    for (unsigned i = 0; i < LIGHTHOUSE_CAPACITY; ++i) {
        uint64_t timestamp_ns = atomic_load_explicit(
            &lighthouse_scene[i].timestamp_ns, memory_order_acquire);
        if (timestamp_ns == 0) {
            continue;
        }
        double pose[7];
        for (unsigned j = 0; j < 7; ++j) {
            pose[j] = bits_to_double(atomic_load_explicit(
                &lighthouse_scene[i].pose_bits[j], memory_order_relaxed));
        }
        uint64_t generation = atomic_load_explicit(
            &lighthouse_scene[i].generation, memory_order_relaxed);
        PyObject *entry = Py_BuildValue(
            "{s:d,s:K,s:(ddd),s:(dddd)}",
            "timestamp_s", (double)timestamp_ns / 1000000000.0,
            "generation", (unsigned long long)generation,
            "position", pose[0], pose[1], pose[2],
            "rotation", pose[3], pose[4], pose[5], pose[6]);
        char name[8];
        PyOS_snprintf(name, sizeof(name), "LH%u", i);
        if (entry == NULL || PyDict_SetItemString(lighthouses, name, entry) < 0) {
            Py_XDECREF(entry);
            Py_DECREF(lighthouses);
            Py_DECREF(result);
            return NULL;
        }
        Py_DECREF(entry);
    }
    if (PyDict_SetItemString(result, "lighthouses", lighthouses) < 0) {
        Py_DECREF(lighthouses);
        Py_DECREF(result);
        return NULL;
    }
    Py_DECREF(lighthouses);
    return result;
}

static void snapshot_events(OpticalEvent *buffer, uint64_t now,
                            uint64_t window_ns, uint64_t *latest_ns,
                            uint64_t *count, uint32_t *channels) {
    *latest_ns = 0;
    *count = 0;
    *channels = 0;
    for (unsigned i = 0; i < EVENT_CAPACITY; ++i) {
        uint64_t timestamp_ns = atomic_load_explicit(
            &buffer[i].timestamp_ns, memory_order_acquire);
        if (timestamp_ns == 0 || timestamp_ns > now) {
            continue;
        }
        if (timestamp_ns > *latest_ns) {
            *latest_ns = timestamp_ns;
        }
        if (now - timestamp_ns > window_ns) {
            continue;
        }
        uint8_t channel = atomic_load_explicit(
            &buffer[i].channel, memory_order_relaxed);
        ++*count;
        if (channel < CHANNEL_CAPACITY) {
            *channels |= UINT32_C(1) << channel;
        }
    }
}

static PyObject *snapshot_monitor(PyObject *self, PyObject *args) {
    (void)self;
    double window_s = 0.1;
    if (!PyArg_ParseTuple(args, "|d", &window_s)) {
        return NULL;
    }
    if (!(window_s > 0.0)) {
        PyErr_SetString(PyExc_ValueError, "window_s must be positive");
        return NULL;
    }

    uint64_t now = monotonic_ns();
    uint64_t window_ns = (uint64_t)(window_s * 1000000000.0);
    uint64_t raw_latest_ns = 0;
    uint64_t raw_count = 0;
    uint32_t raw_channels = 0;
    uint64_t decoded_latest_ns = 0;
    uint64_t decoded_count = 0;
    uint32_t decoded_channels = 0;
    snapshot_events(raw_events, now, window_ns, &raw_latest_ns, &raw_count,
                    &raw_channels);
    snapshot_events(decoded_events, now, window_ns, &decoded_latest_ns,
                    &decoded_count, &decoded_channels);

    unsigned channel_count = 0;
    while (decoded_channels != 0) {
        channel_count += decoded_channels & 1u;
        decoded_channels >>= 1u;
    }
    uint64_t raw_sequence = atomic_load_explicit(
        &raw_write_sequence, memory_order_relaxed);
    uint64_t decoded_sequence = atomic_load_explicit(
        &decoded_write_sequence, memory_order_relaxed);
    return Py_BuildValue(
        "(KKKKKIK)",
        (unsigned long long)raw_latest_ns,
        (unsigned long long)raw_count,
        (unsigned long long)raw_sequence,
        (unsigned long long)decoded_latest_ns,
        (unsigned long long)decoded_count,
        channel_count,
        (unsigned long long)decoded_sequence);
}

static PyMethodDef methods[] = {
    {"install", install_monitor, METH_VARARGS,
     "Install native raw-lightcap and decoded sync+sweep monitors."},
    {"release", release_monitor, METH_VARARGS,
     "Forget a libsurvive context after it has been destroyed."},
    {"snapshot", snapshot_monitor, METH_VARARGS,
     "Return raw and decoded optical event snapshots."},
    {"scene_snapshot", scene_snapshot, METH_NOARGS,
     "Return context epoch and global Lighthouse scene events."},
    {NULL, NULL, 0, NULL},
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "_optical_health_native",
    "Native libsurvive optical-health bridge.",
    -1,
    methods,
};

PyMODINIT_FUNC PyInit__optical_health_native(void) {
    reset_events();
    return PyModule_Create(&module);
}
