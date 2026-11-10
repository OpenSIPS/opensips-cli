import os
import sys
import unittest

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from opensipscli.config import OpenSIPSCLIConfig


class TestCustomOptionsEdgeCases(unittest.TestCase):
    def test_option_without_value_does_not_raise(self):
        cfg = OpenSIPSCLIConfig()
        cfg.set_custom_options(["foo"])
        self.assertNotIn("foo", cfg.custom_options)

    def test_empty_value_clears_existing_override(self):
        cfg = OpenSIPSCLIConfig()
        cfg.set_option("foo", "bar")
        cfg.set_custom_options(["foo"])
        self.assertNotIn("foo", cfg.custom_options)

    def test_key_value_still_sets_override(self):
        cfg = OpenSIPSCLIConfig()
        cfg.set_custom_options(["foo=bar"])
        self.assertEqual(cfg.custom_options["foo"], "bar")


if __name__ == "__main__":
    unittest.main()
