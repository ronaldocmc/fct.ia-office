import os
import tempfile
import unittest
from pathlib import Path
from copy import deepcopy
from fctia.brain.store import Brain
from fctia.brain.postgres_store import PostgresBrain, digest, vector_literal
from fctia.runtime.tasks import TaskEngine
from fctia.persistence.import_sqlite import migrate
from fctia.persistence.postgres import ConflictError

DSN=os.getenv("FCTIA_TEST_DSN")
class VectorTest(unittest.TestCase):
    def test_validation(self):
        self.assertTrue(vector_literal([1]+[0]*383).startswith("[1.0,"))
        for v in ([1],[0]*384,[float("nan")]*384):
            with self.assertRaises(ValueError):
                vector_literal(v)

@unittest.skipUnless(DSN,"Dedicated disposable PostgreSQL required")
class Integration(unittest.TestCase):
    def test_migration_and_brain(self):
        with tempfile.TemporaryDirectory() as temp:
            path=str(Path(temp)/"source.sqlite")
            brain=Brain(path)
            engine=TaskEngine(brain.db)
            agent=next(iter(engine.profiles.values()))
            task=engine.create("Synthetic test",agent["skills"][0],{"synthetic":True})
            ident=brain.propose(agent["id"],"Synthetic test knowledge","fixture")
            brain.approve(agent["id"],ident,"test")
            brain.close()
            self.assertEqual(migrate(path)["tasks"],1)
            self.assertEqual(migrate(path,DSN,True)["events"],1)
            with self.assertRaises(ValueError):
                migrate(path,DSN,True)
            pg=PostgresBrain(DSN)
            try:
                self.assertEqual(pg.get_task(task["id"]),task)
                self.assertEqual(len(pg.list_events()),1)
                self.assertEqual(pg.search(agent["id"],"Synthetic")[0]["id"],ident)
                self.assertEqual(pg.search("another-scope","Synthetic"),[])
                v=[1]+[0]*383
                pg.embed(agent["id"],ident,"test-model:v1",v,digest("Synthetic test knowledge"))
                self.assertEqual(pg.semantic_search(agent["id"],"test-model:v1",v)[0]["id"],ident)
                self.assertEqual(pg.semantic_search("another-scope","test-model:v1",v),[])
                self.assertEqual(pg.semantic_search(agent["id"],"other-model",v),[])
                pending=pg.propose(agent["id"],"Pending","fixture")
                with self.assertRaises(LookupError):
                    pg.embed(agent["id"],pending,"test-model:v1",v,digest("Pending"))
                with self.assertRaises(LookupError):
                    pg.approve("another-scope",pending,"test")
                self.assertEqual(pg.pending(agent["id"])[0]["id"],pending)
                changed=deepcopy(task)
                changed.update(state="assigned",agent=agent["id"])
                event=dict(task_id=task["id"],state="assigned",actor="test",action="assigned",at="2026-01-01T00:00:00+00:00")
                pg.save_task(changed,event,task)
                with self.assertRaises(ConflictError):
                    pg.save_task(changed,event,task)
                self.assertEqual(len(pg.list_events()),2)
            finally:
                pg.close()
            pg=PostgresBrain(DSN)
            try:
                self.assertEqual(pg.get_task(task["id"])["state"],"assigned")
            finally:
                pg.close()

if __name__=="__main__":
    unittest.main()
