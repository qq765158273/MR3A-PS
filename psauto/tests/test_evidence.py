"""Keep every event and failed frame while sharing lossless screenshot files."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
import weakref
from unittest.mock import patch

import numpy as np
from PIL import Image

from psauto.evidence import EvidenceSink, export_task_evidence, _attach_timings, _write_summary, _ScreenshotStore


class EvidenceTests(unittest.TestCase):
    def test_streaming_releases_node_raw_and_draw_before_next_public_read(self):
        from maa.define import TaskDetail
        refs, reads = [], []
        def get_node(node_id):
            self.assertTrue(all(ref() is None for ref in refs), 'Previous images retained')
            reads.append(node_id)
            raw = np.full((12,16,3), node_id, dtype=np.uint8)
            draw = raw.copy()
            reco = SimpleNamespace(reco_id=node_id, algorithm='ColorMatch', hit=True,
                                   raw_detail={}, raw_image=raw, draw_images=[draw])
            node = SimpleNamespace(name='same', completed=True, node_id=node_id,
                                   recognition=reco, action=None)
            refs.extend([weakref.ref(raw), weakref.ref(draw)])
            return node
        def forbid_eager(node_id):
            raise AssertionError('TaskDetail.nodes must never be accessed')
        detail = TaskDetail(1, 'same', [1,2,3], 3, forbid_eager)
        tasker = SimpleNamespace(get_node_detail=get_node)
        job = SimpleNamespace(succeeded=True, get=lambda:detail)
        for with_trace in [False, True]:
            reads.clear()
            profile = {}
            with TemporaryDirectory() as tmp:
                if with_trace:
                    tasker.add_context_sink=lambda sink:7
                    tasker.remove_context_sink=lambda sink:None
                    report=export_task_evidence(job,tmp,EvidenceSink(tasker),profile=profile)
                else:
                    report=export_task_evidence(job,tmp,tasker=tasker,profile=profile)
            self.assertEqual(reads,[1,2,3])
            self.assertEqual(len(report['nodes']),3)
            self.assertTrue(all(ref() is None for ref in refs))
            self.assertEqual(profile['node_access'],'streaming')
            self.assertEqual(profile['counts']['nodes'],3)
            self.assertGreaterEqual(profile['total_ms'],sum(profile['phases_ms'].values())-.1)
            self.assertIsNone(detail._nodes)

    def test_missing_streamed_node_fails_and_still_finishes_profile(self):
        detail=SimpleNamespace(entry='same',task_id=1,node_id_list=[123])
        job=SimpleNamespace(succeeded=True,get=lambda:detail)
        profile={}
        with TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError,'Failed to get node detail: 123'):
                export_task_evidence(job,tmp,tasker=SimpleNamespace(get_node_detail=lambda nid:None),profile=profile)
            self.assertFalse((Path(tmp)/'report.json').exists())
        self.assertEqual(profile['node_access'],'streaming')
        self.assertIn('node_detail_ms',profile['phases_ms'])
        self.assertIn('total_ms',profile)

    def test_legacy_without_owner_still_exports_and_labels_eager_access(self):
        job=SimpleNamespace(succeeded=True,get=lambda:SimpleNamespace(entry='old',nodes=[
            SimpleNamespace(name='old',completed=True,recognition=None,action=None)]))
        profile={}
        with TemporaryDirectory() as tmp:
            report=export_task_evidence(job,tmp,profile=profile)
        self.assertEqual(len(report['nodes']),1)
        self.assertEqual(profile['node_access'],'eager_compatibility')

    def test_contiguous_and_strided_bgr_keep_color_and_deduplication(self):
        raw=np.arange(12*16*3,dtype=np.uint8).reshape(12,16,3)
        views=[raw,raw[:,::-1],raw[::2,::2],raw.transpose(1,0,2)]
        with TemporaryDirectory() as tmp:
            store=_ScreenshotStore(tmp)
            for index,view in enumerate(views):
                with self.subTest(strides=view.strides):
                    filename=store.save(view,f'{index}.png',index)
                    self.assertEqual(store.save(view.copy(),f'duplicate{index}.png',index+10),filename)
                    with Image.open(Path(tmp)/filename) as image:
                        np.testing.assert_array_equal(np.asarray(image),view[:,:,::-1])
            self.assertEqual(len(list(Path(tmp).glob('*.png'))),len(views))

    def test_candidate_frames_are_released_and_write_failure_is_not_hidden(self):
        refs=[]
        def get_reco(reco_id):
            self.assertTrue(all(ref() is None for ref in refs))
            raw=np.full((12,16,3),reco_id,dtype=np.uint8)
            refs.append(weakref.ref(raw))
            return SimpleNamespace(raw_image=raw)
        tasker=SimpleNamespace(add_context_sink=lambda sink:7,remove_context_sink=lambda sid:None,
                               get_recognition_detail=get_reco)
        trace=EvidenceSink(tasker)
        for reco_id in [1,2,3]:
            trace.on_raw_notification(tasker,'Node.Recognition.Failed',{'reco_id':reco_id})
        with TemporaryDirectory() as tmp:
            trace.write(Path(tmp))
        self.assertTrue(all(ref() is None for ref in refs))
        raw=np.ones((12,16,3),dtype=np.uint8)
        with TemporaryDirectory() as tmp, patch.object(Path,'write_bytes',side_effect=OSError('disk full')):
            with self.assertRaisesRegex(OSError,'disk full'):
                _ScreenshotStore(tmp).save(raw,'failed.png')

    def test_actual_maa_retry_and_failed_action_export_all_native_node_spans(self):
        from maa.define import LoggingLevelEnum
        from maa.tasker import Tasker
        from maa.toolkit import Toolkit
        from psauto.config import Config
        from psauto.controller import JumpServerController
        from psauto.pipeline import create_tasker

        class Replay(JumpServerController):
            captures=0
            fail_click=False
            def connect(self): return True
            def connected(self): return True
            def request_uuid(self): return 'native-evidence-retry'
            def screencap(self):
                self.captures+=1
                return np.full((1080,1920,3),255 if self.captures>=3 else 0,dtype=np.uint8)
            def click(self,x,y): return not self.fail_click

        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'pipeline').mkdir()
            (root/'pipeline/retry.json').write_text(json.dumps({
                'Start':{'action':'DoNothing','next':['Ready'],'pre_delay':0,'post_delay':0,'rate_limit':0},
                'Ready':{'recognition':'ColorMatch','lower':[250,250,250],'upper':[255,255,255],
                         'roi':[0,0,4,4],'count':16,'action':'DoNothing','next':['Click'],
                         'pre_delay':0,'post_delay':0,'rate_limit':0,'timeout':2000},
                'Click':{'action':'Click','target':[1,1,1,1],'pre_delay':0,'post_delay':0}
            }),encoding='utf-8')
            Toolkit.init_option(str(Path(__file__).resolve().parents[1]))
            Tasker.set_stdout_level(LoggingLevelEnum.Off)
            controller=Replay(None,Config(jumpserver_url='http://offline.invalid'))
            controller.set_screenshot_use_raw_size(True)
            self.assertTrue(controller.post_connection().wait().succeeded)
            tasker=create_tasker(str(root),controller)
            for fail in [False,True]:
                controller.captures=0
                controller.fail_click=fail
                trace=EvidenceSink(tasker)
                job=tasker.post_task('Start').wait()
                directory=root/('failed' if fail else 'success')
                report=export_task_evidence(job,directory,trace)
                summary=json.loads((directory/'summary.json').read_text(encoding='utf-8'))
                with self.subTest(failed_action=fail):
                    self.assertEqual(job.succeeded,not fail)
                    self.assertEqual(summary['succeeded'],not fail)
                    self.assertEqual(summary['action_failures'],int(fail))
                    self.assertEqual(summary['scan_retries'],1)
                    self.assertEqual(summary['timed_nodes'],len(report['nodes']))
                    self.assertTrue(summary['timing_complete'])
                    self.assertEqual(sum(summary['phase_ms'].values()),summary['pipeline_event_ms'])
                    for node in report['nodes']:
                        self.assertIn('timing',node)
                        timing=node['timing']
                        self.assertEqual(sum(timing[k] for k in ['scan_prepare_ms','recognition_ms',
                                         'before_action_ms','action_ms','after_action_ms']),timing['total_ms'])

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
            summary=json.loads((directory/'summary.json').read_text(encoding='utf-8'))
            self.assertEqual(len(events),3)
            self.assertEqual(summary['recognition_failures'],1)
            self.assertEqual(summary['node_count'],2)
            self.assertFalse(summary['timing_complete'],'No native node lifecycle was supplied')
            self.assertEqual(len(list(directory.glob('*.png'))),2)
            shared=report['nodes'][0]['screenshot']
            self.assertEqual(report['nodes'][1]['screenshot'],shared)
            self.assertEqual([e['screenshot'] for e in events[:2]],[shared,shared])
            for item,expected in [(events[0],frame),(events[2],failed)]:
                with Image.open(directory/item['screenshot']) as image:
                    np.testing.assert_array_equal(np.asarray(image)[:,:,::-1],expected)
        self.assertEqual(removed,[7])

    def test_native_ids_keep_a_retried_node_and_a_repeated_name_separate(self):
        events=[]
        def event(ms,kind,**details):
            events.append({'event':'Node.'+kind,'elapsed_ms':ms,'details':{'task_id':1,**details}})
        event(10,'PipelineNode.Starting',node_id=11,name='same')
        event(20,'NextList.Starting')
        event(21,'Recognition.Starting',reco_id=21,name='same')
        event(25,'Recognition.Failed',reco_id=21,name='same')
        event(25,'NextList.Failed')
        event(40,'NextList.Starting')
        event(41,'Recognition.Starting',reco_id=22,name='same')
        event(45,'Recognition.Succeeded',reco_id=22,name='same')
        event(45,'NextList.Succeeded')
        event(50,'Action.Starting',action_id=31,name='same')
        event(70,'Action.Succeeded',action_id=31,name='same')
        event(80,'PipelineNode.Succeeded',node_id=11,name='same')
        event(80,'PipelineNode.Starting',node_id=12,name='same')
        event(90,'NextList.Starting')
        event(95,'Recognition.Succeeded',reco_id=23,name='same')
        event(95,'NextList.Succeeded')
        event(96,'Action.Starting',action_id=32,name='same')
        event(98,'Action.Succeeded',action_id=32,name='same')
        event(100,'PipelineNode.Succeeded',node_id=12,name='same')
        report={'task_id':1,'succeeded':True,'nodes':[
            {'node_id':11,'name':'same','completed':True,'recognition':{'reco_id':22,'hit':True}},
            {'node_id':12,'name':'same','completed':True,'recognition':{'reco_id':23,'hit':False}}]}
        _attach_timings(report,events)
        first,second=report['nodes']
        self.assertEqual(first['timing']['total_ms'],70)
        self.assertEqual(first['timing']['scan_retries'],1)
        self.assertEqual(first['timing']['scan_prepare_ms'],25)
        self.assertEqual(first['timing']['recognition_ms'],10)
        self.assertEqual(second['timing']['total_ms'],20)
        self.assertEqual(second['timing']['scan_retries'],0)
        self.assertTrue(second['recognition']['rule_passed'],'Inverse recognition succeeded despite raw hit=False')
        with TemporaryDirectory() as tmp:
            summary=_write_summary(tmp,report,events)
        self.assertTrue(summary['succeeded'])
        self.assertEqual(summary['candidate_misses'],1)
        self.assertEqual(summary['pipeline_node_failures'],0)
        self.assertEqual(summary['scan_retries'],1)
        self.assertEqual(sum(summary['phase_ms'].values()),100)

    def test_failed_recognition_wait_and_nested_task_are_not_lost_or_double_counted(self):
        def event(ms,kind,task=1,**details):
            return {'elapsed_ms':ms,'event':'Node.'+kind,'details':{'task_id':task,**details}}
        events=[event(10,'PipelineNode.Starting',node_id=11),
                event(20,'NextList.Starting'),event(30,'NextList.Succeeded'),
                event(40,'Action.Starting',action_id=31),
                event(42,'PipelineNode.Starting',task=2,node_id=21),
                event(50,'Action.Failed',task=2,action_id=41),
                event(55,'PipelineNode.Failed',task=2,node_id=21),
                event(60,'Action.Failed',action_id=31),event(70,'PipelineNode.Failed',node_id=11),
                event(70,'PipelineNode.Starting',node_id=12),
                event(80,'NextList.Starting'),event(85,'Recognition.Failed',reco_id=21),
                event(90,'NextList.Failed'),event(100,'NextList.Starting'),
                event(105,'Recognition.Failed',reco_id=22),event(110,'NextList.Failed'),
                event(120,'PipelineNode.Failed',node_id=12)]
        report={'task_id':1,'succeeded':False,'nodes':[
            {'node_id':11,'name':'click','completed':False},
            {'node_id':12,'name':'','completed':False}]}
        _attach_timings(report,events)
        self.assertEqual(report['nodes'][0]['timing']['action_ms'],20)
        self.assertEqual(report['nodes'][1]['timing']['total_ms'],50)
        self.assertEqual(report['nodes'][1]['timing']['scan_retries'],1)
        with TemporaryDirectory() as tmp:
            summary=_write_summary(tmp,report,events)
        self.assertFalse(summary['succeeded'])
        self.assertEqual(summary['action_failures'],1)
        self.assertEqual(summary['pipeline_node_failures'],2)
        self.assertEqual(summary['timed_nodes'],2)
        self.assertTrue(summary['timing_complete'])
        self.assertEqual(sum(summary['phase_ms'].values()),120)
