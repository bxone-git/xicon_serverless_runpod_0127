"""
Request Transformer Module

Transforms user's custom request format into ComfyUI workflow with injected parameters.
Handles media downloads (images, videos) and parameter mapping.
"""

import json
import os
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ComfyUI input directory
COMFYUI_INPUT_DIR = "/comfyui/input"

# Parameter mapping to workflow nodes
PARAM_MAPPING = {
    "reference_image": {"node": "106", "field": "image"},
    "dance_video": {"node": "130", "field": "video"},
    "prompt": {"node": "368", "field": "positive_prompt"},
    "width": {"node": "203", "field": "value"},
    "height": {"node": "204", "field": "value"},
    "steps": {"node": "349", "field": "steps"},
    "cfg": {"node": "238", "field": "value"},
    "seed": {"node": "348", "field": "seed"}
}


def download_media_from_url(url: str, media_type: str = "image") -> str:
    """
    Download media from URL and save to ComfyUI input directory.

    Args:
        url: URL of the media file
        media_type: Type of media ("image" or "video")

    Returns:
        str: Filename of the saved media

    Raises:
        ValueError: If URL is empty or invalid
        requests.RequestException: If download fails
    """
    if not url:
        raise ValueError("URL cannot be empty")

    try:
        # Generate unique filename with appropriate extension
        ext = ".jpg" if media_type == "image" else ".mp4"
        filename = f"{uuid.uuid4()}{ext}"
        save_path = os.path.join(COMFYUI_INPUT_DIR, filename)

        # Ensure input directory exists
        os.makedirs(COMFYUI_INPUT_DIR, exist_ok=True)

        # Download media with timeout
        logger.info(f"Downloading {media_type} from {url}")
        response = requests.get(url, timeout=120, stream=True)
        response.raise_for_status()

        # Save to file
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Successfully downloaded {media_type} to {filename}")
        return filename

    except requests.RequestException as e:
        logger.error(f"Failed to download media from {url}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error downloading media: {str(e)}")
        raise


def inject_parameters(workflow: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Replace {{placeholders}} in workflow with actual values.

    Args:
        workflow: ComfyUI workflow dict
        params: Parameters to inject

    Returns:
        Dict: Modified workflow with injected parameters
    """
    # Convert workflow to string for placeholder replacement
    workflow_str = json.dumps(workflow)

    # Replace string placeholders
    workflow_str = workflow_str.replace(
        "{{reference_image_filename}}",
        params.get("reference_image_filename", "")
    )
    workflow_str = workflow_str.replace(
        "{{dance_video_filename}}",
        params.get("dance_video_filename", "")
    )
    workflow_str = workflow_str.replace(
        "{{prompt}}",
        params.get("prompt", "")
    )

    # Replace numeric placeholders (handle JSON number conversion)
    workflow_str = workflow_str.replace(
        '"{{width}}"',
        str(params.get("width", 416))
    )
    workflow_str = workflow_str.replace(
        '"{{height}}"',
        str(params.get("height", 672))
    )
    workflow_str = workflow_str.replace(
        '"{{steps}}"',
        str(params.get("steps", 6))
    )
    workflow_str = workflow_str.replace(
        '"{{cfg}}"',
        str(params.get("cfg", 1.0))
    )
    workflow_str = workflow_str.replace(
        '"{{seed}}"',
        str(params.get("seed", -1))
    )

    return json.loads(workflow_str)


def validate_user_input(user_input: Dict[str, Any]) -> None:
    """
    Validate user input structure and required fields.

    Args:
        user_input: User request dict

    Raises:
        ValueError: If validation fails
    """
    # Check for required media
    images = user_input.get("images", {})
    videos = user_input.get("videos", {})

    if not images.get("reference_image"):
        raise ValueError("reference_image is required in images")

    if not videos.get("dance_video"):
        raise ValueError("dance_video is required in videos")

    # Validate numeric parameters
    width = user_input.get("width", 416)
    height = user_input.get("height", 672)
    steps = user_input.get("steps", 6)
    cfg = user_input.get("cfg", 1.0)

    if not isinstance(width, (int, float)) or width <= 0:
        raise ValueError(f"Invalid width: {width}")

    if not isinstance(height, (int, float)) or height <= 0:
        raise ValueError(f"Invalid height: {height}")

    if not isinstance(steps, int) or steps <= 0:
        raise ValueError(f"Invalid steps: {steps}")

    if not isinstance(cfg, (int, float)) or cfg < 0:
        raise ValueError(f"Invalid cfg: {cfg}")


def transform_request_to_workflow(
    user_input: Dict[str, Any],
    workflow_template: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main transformation function: convert user request to ComfyUI workflow.

    Args:
        user_input: User request with media URLs and parameters
        workflow_template: ComfyUI workflow template

    Returns:
        Dict: Complete ComfyUI workflow with injected parameters

    Raises:
        ValueError: If validation fails
        requests.RequestException: If media download fails
    """
    logger.info("Starting request transformation")

    # Validate input
    validate_user_input(user_input)

    # Extract media URLs
    images = user_input.get("images", {})
    videos = user_input.get("videos", {})

    ref_image_url = images.get("reference_image", "")
    dance_video_url = videos.get("dance_video", "")

    # Download media files
    logger.info("Downloading media files")
    try:
        ref_image_filename = download_media_from_url(ref_image_url, "image")
        dance_video_filename = download_media_from_url(dance_video_url, "video")
    except Exception as e:
        logger.error(f"Media download failed: {str(e)}")
        raise

    # Prepare parameters for injection
    params = {
        "reference_image_filename": ref_image_filename,
        "dance_video_filename": dance_video_filename,
        "prompt": user_input.get("prompt", ""),
        "width": user_input.get("width", 416),
        "height": user_input.get("height", 672),
        "steps": user_input.get("steps", 6),
        "cfg": user_input.get("cfg", 1.0),
        "seed": user_input.get("seed", -1)
    }

    logger.info(f"Injecting parameters: {params}")

    # Inject parameters into workflow
    modified_workflow = inject_parameters(workflow_template, params)

    logger.info("Request transformation complete")
    return modified_workflow


def load_workflow_template(template_path: str) -> Dict[str, Any]:
    """
    Load workflow template from file.

    Args:
        template_path: Path to workflow template JSON

    Returns:
        Dict: Workflow template

    Raises:
        FileNotFoundError: If template file doesn't exist
        json.JSONDecodeError: If template is invalid JSON
    """
    with open(template_path, 'r') as f:
        return json.load(f)


if __name__ == "__main__":
    # Example usage
    sample_user_input = {
        "images": {
            "reference_image": "https://example.com/reference.jpg"
        },
        "videos": {
            "dance_video": "https://example.com/dance.mp4"
        },
        "prompt": "a person dancing gracefully",
        "width": 416,
        "height": 672,
        "steps": 6,
        "cfg": 1.0,
        "seed": 42
    }

    # Load template
    template_path = os.path.join(
        os.path.dirname(__file__),
        "workflow_template.json"
    )

    try:
        template = load_workflow_template(template_path)
        result = transform_request_to_workflow(sample_user_input, template)
        print(json.dumps(result, indent=2))
    except Exception as e:
        logger.error(f"Transformation failed: {str(e)}")
