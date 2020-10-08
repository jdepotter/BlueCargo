import unittest
from whcorp import WHCorpJob
import json

class TestWHCorpJob(unittest.TestCase):
    def test_validate_shift_match(self):
        job = WHCorpJob({"name": "WHCorp", "url": None})

        val = None
        self.assertDictEqual(job._v.validate_shift_match(val), {"shift": None})

        val = "Morning (10am - 2pm)"
        self.assertDictEqual(job._v.validate_shift_match(val), {"shift": "Morning", "hours": f"10am - 2pm"})

        val = "  Morning (10am - 2pm)  "
        self.assertDictEqual(job._v.validate_shift_match(val), {"shift": "Morning", "hours": f"10am - 2pm"})

        val = "Afternoon (1pm - 05pm)"
        self.assertDictEqual(job._v.validate_shift_match(val), {"shift": "Afternoon", "hours": f"1pm - 05pm"})

        val = "Evening (1pm - 05pm)"
        self.assertIsNone(job._v.validate_shift_match(val))