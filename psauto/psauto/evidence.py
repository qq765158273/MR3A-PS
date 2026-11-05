"""Export native Maa results and debug screenshots; does not make workflow decisions."""

import json
import hashlib
import io
import re
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

from PIL import Image
from maa.context import ContextEventSink


class _ExportProfile:
    """Post-task export costs; the pipeline's native event timing is unchanged."""
    def __init__(self, target=None):
        self.target = target if target is not None else {}
        self.started = time.perf_counter()
        self.phases = Counter()
        self.counts = Counter()
        self.node_access = 'eager'

    @contextmanager
    def measure(self, phase):
        started = time.perf_counter()
        try:
            yield
        finally:
            self.phases[phase] += (time.perf_counter() - started) * 1000

    def finish(self):
        elapsed = (time.perf_counter() - self.started) * 1000
        self.target.update({'node_access': self.node_access,
                            'total_ms': round(elapsed, 2),
                            'phases_ms': {key: round(value, 2) for key, value in self.phases.items()},
                            'unattributed_ms': round(elapsed - sum(self.phases.values()), 2),
                            'counts': dict(self.counts)})


class _ScreenshotStore:
    """Share identical raw frames across node and recognition evidence."""
    def __init__(self, directory, profile=None):
        self.directory = Path(directory)
        self.frames = {}
        self.recognitions = {}
        self.profile = profile if profile is not None else _ExportProfile()

    def save(self, raw, filename, reco_id=None):
        if reco_id in self.recognitions:
            self.profile.counts['recognition_reuses'] += 1
            return self.recognitions[reco_id]
        with self.profile.measure('hash_copy_ms'):
            # Maa returns contiguous BGR; preserve C-order for strided callers too.
            pixels = raw if raw.flags.c_contiguous else raw.copy(order='C')
        with self.profile.measure('hash_ms'):
            digest = (pixels.shape, hashlib.sha256(memoryview(pixels)).digest())
        self.profile.counts['frames_hashed'] += 1
        self.profile.counts['raw_bytes_hashed'] += raw.nbytes
        if digest not in self.frames:
            with self.profile.measure('image_conversion_ms'):
                image = Image.frombuffer('RGB', (pixels.shape[1], pixels.shape[0]),
                                         pixels, 'raw', 'BGR', 0, 1)
            with image, io.BytesIO() as encoded:
                with self.profile.measure('png_encode_ms'):
                    image.save(encoded, format='PNG', compress_level=1)
                with self.profile.measure('png_write_ms'):
                    with encoded.getbuffer() as payload:
                        (self.directory / filename).write_bytes(payload)
            self.profile.counts['unique_pngs'] += 1
            self.frames[digest] = filename
        filename = self.frames[digest]
        if reco_id is not None:
            self.recognitions[reco_id] = filename
        return filename


class EvidenceSink(ContextEventSink):
    """Record Maa notifications, including failed recognition candidates."""

    def __init__(self, tasker):
        self.tasker = tasker
        self.events = []
        self.started = time.monotonic()
        self.sink_id = tasker.add_context_sink(self)

    def on_raw_notification(self, tasker, msg, details):
        self.events.append({'event': msg, 'elapsed_ms': round((time.monotonic() - self.started) * 1000),
                            'details': details})

    def write(self, directory, screenshots=None):
        screenshots = screenshots or _ScreenshotStore(directory)
        captured = set()
        for event in self.events:
            reco_id = event['details'].get('reco_id')
            if not reco_id or reco_id in captured or not event['event'].endswith(('Succeeded', 'Failed')):
                continue
            captured.add(reco_id)
            if reco_id in screenshots.recognitions:
                event['screenshot'] = screenshots.recognitions[reco_id]
                continue
            with screenshots.profile.measure('candidate_detail_ms'):
                reco = self.tasker.get_recognition_detail(reco_id)
            screenshots.profile.counts['candidate_detail_reads'] += 1
            raw = reco.raw_image if reco is not None else None
            if raw is not None and raw.size:
                filename = f'recognition_{reco_id}.png'
                event['screenshot'] = screenshots.save(raw, filename, reco_id)
            del raw, reco  # Do not retain the preceding candidate's debug images.
        with screenshots.profile.measure('metadata_ms'):
            (directory / 'events.json').write_text(json.dumps(self.events, ensure_ascii=False, indent=2), encoding='utf-8')
        self.close()

    def close(self):
        if self.sink_id is not None:
            self.tasker.remove_context_sink(self.sink_id)
            self.sink_id = None


