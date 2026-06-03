from __future__ import annotations

import json
import unittest

from scripts import validate_with_timing


class ValidateWithTimingTests(unittest.TestCase):
    def test_diff_review_output_summary_keeps_base_loader_counts(self) -> None:
        summary = validate_with_timing.output_summary(
            "diff_review",
            json.dumps(
                {
                    "record_delta": {"total": {"added": 1, "modified": 2}},
                    "timings_ms": {
                        "base_record_load_ms": 123,
                        "base_record_path_count": 426,
                        "base_record_blob_count": 420,
                        "base_record_git_process_count": 2,
                    },
                    "graph_impact": {"after_node_count": 5, "after_edge_count": 8},
                    "warnings": [{"code": "fixture"}],
                    "errors": [],
                }
            ),
        )

        self.assertEqual(summary["record_delta"], {"added": 1, "modified": 2})
        self.assertEqual(summary["base_record_load_ms"], 123)
        self.assertEqual(summary["base_record_path_count"], 426)
        self.assertEqual(summary["base_record_blob_count"], 420)
        self.assertEqual(summary["base_record_git_process_count"], 2)
        self.assertEqual(summary["after_node_count"], 5)
        self.assertEqual(summary["warning_count"], 1)
        self.assertEqual(summary["error_count"], 0)


if __name__ == "__main__":
    unittest.main()
