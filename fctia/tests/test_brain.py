import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"brain"))
from store import Brain

class BrainTest(unittest.TestCase):
    def test_review_and_scope(self):
        brain=Brain(":memory:")
        self.addCleanup(brain.close)
        ident=brain.propose("direcao","Regra fictícia de agenda","documento fictício")
        self.assertEqual(brain.search("direcao","agenda"),[])
        with self.assertRaises(LookupError):
            brain.approve("secretaria",ident,"revisor")
        brain.approve("direcao",ident,"revisor")
        self.assertEqual(brain.search("secretaria","agenda"),[])
        self.assertEqual(brain.search("direcao","agenda")[0]["source"],"documento fictício")