_PHASES = ('scan_prepare_ms', 'recognition_ms', 'before_action_ms', 'action_ms', 'after_action_ms')


def _pipeline_spans(events):
    """Use native task/node IDs; recognition retries do not create report nodes."""
    spans, active = {}, {}
    for event in events:
        details, kind = event['details'], event['event']
        task_id = details.get('task_id')
        key = (task_id, details.get('node_id'))
        if kind == 'Node.PipelineNode.Starting':
            span = {'events': [event]}
            spans[key] = span
            active.setdefault(task_id, []).append(span)
        elif kind in ('Node.PipelineNode.Succeeded', 'Node.PipelineNode.Failed'):
            span = spans.get(key)
            if span is not None:
                span['events'].append(event)
                span['status'] = 'succeeded' if kind.endswith('.Succeeded') else 'failed'
                stack = active.get(task_id, [])
                if stack and stack[-1] is span:
                    stack.pop()
        elif active.get(task_id):
            active[task_id][-1]['events'].append(event)
    return spans


def _node_timing(span):
    group = span['events']
    if 'status' not in span:
        return None
    phases = Counter({key: 0 for key in _PHASES})
    phase, previous = 'scan_prepare_ms', group[0]['elapsed_ms']
    transitions = {
        'Node.NextList.Starting': 'recognition_ms',
        'Node.NextList.Succeeded': 'before_action_ms',
        'Node.NextList.Failed': 'scan_prepare_ms',
        'Node.Action.Starting': 'action_ms',
        'Node.Action.Succeeded': 'after_action_ms',
        'Node.Action.Failed': 'after_action_ms',
    }
    for event in group[1:]:
        stamp = event['elapsed_ms']
        phases[phase] += max(0, stamp - previous)
        previous = stamp
        phase = transitions.get(event['event'], phase)
    counts = Counter(event['event'] for event in group)
    return {**phases, 'total_ms': group[-1]['elapsed_ms'] - group[0]['elapsed_ms'],
            'scan_attempts': counts['Node.NextList.Starting'],
            'scan_retries': max(0, counts['Node.NextList.Starting'] - 1),
            'recognition_attempts': counts['Node.Recognition.Starting'],
            'candidate_misses': counts['Node.Recognition.Failed'], 'status': span['status']}


def _attach_timings(report, events):
    spans = _pipeline_spans(events)
    for node in report['nodes']:
        span = spans.get((report.get('task_id'), node.get('node_id')))
        if span is None:
            continue
        timing = _node_timing(span)
        if timing is not None:
            node['timing'] = timing
        recognition = node.get('recognition')
        if recognition is not None:
            recognition['rule_passed'] = any(
                event['event'] == 'Node.Recognition.Succeeded'
                and event['details'].get('reco_id') == recognition.get('reco_id')
                for event in span['events'])


