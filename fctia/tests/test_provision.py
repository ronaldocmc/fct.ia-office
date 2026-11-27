import sys
import json
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "deploy"))
from provision import API, provision, TEMPLATE

class FakeAPI:
    def __init__(self):
        self.company = None
        self.agents = []
    def call(self, method, path, payload=None):
        if path == "/companies":
            if method == "GET":
                return [self.company] if self.company else []
            self.company = dict(payload, id="11111111-1111-4111-8111-111111111111")
            return self.company
        if path.endswith("/agents"):
            if method == "GET":
                return list(self.agents)
            assert payload["adapterConfig"]["command"] == "/bin/false"
            assert not payload["runtimeConfig"]["heartbeat"]["enabled"]
            agent = dict(payload, id=payload["setupId"], lifecycleHolds=["setup"])
            self.agents.append(agent)
            return agent
        if method == "PATCH":
            self.company.update(payload)
            return self.company
        raise AssertionError((method,path))

class ProvisionTest(unittest.TestCase):
    def test_create_and_repeat(self):
        api = FakeAPI()
        spec = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        first = provision(api, spec)
        second = provision(api, spec)
        self.assertEqual(first, second)
        self.assertEqual(len(api.agents), 4)
        self.assertTrue(api.company["requireBoardApprovalForNewAgents"])
        self.assertEqual(api.agents[1]["reportsTo"], first["agents"]["coordenador"])
    def test_external_target_rejected(self):
        with self.assertRaises(ValueError):
            API("https://example.org", "test")
    def test_unmanaged_agent_rejected(self):
        api = FakeAPI()
        spec = json.loads(TEMPLATE.read_text(encoding="utf-8"))
        provision(api,spec)
        api.agents.append({"id":"unmanaged","metadata":{}})
        with self.assertRaises(RuntimeError):
            provision(api,spec)
