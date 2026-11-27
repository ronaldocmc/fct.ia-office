import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.tasks import TaskEngine

class TaskTest(unittest.TestCase):
    def setUp(self):
        self.engine=TaskEngine()
        self.payload={"synthetic":True,"destinatario":"Setor fictício","assunto":"Teste","texto":"Minuta"}
    def task(self):
        return self.engine.create("Ofício experimental","minuta_oficio",self.payload)["id"]
    def test_complete_flow(self):
        t=self.task()
        self.engine.assign(t,"documental")
        result=self.engine.run(t)
        self.assertEqual(result["state"],"awaiting_review")
        self.assertEqual(self.engine.review(t,True,"gestor-demo","Conferido")["state"],"approved")
        self.assertEqual([e["action"] for e in self.engine.events],["created","assigned","started","draft_generated","approved"])
    def test_wrong_profile_and_premature_review(self):
        t=self.task()
        with self.assertRaises(ValueError): self.engine.assign(t,"executivo")
        with self.assertRaises(ValueError): self.engine.run(t)
        with self.assertRaises(ValueError): self.engine.review(t,True,"gestor-demo","Conferido")
    def test_revision(self):
        t=self.task()
        self.engine.assign(t,"documental")
        self.engine.run(t)
        self.engine.review(t,False,"gestor-demo","Corrigir texto")
        self.engine.revise(t,dict(self.payload,texto="Corrigido"))
        self.engine.assign(t,"documental")
        result=self.engine.run(t)
        self.assertIn("Corrigido",result["result"]["result"])
    def test_failed_execution(self):
        t=self.engine.create("Ofício incompleto","minuta_oficio",{"synthetic":True})["id"]
        self.engine.assign(t,"documental")
        with self.assertRaises(ValueError): self.engine.run(t)
        self.assertEqual(self.engine.tasks[t]["state"],"failed")
