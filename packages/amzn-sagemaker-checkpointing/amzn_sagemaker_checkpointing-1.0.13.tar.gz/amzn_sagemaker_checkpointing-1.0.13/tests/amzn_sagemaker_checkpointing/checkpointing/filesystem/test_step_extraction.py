import os
import unittest
from unittest import TestCase

from amzn_sagemaker_checkpointing.checkpointing.filesystem.exceptions import (
    SageMakerTieredStorageError,
)
from amzn_sagemaker_checkpointing.checkpointing.filesystem.filesystem import (
    _get_step_val,
)


class TestStepValueExtraction(TestCase):
    def test_explicit_step_precedence(self):
        """Test explicit step values always take precedence over path extraction."""
        self._assert_step_extraction(
            [
                (0, "/some/path", 0),
                (0, "/any/path/step_999", 0),
                (42, "/path/step_123/file", 42),
                (9999, "/step_0/checkpoint", 9999),
                (42, "/some/path/step_100/checkpoint", 42),
            ]
        )

    def test_step_from_path(self):
        """Test step extraction from various path formats."""
        self._assert_step_extraction_from_path(
            [
                ("/some/path/step_123/checkpoint", 123),
                ("/some/path/step_456", 456),
                ("/some/path/step_0/checkpoint", 0),
                ("/some/path/step_999999/checkpoint", 999999),
                (os.path.join("/some/path", "step_789", "checkpoint"), 789),
                ("/root/training/experiment_1/step_42/model.pt", 42),
                ("/very/long/nested/path/with/many/dirs/step_12345/checkpoint.bin", 12345),
                ("/path/with/step_100/nested/step_200/file.txt", 100),
                ("./relative/path/step_5/data", 5),
                ("/step_0/beginning", 0),
                ("/end/step_9999", 9999),
                ("/path/step_100/nested/step_200", 100),
                ("/path/step_100123/checkpoint", 100123),
                ("/root/parent/child/grandchild/step_42/file.txt", 42),
            ]
        )

    def test_invalid_paths(self):
        """Test step extraction with invalid path formats raises errors."""
        self._assert_raises_error(
            [
                "/no/step/pattern/here",
                "/path/step_/incomplete",
                "/path/step_abc/invalid_number",
                "",
                None,
                "/some/path/without/step",
                "/some/path/step_abc/checkpoint",
                "/some/path/step_/checkpoint",
                "/path/step_12.5/float",
            ]
        )

    def test_negative_step_in_path(self):
        """Test that negative step numbers in paths are parsed as integers."""
        result = _get_step_val(-1, "/path/step_-5/negative")
        self.assertEqual(result, -5)  # TODO Fix this case while refactoring code - this need to fail

    def _assert_step_extraction(self, test_cases):
        """Helper to assert step extraction for multiple test cases."""
        for *args, expected in test_cases:
            with self.subTest(args=args):
                result = _get_step_val(*args)
                self.assertEqual(result, expected)

    def _assert_step_extraction_from_path(self, test_cases):
        """Helper to assert step extraction from path (prepends -1 for step arg)."""
        self._assert_step_extraction([(-1, path, expected) for path, expected in test_cases])

    def _assert_raises_error(self, paths):
        """Helper to assert SageMakerTieredStorageError for invalid paths."""
        for path in paths:
            with self.subTest(path=path):
                with self.assertRaises(SageMakerTieredStorageError):
                    _get_step_val(-1, path)


if __name__ == "__main__":
    unittest.main()
