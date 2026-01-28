"""
Unit tests for request_transformer module
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from request_transformer import (
    inject_parameters,
    validate_user_input,
    transform_request_to_workflow,
    load_workflow_template,
    download_media_from_url
)


class TestRequestTransformer(unittest.TestCase):
    """Test cases for request transformer"""

    def setUp(self):
        """Set up test fixtures"""
        self.sample_workflow = {
            "106": {
                "inputs": {
                    "image": "{{reference_image_filename}}"
                }
            },
            "130": {
                "inputs": {
                    "video": "{{dance_video_filename}}"
                }
            },
            "203": {
                "inputs": {
                    "value": "{{width}}"
                }
            },
            "204": {
                "inputs": {
                    "value": "{{height}}"
                }
            },
            "238": {
                "inputs": {
                    "value": "{{cfg}}"
                }
            },
            "348": {
                "inputs": {
                    "seed": "{{seed}}"
                }
            },
            "349": {
                "inputs": {
                    "steps": "{{steps}}"
                }
            },
            "368": {
                "inputs": {
                    "positive_prompt": "{{prompt}}"
                }
            }
        }

        self.sample_user_input = {
            "images": {
                "reference_image": "https://example.com/reference.jpg"
            },
            "videos": {
                "dance_video": "https://example.com/dance.mp4"
            },
            "prompt": "a person dancing",
            "width": 416,
            "height": 672,
            "steps": 6,
            "cfg": 1.0,
            "seed": 42
        }

    def test_inject_parameters_strings(self):
        """Test string parameter injection"""
        params = {
            "reference_image_filename": "test.jpg",
            "dance_video_filename": "test.mp4",
            "prompt": "test prompt"
        }

        result = inject_parameters(self.sample_workflow, params)

        self.assertEqual(result["106"]["inputs"]["image"], "test.jpg")
        self.assertEqual(result["130"]["inputs"]["video"], "test.mp4")
        self.assertEqual(result["368"]["inputs"]["positive_prompt"], "test prompt")

    def test_inject_parameters_numbers(self):
        """Test numeric parameter injection"""
        params = {
            "width": 512,
            "height": 768,
            "steps": 10,
            "cfg": 2.5,
            "seed": 123
        }

        result = inject_parameters(self.sample_workflow, params)

        self.assertEqual(result["203"]["inputs"]["value"], 512)
        self.assertEqual(result["204"]["inputs"]["value"], 768)
        self.assertEqual(result["349"]["inputs"]["steps"], 10)
        self.assertEqual(result["238"]["inputs"]["value"], 2.5)
        self.assertEqual(result["348"]["inputs"]["seed"], 123)

    def test_inject_parameters_defaults(self):
        """Test default parameter values"""
        params = {}
        result = inject_parameters(self.sample_workflow, params)

        # Check defaults are applied
        self.assertEqual(result["203"]["inputs"]["value"], 416)
        self.assertEqual(result["204"]["inputs"]["value"], 672)
        self.assertEqual(result["349"]["inputs"]["steps"], 6)
        self.assertEqual(result["238"]["inputs"]["value"], 1.0)
        self.assertEqual(result["348"]["inputs"]["seed"], -1)

    def test_validate_user_input_success(self):
        """Test successful validation"""
        try:
            validate_user_input(self.sample_user_input)
        except ValueError:
            self.fail("validate_user_input raised ValueError unexpectedly")

    def test_validate_user_input_missing_reference_image(self):
        """Test validation fails without reference_image"""
        invalid_input = {
            "images": {},
            "videos": {"dance_video": "http://example.com/dance.mp4"}
        }

        with self.assertRaises(ValueError) as context:
            validate_user_input(invalid_input)

        self.assertIn("reference_image", str(context.exception))

    def test_validate_user_input_missing_dance_video(self):
        """Test validation fails without dance_video"""
        invalid_input = {
            "images": {"reference_image": "http://example.com/ref.jpg"},
            "videos": {}
        }

        with self.assertRaises(ValueError) as context:
            validate_user_input(invalid_input)

        self.assertIn("dance_video", str(context.exception))

    def test_validate_user_input_invalid_width(self):
        """Test validation fails with invalid width"""
        invalid_input = self.sample_user_input.copy()
        invalid_input["width"] = -100

        with self.assertRaises(ValueError) as context:
            validate_user_input(invalid_input)

        self.assertIn("width", str(context.exception))

    def test_validate_user_input_invalid_steps(self):
        """Test validation fails with invalid steps"""
        invalid_input = self.sample_user_input.copy()
        invalid_input["steps"] = 0

        with self.assertRaises(ValueError) as context:
            validate_user_input(invalid_input)

        self.assertIn("steps", str(context.exception))

    @patch('request_transformer.requests.get')
    @patch('request_transformer.os.makedirs')
    def test_download_media_from_url_success(self, mock_makedirs, mock_get):
        """Test successful media download"""
        # Mock response
        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"test data"]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('request_transformer.COMFYUI_INPUT_DIR', tmpdir):
                filename = download_media_from_url("http://example.com/test.jpg", "image")

                self.assertTrue(filename.endswith(".jpg"))
                self.assertTrue(os.path.exists(os.path.join(tmpdir, filename)))

    def test_download_media_from_url_empty(self):
        """Test download fails with empty URL"""
        with self.assertRaises(ValueError):
            download_media_from_url("", "image")

    def test_load_workflow_template_success(self):
        """Test loading workflow template from file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.sample_workflow, f)
            temp_path = f.name

        try:
            result = load_workflow_template(temp_path)
            self.assertEqual(result, self.sample_workflow)
        finally:
            os.unlink(temp_path)

    def test_load_workflow_template_not_found(self):
        """Test loading non-existent template"""
        with self.assertRaises(FileNotFoundError):
            load_workflow_template("/nonexistent/path.json")

    @patch('request_transformer.download_media_from_url')
    def test_transform_request_to_workflow_success(self, mock_download):
        """Test complete transformation"""
        mock_download.side_effect = ["ref.jpg", "dance.mp4"]

        result = transform_request_to_workflow(
            self.sample_user_input,
            self.sample_workflow
        )

        # Verify media download was called
        self.assertEqual(mock_download.call_count, 2)

        # Verify parameters were injected
        self.assertEqual(result["106"]["inputs"]["image"], "ref.jpg")
        self.assertEqual(result["130"]["inputs"]["video"], "dance.mp4")
        self.assertEqual(result["368"]["inputs"]["positive_prompt"], "a person dancing")
        self.assertEqual(result["203"]["inputs"]["value"], 416)
        self.assertEqual(result["204"]["inputs"]["value"], 672)
        self.assertEqual(result["349"]["inputs"]["steps"], 6)
        self.assertEqual(result["238"]["inputs"]["value"], 1.0)
        self.assertEqual(result["348"]["inputs"]["seed"], 42)


if __name__ == '__main__':
    unittest.main()
