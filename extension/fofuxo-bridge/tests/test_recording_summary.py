"""Pure regressions for vertex movement attribution in compact summaries."""

import importlib.util
from pathlib import Path
import unittest


source = Path(__file__).resolve().parents[1] / "recording.py"
spec = importlib.util.spec_from_file_location("recording_summary_under_test", source)
recording = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recording)


class MovementAttributionTests(unittest.TestCase):
    def summarize(self, regions):
        return recording.summarize([{
            "op": "TRANSFORM_OT_translate",
            "moved": {"1": [1, 0, 0], "2": [0, 2, 0]},
            "regions": regions,
        }])

    def test_no_regions(self):
        self.assertEqual(self.summarize({})["unattributed_vertex_samples"], 2)

    def test_empty_named_region(self):
        self.assertEqual(self.summarize({"TestRegion": []})["unattributed_vertex_samples"], 2)

    def test_partial_membership(self):
        result = self.summarize({"TestRegion": [1]})
        self.assertEqual(result["unattributed_vertex_samples"], 1)
        self.assertEqual(result["moves_by_region"]["TestRegion"]["net_mm"], [1, 0, 0])

    def test_complete_membership(self):
        self.assertEqual(self.summarize({"TestRegion": [1, 2]})["unattributed_vertex_samples"], 0)

    def test_overlapping_membership(self):
        self.assertEqual(self.summarize({"FirstRegion": [1], "SecondRegion": [1]})["unattributed_vertex_samples"], 1)


if __name__ == "__main__":
    unittest.main()
