import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"runtime"))
from skills import execute

class SkillsTest(unittest.TestCase):
    def test_office(self):
        r=execute("minuta_oficio",{"synthetic":True,"destinatario":"Setor fictício","assunto":"Teste","texto":"Minuta"})
        self.assertIn("OFÍCIO EXPERIMENTAL",r["result"])
        self.assertTrue(r["requires_human_review"])
        self.assertFalse(r["external_action"])
    def test_briefing(self):
        self.assertIn("- Reunião fictícia",execute("briefing",{"synthetic":True,"itens":["Reunião fictícia"]})["result"])
    def test_classification(self):
        self.assertIn("tecnologia",execute("classificar_solicitacao",{"synthetic":True,"descricao":"Computador sem rede"})["result"])
    def test_reject_real_data_flag(self):
        with self.assertRaises(ValueError):
            execute("briefing",{"itens":[]})
    def test_unknown_skill(self):
        with self.assertRaises(ValueError):
            execute("unknown",{"synthetic":True})
