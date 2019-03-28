from unittest import TestCase
from lib import properties

class TestGenPropertiesToTest(TestCase):
    def test_gen_properties_to_test(self):
        prop = {"properties": {"linger.ms": 1}, "brokers": {"instance-type": "c2"}}
        rangeprop = {"properties": {"batch.size": [100, 200]}, "brokers": {"broker-count": [1, 2]}}
        tests = list(properties.gen_properties_to_test(prop, rangeprop))
        self.assertEqual(4, len(tests))
