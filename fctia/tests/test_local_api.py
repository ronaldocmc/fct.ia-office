import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from fctia.local_api import Office

class OfficeTest(unittest.TestCase):
    def setUp(self):
        self.office=Office()
        self.addCleanup(self.office.brain.close)

    def call(self, method, path, data=None):
        return self.office.dispatch(method,path,data)

    def test_task_to_knowledge(self):
        t=self.call("POST","/api/tasks",{"title":"Ofício fictício","skill":"minuta_oficio","payload":{"synthetic":True,"destinatario":"Setor fictício","assunto":"Teste","texto":"Agenda fictícia"}})
        path="/api/tasks/"+t["id"]
        with self.assertRaises(ValueError):
            self.call("POST",path+"/knowledge")
        self.call("POST",path+"/assign",{"agent":"documental"})
        self.call("POST",path+"/run")
        self.call("POST",path+"/review",{"approve":True,"comment":"Conferido"})
        k=self.call("POST",path+"/knowledge")
        self.assertEqual(k,self.call("POST",path+"/knowledge"))
        self.assertEqual(len(self.call("GET","/api/brain/pending")),1)
        self.assertEqual(self.call("GET","/api/brain?scope=documental&q=Agenda"),[])
        self.call("POST","/api/brain/approve",k)
        self.assertEqual(len(self.call("GET","/api/brain?scope=documental&q=Agenda")),1)
        self.assertEqual(self.call("GET","/api/brain?scope=executivo&q=Agenda"),[])
        self.assertEqual(len(self.call("GET","/api/events")),5)

    def test_invalid_scope(self):
        with self.assertRaises(ValueError):
            self.call("GET","/api/brain?scope=unknown")

    def test_profiles(self):
        self.assertEqual(len(self.call("GET","/api/agents")),4)
