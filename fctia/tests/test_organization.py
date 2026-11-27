import json
import unittest
from pathlib import Path

class OrganizationTest(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "templates" / "organization-v01.json"
        self.spec = json.loads(path.read_text(encoding="utf-8"))

    def test_hierarchy(self):
        agents = self.spec["agents"]
        ids = {a["id"] for a in agents}
        self.assertEqual(len(ids), 4)
        self.assertEqual(len(agents), 4)
        roots = [a for a in agents if a["reportsTo"] is None]
        self.assertEqual([a["id"] for a in roots], ["coordenador"])
        for a in agents:
            if a["id"] != "coordenador":
                self.assertEqual(a["reportsTo"], "coordenador")

    def test_safe_defaults(self):
        self.assertTrue(self.spec["organization"]["syntheticDataOnly"])
        for a in self.spec["agents"]:
            self.assertIsNone(a["runtime"])
            self.assertFalse(a["automaticExecution"])
            self.assertFalse(a["externalActions"])
            self.assertTrue(a["approvalRequired"])
            self.assertTrue(a["skills"])
