"""Offline native Maa export benchmark; no browser, database or input actions.

Run each implementation in a NEW process. --exporter accepts a saved evidence.py
for baseline comparisons. Source is an existing run's directory with report/PNG.
Windows working-set/private sampling covers EXPORT ONLY, not native task creation.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import sys
import threading
import time

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maa.define import LoggingLevelEnum
from maa.tasker import Tasker
from maa.toolkit import Toolkit
from psauto.config import Config
from psauto.controller import JumpServerController
from psauto.pipeline import create_tasker


class MemoryCounters(ctypes.Structure):
    _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
        (name, ctypes.c_size_t) for name in ('PeakWorkingSetSize', 'WorkingSetSize',
        'QuotaPeakPagedPoolUsage', 'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage',
        'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage', 'PrivateUsage')]


def memory():
    counters = MemoryCounters()
    counters.cb = ctypes.sizeof(counters)
    handle = ctypes.windll.kernel32.GetCurrentProcess
    handle.restype = wintypes.HANDLE
    query = ctypes.windll.psapi.GetProcessMemoryInfo
    query.argtypes = [wintypes.HANDLE, ctypes.POINTER(MemoryCounters), wintypes.DWORD]
    query.restype = wintypes.BOOL
    if not query(handle(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError()
    return {'rss': counters.WorkingSetSize, 'private': counters.PrivateUsage}


def sample(stop, peaks, errors):
    try:
        while not stop.wait(.02):
            current = memory()
            # Bound THIS benchmark process only; never touch other processes.
            if current['private'] > 6 * 1024**3:
                os._exit(90)
            for key, value in current.items():
                peaks[key] = max(peaks[key], value)
    except Exception as exc:
        errors.append(exc)


def stable(value):
    """Native elapsed durations vary; retain every non-timing field for A/B."""
    if isinstance(value, dict):
        return {key: stable(item) for key, item in value.items()
                if key not in ('timing', 'elapsed_ms', 'pipeline_event_ms', 'phase_ms')}
    if isinstance(value, list):
        return [stable(item) for item in value]
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--exporter', type=Path)
    parser.add_argument('--nodes', type=int, default=208)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    if args.exporter:
        spec = importlib.util.spec_from_file_location('benchmark_exporter', args.exporter)
        exporter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(exporter)
    else:
        from psauto import evidence as exporter
    source = json.loads((args.source / 'report.json').read_text(encoding='utf-8'))
    frames = [args.source / node['screenshot'] for node in source['nodes'] if 'screenshot' in node]

    class Replay(JumpServerController):
        captures = 0
        def connect(self): return True
        def connected(self): return True
        def request_uuid(self): return 'offline-evidence-benchmark'
        def screencap(self):
            path = frames[self.captures % len(frames)]
            self.captures += 1
            with Image.open(path) as image:
                return np.asarray(image.convert('RGB'))[:, :, ::-1].copy()
        def reject(self, *args): raise AssertionError('Benchmark cannot send input')
        click = click_key = key_down = key_up = input_text = reject

    bundle = args.output / 'resource'
    (bundle / 'pipeline').mkdir(parents=True)
    pipeline = {f'Bench{i:03d}': {
        'recognition': 'ColorMatch', 'lower': [0, 0, 0], 'upper': [255, 255, 255],
        'roi': [0, 0, 1, 1], 'count': 1, 'action': 'DoNothing',
        'pre_delay': 0, 'post_delay': 0, 'rate_limit': 0,
        'next': [f'Bench{i+1:03d}'] if i + 1 < args.nodes else []}
        for i in range(args.nodes)}
    (bundle / 'pipeline/benchmark.json').write_text(json.dumps(pipeline), encoding='utf-8')
    Toolkit.init_option(str(args.output))
    Tasker.set_stdout_level(LoggingLevelEnum.Off)
    Tasker.set_debug_mode(True)
    controller = Replay(None, Config(jumpserver_url='http://offline.invalid'))
    controller.set_screenshot_use_raw_size(True)
    assert controller.post_connection().wait().succeeded
    tasker = create_tasker(str(bundle), controller)
    trace = exporter.EvidenceSink(tasker)
    job = tasker.post_task('Bench000').wait()
    assert job.succeeded
    before = memory()
    peaks = dict(before)
    stop = threading.Event()
    sample_errors = []
    sampler = threading.Thread(target=sample, args=(stop, peaks, sample_errors), daemon=True)
    sampler.start()
    profile = {}
    started = time.perf_counter()
    try:
        options = {'profile': profile} if 'profile' in inspect.signature(exporter.export_task_evidence).parameters else {}
        report = exporter.export_task_evidence(job, args.output, trace, **options)
    finally:
        elapsed = (time.perf_counter() - started) * 1000
        current = memory()
        for key, value in current.items():
            peaks[key] = max(peaks[key], value)
        stop.set()
        sampler.join()
        trace.close()
    if sample_errors:
        raise RuntimeError('Memory sampling failed; no benchmark metrics published') from sample_errors[0]
    manifest = {}
    for path in args.output.glob('*.png'):
        with Image.open(path) as image:
            manifest[path.name] = {'size': image.size,
                                  'rgb_sha256': hashlib.sha256(image.convert('RGB').tobytes()).hexdigest()}
    normalized = {name: stable(json.loads((args.output / name).read_text(encoding='utf-8')))
                  for name in ('report.json', 'events.json', 'summary.json')}
    (args.output / 'normalized.json').write_text(json.dumps(normalized, ensure_ascii=False), encoding='utf-8')
    metrics = {'nodes': len(report['nodes']), 'captures': controller.captures,
               'export_ms': round(elapsed, 2), 'profile': profile, 'sample_interval_ms': 20,
               'before_bytes': before, 'peak_bytes': peaks,
               'peak_increase_bytes': {key: peaks[key] - before[key] for key in peaks},
               'pixel_manifest': manifest, 'python': sys.version,
               'exporter_sha256': hashlib.sha256(Path(exporter.__file__).read_bytes()).hexdigest()}
    (args.output / 'benchmark.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in metrics.items() if key != 'pixel_manifest'}, indent=2))


if __name__ == '__main__':
    main()
