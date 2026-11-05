"""Export native Maa results and debug screenshots; does not make workflow decisions."""

import json
import hashlib
import re
import time
from collections import Counter
from pathlib import Path

from PIL import Image
from maa.context import ContextEventSink


class _ScreenshotStore:
    """Share identical raw frames across node and recognition evidence."""
    def __init__(self, directory):
        self.directory = Path(directory)
        self.frames = {}
        self.recognitions = {}

    def save(self, raw, filename, reco_id=None):
        if reco_id in self.recognitions:
            return self.recognitions[reco_id]
        digest = (raw.shape, hashlib.sha256(raw.tobytes()).digest())
        if digest not in self.frames:
            Image.fromarray(raw[:, :, ::-1]).save(self.directory / filename, compress_level=1)
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
            reco = self.tasker.get_recognition_detail(reco_id)
            if reco and reco.raw_image is not None and reco.raw_image.size:
                filename = f'recognition_{reco_id}.png'
                event['screenshot'] = screenshots.save(reco.raw_image, filename, reco_id)
        (directory / 'events.json').write_text(json.dumps(self.events, ensure_ascii=False, indent=2), encoding='utf-8')
        if self.sink_id is not None:
            self.tasker.remove_context_sink(self.sink_id)


def _event_group(events, starts, index):
    end = starts[index + 1] if index + 1 < len(starts) else len(events)
    return events[starts[index]:end]


def _first_event(group, name):
    return next((event for event in group if event['event'] == name), None)


def _node_timing(group):
    scan = _first_event(group, 'Node.NextList.Starting')
    recognized = _first_event(group, 'Node.NextList.Succeeded')
    action_start = _first_event(group, 'Node.Action.Starting')
    action_end = _first_event(group, 'Node.Action.Succeeded')
    done = _first_event(group, 'Node.PipelineNode.Succeeded')
    if not scan or not recognized or not action_start or not done:
        return None
    start = scan['elapsed_ms']
    action_start_ms = action_start['elapsed_ms']
    action_end_ms = (action_end or action_start)['elapsed_ms']
    done_ms = done['elapsed_ms']
    return {
        'recognition_ms': max(0, recognized['elapsed_ms'] - start),
        'before_action_ms': max(0, action_start_ms - recognized['elapsed_ms']),
        'action_ms': max(0, action_end_ms - action_start_ms),
        'after_action_ms': max(0, done_ms - action_end_ms),
        'total_ms': max(0, done_ms - start),
    }


def _attach_timings(report, events):
    starts = [index for index, event in enumerate(events)
              if event['event'] == 'Node.NextList.Starting']
    for index, node in enumerate(report['nodes']):
        if index >= len(starts):
            break
        timing = _node_timing(_event_group(events, starts, index))
        if timing:
            node['timing'] = timing
    return starts


def _write_summary(directory, report, events, starts):
    recognition_failed = [event for event in events
                          if event['event'] == 'Node.Recognition.Failed']
    action_failed = [event for event in events
                     if event['event'] == 'Node.Action.Failed']
    phase = Counter()
    rows = [node.get('timing') for node in report['nodes']]
    for row in rows:
        if row:
            phase['recognition_ms'] += row['recognition_ms']
            phase['before_action_ms'] += row['before_action_ms']
            phase['action_ms'] += row['action_ms']
            phase['after_action_ms'] += row['after_action_ms']
    for index, start in enumerate(starts[:-1]):
        group = _event_group(events, starts, index)
        done = _first_event(group, 'Node.PipelineNode.Succeeded')
        next_scan = events[starts[index + 1]]
        if done:
            phase['next_scan_prepare_ms'] += max(0, next_scan['elapsed_ms'] - done['elapsed_ms'])
    if starts:
        first_scan = events[starts[0]]['elapsed_ms']
        phase['initial_ms'] = first_scan
    summary = {
        'pipeline_event_ms': max((event['elapsed_ms'] for event in events), default=0),
        'completed_nodes': sum(1 for node in report['nodes'] if node['completed']),
        'node_count': len(report['nodes']),
        'recognition_attempts': sum(1 for event in events
                                   if event['event'] == 'Node.Recognition.Starting'),
        'recognition_failures': len(recognition_failed),
        'action_failures': len(action_failed),
        'event_counts': dict(Counter(event['event'] for event in events)),
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


def export_task_evidence(job, directory, trace=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    screenshots = _ScreenshotStore(directory)
    detail = job.get()
    report = {"entry": detail.entry if detail else None, "succeeded": job.succeeded, "nodes": []}
    if detail:
        for index, node in enumerate(detail.nodes):
            item = {"name": node.name, "completed": node.completed}
            reco = node.recognition
            if reco:
                item['recognition'] = {"algorithm": str(reco.algorithm), "hit": reco.hit,
                                       "detail": reco.raw_detail}
                raw = reco.raw_image
                if raw is not None and raw.size:
                    name = re.sub(r'[^A-Za-z0-9_-]', '_', node.name)
                    filename = f'{index:03d}_{name}.png'
                    item['screenshot'] = screenshots.save(raw, filename, reco.reco_id)
            if node.action:
                item['action'] = {"type": str(node.action.action), "success": node.action.success,
                                  "detail": node.action.raw_detail}
            report['nodes'].append(item)
    (directory / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    events = trace.events if trace is not None else []
    starts = _attach_timings(report, events)
    (directory / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    if trace is not None:
        trace.write(directory, screenshots)
    _write_summary(directory, report, events, starts)
    return report