def _write_summary(directory, report, events):
    task_id = report.get('task_id')
    events = [event for event in events
              if task_id is None or event['details'].get('task_id') == task_id]
    counts = Counter(event['event'] for event in events)
    timings = [node['timing'] for node in report['nodes'] if 'timing' in node]
    phase = {key: sum(row[key] for row in timings) for key in _PHASES}
    event_ms = max((event['elapsed_ms'] for event in events), default=0)
    phase['unattributed_ms'] = event_ms - sum(phase.values())
    summary = {
        'timing_basis': 'native_node_lifecycle',
        'succeeded': report['succeeded'],
        'pipeline_event_ms': event_ms,
        'completed_nodes': sum(1 for node in report['nodes'] if node['completed']),
        'node_count': len(report['nodes']),
        'timed_nodes': len(timings),
        'timing_complete': bool(timings) and len(timings) == len(report['nodes']) and phase['unattributed_ms'] >= 0,
        'recognition_attempts': counts['Node.Recognition.Starting'],
        'candidate_misses': counts['Node.Recognition.Failed'],
        'recognition_failures': counts['Node.Recognition.Failed'],  # Compatibility; candidate misses, not task failures.
        'scan_retries': sum(row['scan_retries'] for row in timings),
        'pipeline_node_failures': counts['Node.PipelineNode.Failed'],
        'action_failures': counts['Node.Action.Failed'],
        'event_counts': dict(counts),
        'action_counts': dict(Counter(node.get('action', {}).get('type')
                                      for node in report['nodes'] if node.get('action'))),
        'recognition_algorithm_counts': dict(Counter(node.get('recognition', {}).get('algorithm')
                                                     for node in report['nodes'] if node.get('recognition'))),
        'screenshot_files': len(list(Path(directory).glob('*.png'))),
        'phase_ms': dict(phase),
    }
    (Path(directory) / 'summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return summary


def _node_record(node, index, screenshots):
    item = {"name": node.name, "completed": node.completed, 'node_id': getattr(node, 'node_id', None)}
    reco = node.recognition
    if reco:
        item['recognition'] = {"algorithm": str(reco.algorithm), "hit": reco.hit, 'reco_id': reco.reco_id,
                               "detail": reco.raw_detail}
        raw = reco.raw_image
        if raw is not None and raw.size:
            name = re.sub(r'[^A-Za-z0-9_-]', '_', node.name)
            filename = f'{index:03d}_{name}.png'
            item['screenshot'] = screenshots.save(raw, filename, reco.reco_id)
    if node.action:
        item['action'] = {"type": str(node.action.action), "success": node.action.success,
                          "detail": node.action.raw_detail}
    return item


def export_task_evidence(job, directory, trace=None, *, tasker=None, profile=None):
    measured = _ExportProfile(profile)
    try:
        return _export_task_evidence(job, directory, trace, tasker, measured)
    finally:
        measured.finish()


def _export_task_evidence(job, directory, trace, tasker, measured):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    screenshots = _ScreenshotStore(directory, measured)
    with measured.measure('task_detail_ms'):
        detail = job.get()
    report = {"entry": detail.entry if detail else None, "succeeded": job.succeeded, "nodes": [],
              "task_id": getattr(detail, 'task_id', None)}
    if detail:
        owner = tasker if tasker is not None else getattr(trace, 'tasker', None)
        if owner is not None and hasattr(detail, 'node_id_list'):
            # TaskDetail.nodes caches every raw/draw image. Use only public SDK
            # APIs, and release each detail before asking for the next one.
            measured.node_access = 'streaming'
            for index, node_id in enumerate(detail.node_id_list):
                with measured.measure('node_detail_ms'):
                    node = owner.get_node_detail(node_id)
                if node is None:
                    raise RuntimeError(f'Failed to get node detail: {node_id}')
                report['nodes'].append(_node_record(node, index, screenshots))
                measured.counts['nodes'] += 1
                del node
        else:
            measured.node_access = 'eager_compatibility'
            with measured.measure('node_detail_ms'):
                nodes = detail.nodes
            for index, node in enumerate(nodes):
                report['nodes'].append(_node_record(node, index, screenshots))
                measured.counts['nodes'] += 1
    events = trace.events if trace is not None else []
    with measured.measure('metadata_ms'):
        _attach_timings(report, events)
        (directory / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    if trace is not None:
        trace.write(directory, screenshots)
    with measured.measure('metadata_ms'):
        _write_summary(directory, report, events)
    return report
