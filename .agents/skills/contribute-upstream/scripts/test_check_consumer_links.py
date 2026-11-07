#!/usr/bin/env python3
import os
import tempfile
import unittest
from unittest import mock

import check_consumer_links as consumer


class CheckConsumerLinksTest(unittest.TestCase):
    def test_undefined_ref_heading_slug_is_guidemissing(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "doc.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("# [Guide][missing]\n")
            anchors = consumer.heading_anchors(path)
            self.assertIn("guidemissing", anchors)
            self.assertNotIn("guide", anchors)

    def test_defined_ref_heading_slug_is_guide(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "doc.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("# [Guide][label]\n\n[label]: ./target.md\n")
            anchors = consumer.heading_anchors(path)
            self.assertIn("guide", anchors)

    def test_tab_in_heading_slug_is_hello_world(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "doc.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("# Hello\tWorld\n")
            anchors = consumer.heading_anchors(path)
            self.assertIn("hello-world", anchors)

    def test_empty_angle_ref_dest_heading_slug_is_guide(self):
        with tempfile.TemporaryDirectory() as root:
            path = os.path.join(root, "doc.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("# [Guide][x]\n\n[x]: <>\n")
            anchors = consumer.heading_anchors(path)
            self.assertIn("guide", anchors)
            self.assertNotIn("guidex", anchors)

    def test_missing_consumer_file_does_not_use_core_readme(self):
        with tempfile.TemporaryDirectory() as consumer_root:
            with mock.patch.dict(os.environ, {"CONSUMER_ROOT": consumer_root}):
                self.assertIsNone(consumer.deployed_file("README.md"))
                self.assertIsNone(consumer.deployed_source("README.md"))


if __name__ == "__main__":
    unittest.main()
