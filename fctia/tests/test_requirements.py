"""Structural checks for the requirements baseline; not functional tests."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "requirements"
EXPECTED_COUNTS = [6, 9, 9, 11, 7, 14, 7, 7, 8, 9]


class RequirementsTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "traceability.json").read_text(encoding="utf-8"))
        self.rows = self.data["requirements"]
        self.spec = (ROOT / "REQUISITOS-FUNCIONAIS.md").read_text(encoding="utf-8")

    def test_ids(self):
        self.assertEqual([r["id"] for r in self.rows],
                         [f"RF{i:02d}" for i in range(1, 88)])

    def test_modules(self):
        expected = [f"M{i:02d}" for i, count in enumerate(EXPECTED_COUNTS, 1)
                    for _ in range(count)]
        self.assertEqual([r["module"] for r in self.rows], expected)

    def test_spec_matches_matrix(self):
        entries = re.findall(r"^\| (RF\d+) \| (.*?) \|$", self.spec, re.M)
        self.assertEqual(entries, [(r["id"], r["requirement"]) for r in self.rows])

    def test_traceability_fields(self):
        required = {"id", "module", "requirement", "version", "status",
                    "coverage", "strategy", "evidence", "acceptance_test",
                    "validation_result"}
        for row in self.rows:
            with self.subTest(id=row["id"]):
                self.assertTrue(required <= row.keys())
                if row["status"] == "validado":
                    for key in ("evidence", "acceptance_test", "validation_result"):
                        self.assertTrue(row[key], key)


if __name__ == "__main__":
    unittest.main()
