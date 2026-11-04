"""Export native Maa results and debug screenshots; does not make workflow decisions."""

import json
import hashlib
import re
import time
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
    if trace is not None:
        trace.write(directory, screenshots)
    return report
