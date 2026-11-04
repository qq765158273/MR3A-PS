"""Keep every event and failed frame while sharing lossless screenshot files."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

import numpy as np
from PIL import Image

from psauto.evidence import EvidenceSink, export_task_evidence


class EvidenceTests(unittest.TestCase):
    def test_nodes_and_failed_recognitions_keep_exact_pixels_and_share_identical_frames(self):
        frame = np.zeros((12,16,3),dtype=np.uint8)
        frame[:,:,0]=37
        failed=frame.copy();failed[2,3]=[1,2,3]
        recos={i:SimpleNamespace(reco_id=i,algorithm='TemplateMatch',hit=i!=3,
                               raw_detail={},raw_image=failed if i==3 else frame.copy())
               for i in [1,2,3]}
        removed=[]
        tasker=SimpleNamespace(add_context_sink=lambda sink:7,
                               remove_context_sink=removed.append,
                               get_recognition_detail=recos.__getitem__)
        trace=EvidenceSink(tasker)
        for i,kind in [(1,'Succeeded'),(2,'Succeeded'),(3,'Failed')]:
            trace.on_raw_notification(tasker,'Node.Recognition.'+kind,{'reco_id':i,'name':'check'})
        nodes=[SimpleNamespace(name='same',completed=True,recognition=recos[i],action=None)
               for i in [1,2]]
        job=SimpleNamespace(succeeded=True,get=lambda:SimpleNamespace(entry='same',nodes=nodes))
        with TemporaryDirectory() as tmp:
            directory=Path(tmp)
            report=export_task_evidence(job,directory,trace)
            events=json.loads((directory/'events.json').read_text(encoding='utf-8'))
            self.assertEqual(len(events),3)
            self.assertEqual(len(list(directory.glob('*.png'))),2)
            shared=report['nodes'][0]['screenshot']
            self.assertEqual(report['nodes'][1]['screenshot'],shared)
            self.assertEqual([e['screenshot'] for e in events[:2]],[shared,shared])
            for item,expected in [(events[0],frame),(events[2],failed)]:
                with Image.open(directory/item['screenshot']) as image:
                    np.testing.assert_array_equal(np.asarray(image)[:,:,::-1],expected)
        self.assertEqual(removed,[7])
