"""Protect the public saved-data walkthrough from source-schema drift."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.run_refresh_replay import materialize  # noqa: E402
from norway_company_agent.refresh import diff_datasets  # noqa: E402


class SavedRefreshReplayTests(unittest.TestCase):
    def test_expected_changes_have_evidence_and_repeat_is_stable(self):
        manifest = json.loads((ROOT / "tests/fixtures/refresh-snapshots.json").read_text(encoding="utf-8"))
        modules = set(manifest["modules"])
        old, _ = materialize(manifest["profiles"], manifest["snapshots"]["old"], modules)
        new, _ = materialize(manifest["profiles"], manifest["snapshots"]["new"], modules)
        events = diff_datasets(old, new)

        expected = {(item["organisation_number"], item["field"]) for item in manifest["expected_changes"]}
        self.assertEqual({(event["organisation_number"], event["field"]) for event in events}, expected)
        self.assertTrue(all(event.get("old_content_sha256") and event.get("new_content_sha256") for event in events))
        self.assertEqual(diff_datasets(new, new), [])


if __name__ == "__main__":
    unittest.main()
