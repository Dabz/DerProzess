from unittest import TestCase
from lib import properties


class TestParseProperties(TestCase):
    def test_parse_properties(self):
        fixed = {"properties": { "a": 1, "b": 2}}
        ranged = {"properties": {"c": [1, 2]}}
        prop = {"properties": {"c": 3, "a": 2}, "brokers": {"a": "c2"}}
        rf, rr = properties.parse_properties(prop, fixed, ranged)

        self.assertEqual(rf["properties"]["c"], 3)
        self.assertEqual(rf["properties"]["b"], 2)
        self.assertEqual(rf["brokers"]["a"], "c2")
        self.assertEqual(rr["properties"]["c"], [1, 2])
        self.assertEqual(rr["properties"]["a"], [1, 2])
