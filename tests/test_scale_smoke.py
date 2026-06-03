from __future__ import annotations

import unittest

from scripts import scale_smoke


class ScaleSmokeTests(unittest.TestCase):
    def test_generated_scale_repo_uses_expected_query_indexes(self) -> None:
        payload = scale_smoke.run_scale_smoke(record_count=120)

        self.assertTrue(payload["ok"], payload["violations"])
        self.assertEqual(payload["generated_records"], 120)
        self.assertGreaterEqual(payload["records_loaded_including_ontology"], 120)
        self.assertGreater(payload["graph"]["edge_count"], 0)
        self.assertTrue(payload["query_plans"])
        self.assertTrue(
            all(plan["uses_index"] for plan in payload["query_plans"]),
            payload["query_plans"],
        )


if __name__ == "__main__":
    unittest.main()
