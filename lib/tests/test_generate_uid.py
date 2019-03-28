from unittest import TestCase
from lib import properties


class TestGenerateUid(TestCase):
    def test_generate_uid(self):
        prop = {"properties": {"acks": "all", "linger.ms": 1, "batch.size": 1000}}
        ranged_properties = {"properties": {"acks": ["all", "1"], "linger.ms": [1, 10]}}
        uid = properties.generate_uid(prop, ranged_properties)
        self.assertEqual(uid, "linger.ms-1_acks-all")
