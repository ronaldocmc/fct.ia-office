import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from fctia.local_api import Office

class GraphTest(unittest.TestCase):
    def setUp(self):
        self.office=Office()
        self.addCleanup(self.office.brain.close)
    def propose(self,scope,content,source,approve=True):
        ident=self.office.brain.propose(scope,content,source)
        if approve:
            self.office.brain.approve(scope,ident,"gestor-demo")
        return ident
    def graph(self,scope,query=""):
        from urllib.parse import urlencode
        return self.office.dispatch("GET","/api/brain/graph?"+urlencode({"scope":scope,"q":query}))
    def test_provenance_and_scope(self):
        kid=self.propose("executivo","Briefing fictício","task:001")
        self.propose("executivo","Proposta pendente","task:002",False)
        self.propose("documental","Ofício fictício","task:003")
        g=self.graph("executivo")
        self.assertEqual(g["total"],1)
        self.assertEqual({n["id"] for n in g["nodes"]},{"scope:executivo","knowledge:"+kid,"source:task:001"})
        self.assertEqual(g["edges"],[
            {"from":"scope:executivo","to":"knowledge:"+kid,"relation":"possui conhecimento"},
            {"from":"knowledge:"+kid,"to":"source:task:001","relation":"derivado de"}])
        self.assertEqual(self.graph("executivo","Ofício")["total"],0)
    def test_shared_source(self):
        self.propose("documental","Minuta A","task:001")
        self.propose("documental","Minuta B","task:001")
        g=self.graph("documental")
        self.assertEqual(sum(n["kind"]=="source" for n in g["nodes"]),1)
        self.assertEqual(len(g["edges"]),4)
    def test_limit(self):
        for i in range(51):
            self.propose("executivo","Briefing "+str(i),"task:"+str(i))
        g=self.graph("executivo")
        self.assertEqual(g["total"],51)
        self.assertTrue(g["truncated"])
        self.assertEqual(sum(n["kind"]=="knowledge" for n in g["nodes"]),50)
    def test_invalid_scope(self):
        with self.assertRaises(ValueError):
            self.graph("unknown")
