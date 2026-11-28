import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from fctia.local_api import Office

class PersistenceTest(unittest.TestCase):
    def test_restart_preserves_tasks_events_knowledge(self):
        with tempfile.TemporaryDirectory() as directory:
            path=str(Path(directory)/"office.sqlite")
            first=Office(path)
            try:
                t=first.engine.create("Briefing fictício","briefing",{"synthetic":True,"itens":["Reunião fictícia"]})
                tid=t["id"]
                first.engine.assign(tid,"executivo")
                first.engine.run(tid)
                first.engine.review(tid,True,"gestor-demo","Conferido")
                k=first.dispatch("POST","/api/tasks/"+tid+"/knowledge")
                first.dispatch("POST","/api/brain/approve",k)
                snapshot=first.engine.tasks[tid].copy()
                events=first.engine.events.copy()
            finally:
                first.brain.close()
            second=Office(path)
            try:
                self.assertEqual(second.engine.tasks[tid],snapshot)
                self.assertEqual(second.engine.events,events)
                rows=second.brain.search("executivo","Reunião")
                self.assertEqual(rows[0]["source"],"task:"+tid)
                self.assertEqual(second.dispatch("POST","/api/tasks/"+tid+"/knowledge"),k)
            finally:
                second.brain.close()

    def test_interrupted_task_recovers_as_failed(self):
        with tempfile.TemporaryDirectory() as directory:
            path=str(Path(directory)/"office.sqlite")
            first=Office(path)
            try:
                t=first.engine.create("Briefing fictício","briefing",{"synthetic":True,"itens":["Reunião fictícia"]})
                tid=t["id"]
                first.engine.assign(tid,"executivo")
                task=first.engine.tasks[tid]
                task["state"]="running"
                first.engine._record(task,"executivo","started")
            finally:
                first.brain.close()
            second=Office(path)
            try:
                self.assertEqual(second.engine.tasks[tid]["state"],"failed")
                self.assertEqual(second.engine.events[-1]["action"],"interrupted")
            finally:
                second.brain.close()
