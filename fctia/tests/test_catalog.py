import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "runtime"))
from skills import SKILLS, execute

CASES = {
    "planejamento": {"objetivo":"Evento fictício","etapas":["Preparar pauta"]},
    "delegacao": {"responsavel":"Agente fictício","atividade":"Preparar pauta"},
    "revisao": {"entregavel":"Minuta fictícia","criterios":["Clareza"]},
    "agenda_simulada": {"compromissos":["Reunião fictícia"]},
    "briefing": {"itens":["Reunião fictícia"]},
    "minuta_email": {"destinatario":"Setor fictício","assunto":"Teste","texto":"Minuta"},
    "minuta_oficio": {"destinatario":"Setor fictício","assunto":"Teste","texto":"Minuta"},
    "minuta_ata": {"reuniao":"Reunião fictícia","pautas":["Pauta"],"deliberacoes":["Proposta"]},
    "relatorio": {"titulo":"Relatório fictício","observacoes":["Observação"]},
    "classificar_solicitacao": {"descricao":"Computador sem rede"},
    "propor_ordem": {"descricao":"Reparo fictício","setor":"Tecnologia"},
    "acompanhar_prazo": {"atividade":"Teste","prazo":"2027-01-03","referencia":"2027-01-01"},
}

class CatalogTest(unittest.TestCase):
    def test_all_profile_skills(self):
        template = Path(__file__).resolve().parents[1] / "templates" / "organization-v01.json"
        profiles = json.loads(template.read_text(encoding="utf-8"))["agents"]
        expected = {s for agent in profiles for s in agent["skills"]}
        self.assertEqual(expected, set(SKILLS))
        self.assertEqual(expected, set(CASES))
        for name, payload in CASES.items():
            with self.subTest(skill=name):
                result = execute(name, dict(payload, synthetic=True))
                self.assertEqual(result["status"], "draft")
                self.assertTrue(result["requires_human_review"])
                self.assertFalse(result["external_action"])
                self.assertTrue(result["result"])
    def test_all_skills_reject_missing_flag(self):
        for name, payload in CASES.items():
            with self.subTest(skill=name):
                with self.assertRaises(ValueError):
                    execute(name, payload)
    def test_deadline(self):
        self.assertIn("Restam 2 dia(s)",execute("acompanhar_prazo",dict(CASES["acompanhar_prazo"],synthetic=True))["result"])
