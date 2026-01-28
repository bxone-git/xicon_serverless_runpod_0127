#!/usr/bin/env python3
"""
XiCON Dance SCAIL Handler for RunPod Serverless.

Custom handler that accepts a simplified request format with image/video URLs,
transforms it to ComfyUI workflow format, and returns video outputs from
VHS_VideoCombine nodes.
"""

import runpod
from runpod.serverless.utils import rp_upload
import json
import urllib.request
import urllib.parse
import time
import os
import requests
import base64
import asyncio
import aiohttp
from io import BytesIO
import websocket
import uuid
import tempfile
import socket
import traceback
import logging
from typing import Dict, Any, Optional, Tuple, List

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
COMFY_API_AVAILABLE_INTERVAL_MS = 50
COMFY_API_AVAILABLE_MAX_RETRIES = 500
WEBSOCKET_RECONNECT_ATTEMPTS = int(os.environ.get("WEBSOCKET_RECONNECT_ATTEMPTS", 5))
WEBSOCKET_RECONNECT_DELAY_S = int(os.environ.get("WEBSOCKET_RECONNECT_DELAY_S", 3))

if os.environ.get("WEBSOCKET_TRACE", "false").lower() == "true":
    websocket.enableTrace(True)

COMFY_HOST = "127.0.0.1:8188"
REFRESH_WORKER = os.environ.get("REFRESH_WORKER", "false").lower() == "true"

# Workflow template path - mounted inside container
WORKFLOW_TEMPLATE_PATH = os.environ.get(
    "WORKFLOW_TEMPLATE_PATH",
    "/workflow_template.json"
)

# ComfyUI input directories
COMFY_INPUT_DIR = "/comfyui/input"

# ---------------------------------------------------------------------------
# Input Validation
# ---------------------------------------------------------------------------

def validate_input(job_input: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Validates the XiCON custom input format.

    Expected format:
    {
        "images": {"reference_image": "https://..."},
        "videos": {"dance_video": "https://..." | ""},
        "prompt": "string",
        "negative_prompt": "string (optional)",
        "width": 512,
        "height": 896,
        "steps": 6,
        "cfg": 1,
        "seed": 123456
    }

    Args:
        job_input: The input data to validate.

    Returns:
        tuple: (validated_data, error_message) - error_message is None on success
    """
    if job_input is None:
        return None, "Please provide input"

    # Parse JSON string if needed
    if isinstance(job_input, str):
        try:
            job_input = json.loads(job_input)
        except json.JSONDecodeError:
            return None, "Invalid JSON format in input"

    # Required: images with reference_image
    images = job_input.get("images")
    if not images:
        return None, "Missing 'images' parameter"

    reference_image = images.get("reference_image")
    if not reference_image:
        return None, "Missing 'reference_image' in images"

    # Required: videos (dance_video can be empty string for image-only mode)
    videos = job_input.get("videos")
    if videos is None:
        return None, "Missing 'videos' parameter"

    dance_video = videos.get("dance_video", "")

    # Required: prompt
    prompt = job_input.get("prompt")
    if not prompt:
        return None, "Missing 'prompt' parameter"

    # Optional parameters with defaults
    negative_prompt = job_input.get("negative_prompt", "")
    width = job_input.get("width", 512)
    height = job_input.get("height", 896)
    steps = job_input.get("steps", 6)
    cfg = job_input.get("cfg", 1.0)
    seed = job_input.get("seed", -1)

    # Validate numeric types
    try:
        width = int(width)
        height = int(height)
        steps = int(steps)
        cfg = float(cfg)
        seed = int(seed) if seed != -1 else int(time.time() * 1000) % (2**31)
    except (ValueError, TypeError) as e:
        return None, f"Invalid numeric parameter: {e}"

    # Validate dimensions (must be divisible by 32 for the workflow)
    if width % 32 != 0:
        width = (width // 32) * 32
        print(f"worker-xicon - Adjusted width to {width} (divisible by 32)")
    if height % 32 != 0:
        height = (height // 32) * 32
        print(f"worker-xicon - Adjusted height to {height} (divisible by 32)")

    return {
        "reference_image_url": reference_image,
        "dance_video_url": dance_video,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "width": width,
        "height": height,
        "steps": steps,
        "cfg": cfg,
        "seed": seed,
    }, None


# ---------------------------------------------------------------------------
# URL Download Functions
# ---------------------------------------------------------------------------

async def download_file_async(session: aiohttp.ClientSession, url: str,
                               target_path: str, file_type: str) -> Tuple[bool, str]:
    """
    Download a file from URL asynchronously.

    Args:
        session: aiohttp ClientSession
        url: Source URL
        target_path: Local path to save file
        file_type: Type description for logging

    Returns:
        tuple: (success, error_message)
    """
    try:
        print(f"worker-xicon - Downloading {file_type} from {url}")
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=300)) as response:
            if response.status != 200:
                return False, f"HTTP {response.status} downloading {file_type}"

            content = await response.read()

            # Ensure parent directory exists
            os.makedirs(os.path.dirname(target_path), exist_ok=True)

            with open(target_path, 'wb') as f:
                f.write(content)

            print(f"worker-xicon - Downloaded {file_type}: {len(content)} bytes -> {target_path}")
            return True, ""
    except asyncio.TimeoutError:
        return False, f"Timeout downloading {file_type} from {url}"
    except Exception as e:
        return False, f"Error downloading {file_type}: {e}"


async def download_inputs_async(validated_data: Dict[str, Any], job_id: str) -> Tuple[Dict[str, str], Optional[str]]:
    """
    Download all input images and videos asynchronously.

    Args:
        validated_data: Validated input data containing URLs
        job_id: Job ID for unique naming

    Returns:
        tuple: (filenames_dict, error_message)
    """
    filenames = {}
    download_tasks = []

    async with aiohttp.ClientSession() as session:
        # Reference image (required)
        ref_url = validated_data["reference_image_url"]
        ref_ext = os.path.splitext(urllib.parse.urlparse(ref_url).path)[1] or ".png"
        ref_filename = f"ref_{job_id}{ref_ext}"
        ref_path = os.path.join(COMFY_INPUT_DIR, ref_filename)
        download_tasks.append(
            download_file_async(session, ref_url, ref_path, "reference_image")
        )
        filenames["reference_image"] = ref_filename

        # Dance video (optional)
        video_url = validated_data.get("dance_video_url", "")
        if video_url:
            video_ext = os.path.splitext(urllib.parse.urlparse(video_url).path)[1] or ".mp4"
            video_filename = f"dance_{job_id}{video_ext}"
            video_path = os.path.join(COMFY_INPUT_DIR, video_filename)
            download_tasks.append(
                download_file_async(session, video_url, video_path, "dance_video")
            )
            filenames["dance_video"] = video_filename
        else:
            filenames["dance_video"] = ""

        # Execute all downloads in parallel
        results = await asyncio.gather(*download_tasks, return_exceptions=True)

        # Check for errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                return {}, f"Download failed: {result}"
            success, error = result
            if not success:
                return {}, error

    return filenames, None


def download_inputs(validated_data: Dict[str, Any], job_id: str) -> Tuple[Dict[str, str], Optional[str]]:
    """
    Synchronous wrapper for async download function.
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(download_inputs_async(validated_data, job_id))
        finally:
            loop.close()
    except Exception as e:
        return {}, f"Failed to download inputs: {e}"


# ---------------------------------------------------------------------------
# Workflow Template Processing
# ---------------------------------------------------------------------------

def load_workflow_template() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Load the workflow template from disk.

    Returns:
        tuple: (workflow_dict, error_message)
    """
    try:
        with open(WORKFLOW_TEMPLATE_PATH, 'r') as f:
            workflow = json.load(f)
        print(f"worker-xicon - Loaded workflow template from {WORKFLOW_TEMPLATE_PATH}")
        return workflow, None
    except FileNotFoundError:
        return None, f"Workflow template not found at {WORKFLOW_TEMPLATE_PATH}"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON in workflow template: {e}"
    except Exception as e:
        return None, f"Failed to load workflow template: {e}"


def transform_request_to_workflow(validated_data: Dict[str, Any],
                                   filenames: Dict[str, str],
                                   workflow: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform the request parameters into the workflow by replacing placeholders.

    Placeholders in workflow:
    - {{reference_image_filename}}
    - {{dance_video_filename}}
    - {{prompt}}
    - {{width}}, {{height}}
    - {{steps}}, {{cfg}}, {{seed}}

    Args:
        validated_data: Validated input parameters
        filenames: Downloaded file names
        workflow: Workflow template dict

    Returns:
        Modified workflow dict with placeholders replaced
    """
    # Convert workflow to string for placeholder replacement
    workflow_str = json.dumps(workflow)

    # Replace placeholders
    replacements = {
        "{{reference_image_filename}}": filenames.get("reference_image", ""),
        "{{dance_video_filename}}": filenames.get("dance_video", ""),
        "{{prompt}}": validated_data["prompt"],
        "{{width}}": str(validated_data["width"]),
        "{{height}}": str(validated_data["height"]),
        "{{steps}}": str(validated_data["steps"]),
        "{{cfg}}": str(validated_data["cfg"]),
        "{{seed}}": str(validated_data["seed"]),
    }

    for placeholder, value in replacements.items():
        # Escape special JSON characters in values
        if placeholder in ["{{prompt}}"]:
            # For text fields, escape quotes and backslashes
            value = value.replace("\\", "\\\\").replace('"', '\\"')
        workflow_str = workflow_str.replace(placeholder, value)

    # Parse back to dict
    return json.loads(workflow_str)


# ---------------------------------------------------------------------------
# ComfyUI Communication Functions
# ---------------------------------------------------------------------------

def check_server(url: str, retries: int = 500, delay: int = 50) -> bool:
    """
    Check if ComfyUI server is reachable.
    """
    print(f"worker-xicon - Checking API server at {url}...")
    for i in range(retries):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"worker-xicon - API is reachable")
                return True
        except (requests.Timeout, requests.RequestException):
            pass
        time.sleep(delay / 1000)

    print(f"worker-xicon - Failed to connect to server at {url} after {retries} attempts.")
    return False


def _comfy_server_status() -> Dict[str, Any]:
    """Return reachability info for the ComfyUI HTTP server."""
    try:
        resp = requests.get(f"http://{COMFY_HOST}/", timeout=5)
        return {"reachable": resp.status_code == 200, "status_code": resp.status_code}
    except Exception as exc:
        return {"reachable": False, "error": str(exc)}


def queue_workflow(workflow: Dict[str, Any], client_id: str) -> Dict[str, Any]:
    """
    Queue a workflow to ComfyUI for processing.
    """
    payload = {"prompt": workflow, "client_id": client_id}
    data = json.dumps(payload).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    response = requests.post(
        f"http://{COMFY_HOST}/prompt", data=data, headers=headers, timeout=30
    )

    if response.status_code == 400:
        print(f"worker-xicon - ComfyUI returned 400. Response body: {response.text}")
        try:
            error_data = response.json()
            error_message = "Workflow validation failed"

            if "error" in error_data:
                error_info = error_data["error"]
                if isinstance(error_info, dict):
                    error_message = error_info.get("message", error_message)
                else:
                    error_message = str(error_info)

            if "node_errors" in error_data:
                error_details = []
                for node_id, node_error in error_data["node_errors"].items():
                    if isinstance(node_error, dict):
                        for error_type, error_msg in node_error.items():
                            error_details.append(f"Node {node_id} ({error_type}): {error_msg}")
                    else:
                        error_details.append(f"Node {node_id}: {node_error}")
                if error_details:
                    error_message += ":\n" + "\n".join(f"• {d}" for d in error_details)

            raise ValueError(error_message)
        except (json.JSONDecodeError, KeyError):
            raise ValueError(f"ComfyUI validation failed: {response.text}")

    response.raise_for_status()
    return response.json()


def get_history(prompt_id: str) -> Dict[str, Any]:
    """Retrieve the history of a prompt."""
    response = requests.get(f"http://{COMFY_HOST}/history/{prompt_id}", timeout=30)
    response.raise_for_status()
    return response.json()


def get_file_data(filename: str, subfolder: str, file_type: str) -> Optional[bytes]:
    """
    Fetch file bytes from the ComfyUI /view endpoint.
    Works for both images and videos.
    """
    print(f"worker-xicon - Fetching file data: type={file_type}, subfolder={subfolder}, filename={filename}")
    data = {"filename": filename, "subfolder": subfolder, "type": file_type}
    url_values = urllib.parse.urlencode(data)
    try:
        response = requests.get(f"http://{COMFY_HOST}/view?{url_values}", timeout=120)
        response.raise_for_status()
        print(f"worker-xicon - Successfully fetched file data for {filename}")
        return response.content
    except requests.Timeout:
        print(f"worker-xicon - Timeout fetching file data for {filename}")
        return None
    except requests.RequestException as e:
        print(f"worker-xicon - Error fetching file data for {filename}: {e}")
        return None


def _attempt_websocket_reconnect(ws_url: str, max_attempts: int,
                                  delay_s: int, initial_error: Exception) -> websocket.WebSocket:
    """
    Attempt to reconnect to WebSocket after disconnect.
    """
    print(f"worker-xicon - Websocket connection closed unexpectedly: {initial_error}. Attempting to reconnect...")
    last_error = initial_error

    for attempt in range(max_attempts):
        srv_status = _comfy_server_status()
        if not srv_status["reachable"]:
            print(f"worker-xicon - ComfyUI HTTP unreachable – aborting websocket reconnect")
            raise websocket.WebSocketConnectionClosedException(
                "ComfyUI HTTP unreachable during websocket reconnect"
            )

        print(f"worker-xicon - Reconnect attempt {attempt + 1}/{max_attempts}...")
        try:
            new_ws = websocket.WebSocket()
            new_ws.connect(ws_url, timeout=10)
            print(f"worker-xicon - Websocket reconnected successfully.")
            return new_ws
        except (websocket.WebSocketException, ConnectionRefusedError,
                socket.timeout, OSError) as e:
            last_error = e
            print(f"worker-xicon - Reconnect attempt {attempt + 1} failed: {e}")
            if attempt < max_attempts - 1:
                print(f"worker-xicon - Waiting {delay_s} seconds before next attempt...")
                time.sleep(delay_s)

    raise websocket.WebSocketConnectionClosedException(
        f"Connection closed and failed to reconnect. Last error: {last_error}"
    )


# ---------------------------------------------------------------------------
# Output Processing (Images AND Videos)
# ---------------------------------------------------------------------------

def process_image_output(image_info: Dict[str, Any], job_id: str) -> Optional[Dict[str, Any]]:
    """
    Process an image output from ComfyUI history.
    """
    filename = image_info.get("filename")
    subfolder = image_info.get("subfolder", "")
    img_type = image_info.get("type", "output")

    if img_type == "temp":
        print(f"worker-xicon - Skipping temp image: {filename}")
        return None

    if not filename:
        print(f"worker-xicon - Skipping image with missing filename")
        return None

    image_bytes = get_file_data(filename, subfolder, img_type)
    if not image_bytes:
        print(f"worker-xicon - Failed to fetch image data for {filename}")
        return None

    file_extension = os.path.splitext(filename)[1] or ".png"

    if os.environ.get("BUCKET_ENDPOINT_URL"):
        try:
            with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
                temp_file.write(image_bytes)
                temp_file_path = temp_file.name

            print(f"worker-xicon - Uploading {filename} to S3...")
            s3_url = rp_upload.upload_image(job_id, temp_file_path)
            os.remove(temp_file_path)
            print(f"worker-xicon - Uploaded {filename} to S3: {s3_url}")

            return {"filename": filename, "type": "s3_url", "data": s3_url}
        except Exception as e:
            print(f"worker-xicon - Error uploading {filename} to S3: {e}")
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError:
                    pass
            return None
    else:
        try:
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            return {"filename": filename, "type": "base64", "data": base64_image}
        except Exception as e:
            print(f"worker-xicon - Error encoding {filename} to base64: {e}")
            return None


def process_video_output(video_info: Dict[str, Any], job_id: str) -> Optional[Dict[str, Any]]:
    """
    Process a video output from ComfyUI history (from VHS_VideoCombine 'gifs' key).

    Args:
        video_info: Video info dict from ComfyUI history output
        job_id: Job ID for S3 upload naming

    Returns:
        dict with filename, type, data, and format, or None on error
    """
    filename = video_info.get("filename")
    subfolder = video_info.get("subfolder", "")
    video_type = video_info.get("type", "output")
    video_format = video_info.get("format", "video/h264-mp4")

    if video_type == "temp":
        print(f"worker-xicon - Skipping temp video: {filename}")
        return None

    if not filename:
        print(f"worker-xicon - Skipping video with missing filename")
        return None

    print(f"worker-xicon - Processing video: {filename}, format: {video_format}")

    video_bytes = get_file_data(filename, subfolder, video_type)
    if not video_bytes:
        print(f"worker-xicon - Failed to fetch video data for {filename}")
        return None

    # Determine file extension from format
    format_to_ext = {
        "video/h264-mp4": ".mp4",
        "video/webm": ".webm",
        "image/gif": ".gif",
    }
    file_ext = format_to_ext.get(video_format, ".mp4")

    # Fallback: use extension from filename
    if not file_ext:
        file_ext = os.path.splitext(filename)[1] or ".mp4"

    if os.environ.get("BUCKET_ENDPOINT_URL"):
        try:
            with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
                temp_file.write(video_bytes)
                temp_file_path = temp_file.name

            print(f"worker-xicon - Uploading video {filename} to S3...")
            # Use upload_file for videos (more generic than upload_image)
            s3_url = rp_upload.upload_file(job_id, temp_file_path)
            os.remove(temp_file_path)
            print(f"worker-xicon - Uploaded video {filename} to S3: {s3_url}")

            return {
                "filename": filename,
                "type": "s3_url",
                "data": s3_url,
                "format": video_format
            }
        except Exception as e:
            print(f"worker-xicon - Error uploading video {filename} to S3: {e}")
            if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError:
                    pass
            return None
    else:
        try:
            base64_video = base64.b64encode(video_bytes).decode("utf-8")
            print(f"worker-xicon - Encoded video {filename} as base64")
            return {
                "filename": filename,
                "type": "base64",
                "data": base64_video,
                "format": video_format
            }
        except Exception as e:
            print(f"worker-xicon - Error encoding video {filename} to base64: {e}")
            return None


def process_outputs(outputs: Dict[str, Any], job_id: str) -> Tuple[List[Dict], List[Dict], List[str]]:
    """
    Process all outputs from ComfyUI history, handling both images and videos.

    VHS_VideoCombine nodes output videos under the 'gifs' key (historical naming).

    Args:
        outputs: The outputs dict from ComfyUI history
        job_id: Job ID for upload naming

    Returns:
        tuple: (images_list, videos_list, errors_list)
    """
    images = []
    videos = []
    errors = []

    print(f"worker-xicon - Processing {len(outputs)} output nodes...")

    for node_id, node_output in outputs.items():
        # Handle standard image outputs
        if "images" in node_output:
            print(f"worker-xicon - Node {node_id} contains {len(node_output['images'])} image(s)")
            for image_info in node_output["images"]:
                result = process_image_output(image_info, job_id)
                if result:
                    images.append(result)
                elif image_info.get("type") != "temp":
                    errors.append(f"Failed to process image from node {node_id}")

        # Handle video outputs from VHS_VideoCombine (uses 'gifs' key!)
        if "gifs" in node_output:
            print(f"worker-xicon - Node {node_id} contains {len(node_output['gifs'])} video(s)")
            for video_info in node_output["gifs"]:
                result = process_video_output(video_info, job_id)
                if result:
                    videos.append(result)
                elif video_info.get("type") != "temp":
                    errors.append(f"Failed to process video from node {node_id}")

        # Log any unhandled output types
        other_keys = [k for k in node_output.keys() if k not in ("images", "gifs")]
        if other_keys:
            print(f"worker-xicon - Node {node_id} has unhandled output keys: {other_keys}")

    return images, videos, errors


# ---------------------------------------------------------------------------
# Cleanup Function
# ---------------------------------------------------------------------------

def cleanup_input_files(filenames: Dict[str, str]):
    """
    Remove downloaded input files after processing.
    """
    for file_type, filename in filenames.items():
        if filename:
            filepath = os.path.join(COMFY_INPUT_DIR, filename)
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"worker-xicon - Cleaned up {file_type}: {filepath}")
            except OSError as e:
                print(f"worker-xicon - Failed to cleanup {filepath}: {e}")


# ---------------------------------------------------------------------------
# Main Handler
# ---------------------------------------------------------------------------

def handler(job: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main handler for XiCON Dance SCAIL RunPod serverless function.

    Accepts custom request format, downloads media, transforms to workflow,
    executes in ComfyUI, and returns video outputs.

    Args:
        job: RunPod job dict with 'id' and 'input'

    Returns:
        dict containing 'status', 'images', 'videos', or 'error'
    """
    job_input = job.get("input", {})
    job_id = job.get("id", str(uuid.uuid4()))

    print(f"worker-xicon - Processing job {job_id}")

    # Validate input
    validated_data, error_message = validate_input(job_input)
    if error_message:
        return {"error": error_message}

    print(f"worker-xicon - Input validated: {validated_data['width']}x{validated_data['height']}, "
          f"steps={validated_data['steps']}, cfg={validated_data['cfg']}")

    # Check ComfyUI server
    if not check_server(f"http://{COMFY_HOST}/",
                        COMFY_API_AVAILABLE_MAX_RETRIES,
                        COMFY_API_AVAILABLE_INTERVAL_MS):
        return {"error": f"ComfyUI server ({COMFY_HOST}) not reachable"}

    # Download input files
    filenames, error_message = download_inputs(validated_data, job_id)
    if error_message:
        return {"error": error_message}

    print(f"worker-xicon - Downloaded files: {filenames}")

    # Load workflow template
    workflow, error_message = load_workflow_template()
    if error_message:
        cleanup_input_files(filenames)
        return {"error": error_message}

    # Transform workflow with parameters
    try:
        workflow = transform_request_to_workflow(validated_data, filenames, workflow)
    except Exception as e:
        cleanup_input_files(filenames)
        return {"error": f"Failed to transform workflow: {e}"}

    # Execute workflow via WebSocket
    ws = None
    client_id = str(uuid.uuid4())
    prompt_id = None
    output_images = []
    output_videos = []
    errors = []

    try:
        # Connect WebSocket
        ws_url = f"ws://{COMFY_HOST}/ws?clientId={client_id}"
        print(f"worker-xicon - Connecting to websocket: {ws_url}")
        ws = websocket.WebSocket()
        ws.connect(ws_url, timeout=10)
        print(f"worker-xicon - Websocket connected")

        # Queue workflow
        try:
            queued_workflow = queue_workflow(workflow, client_id)
            prompt_id = queued_workflow.get("prompt_id")
            if not prompt_id:
                raise ValueError(f"Missing 'prompt_id' in queue response")
            print(f"worker-xicon - Queued workflow with ID: {prompt_id}")
        except requests.RequestException as e:
            raise ValueError(f"Error queuing workflow: {e}")

        # Wait for execution
        print(f"worker-xicon - Waiting for workflow execution ({prompt_id})...")
        execution_done = False

        while True:
            try:
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    msg_type = message.get("type")

                    if msg_type == "status":
                        status_data = message.get("data", {}).get("status", {})
                        queue_remaining = status_data.get("exec_info", {}).get("queue_remaining", "N/A")
                        print(f"worker-xicon - Status: {queue_remaining} items in queue")

                    elif msg_type == "executing":
                        data = message.get("data", {})
                        if data.get("node") is None and data.get("prompt_id") == prompt_id:
                            print(f"worker-xicon - Execution finished for prompt {prompt_id}")
                            execution_done = True
                            break

                    elif msg_type == "execution_error":
                        data = message.get("data", {})
                        if data.get("prompt_id") == prompt_id:
                            error_details = (
                                f"Node Type: {data.get('node_type')}, "
                                f"Node ID: {data.get('node_id')}, "
                                f"Message: {data.get('exception_message')}"
                            )
                            print(f"worker-xicon - Execution error: {error_details}")
                            errors.append(f"Workflow execution error: {error_details}")
                            break

                    elif msg_type == "progress":
                        data = message.get("data", {})
                        value = data.get("value", 0)
                        max_val = data.get("max", 0)
                        if max_val > 0:
                            print(f"worker-xicon - Progress: {value}/{max_val} ({100*value//max_val}%)")

            except websocket.WebSocketTimeoutException:
                print(f"worker-xicon - Websocket receive timed out, still waiting...")
                continue
            except websocket.WebSocketConnectionClosedException as closed_err:
                try:
                    ws = _attempt_websocket_reconnect(
                        ws_url, WEBSOCKET_RECONNECT_ATTEMPTS,
                        WEBSOCKET_RECONNECT_DELAY_S, closed_err
                    )
                    continue
                except websocket.WebSocketConnectionClosedException as e:
                    raise e
            except json.JSONDecodeError:
                print(f"worker-xicon - Received invalid JSON via websocket")

        if not execution_done and not errors:
            raise ValueError("Workflow loop exited without completion or error")

        # Fetch history and process outputs
        print(f"worker-xicon - Fetching history for prompt {prompt_id}...")
        history = get_history(prompt_id)

        if prompt_id not in history:
            error_msg = f"Prompt ID {prompt_id} not found in history"
            print(f"worker-xicon - {error_msg}")
            if errors:
                errors.append(error_msg)
                return {"error": "Job processing failed", "details": errors}
            return {"error": error_msg}

        prompt_history = history.get(prompt_id, {})
        outputs = prompt_history.get("outputs", {})

        if not outputs:
            print(f"worker-xicon - No outputs found in history")
            errors.append("No outputs found in history")

        # Process all outputs (images AND videos)
        output_images, output_videos, process_errors = process_outputs(outputs, job_id)
        errors.extend(process_errors)

    except websocket.WebSocketException as e:
        print(f"worker-xicon - WebSocket Error: {e}")
        print(traceback.format_exc())
        cleanup_input_files(filenames)
        return {"error": f"WebSocket communication error: {e}"}
    except requests.RequestException as e:
        print(f"worker-xicon - HTTP Request Error: {e}")
        print(traceback.format_exc())
        cleanup_input_files(filenames)
        return {"error": f"HTTP communication error: {e}"}
    except ValueError as e:
        print(f"worker-xicon - Value Error: {e}")
        print(traceback.format_exc())
        cleanup_input_files(filenames)
        return {"error": str(e)}
    except Exception as e:
        print(f"worker-xicon - Unexpected Error: {e}")
        print(traceback.format_exc())
        cleanup_input_files(filenames)
        return {"error": f"Unexpected error: {e}"}
    finally:
        if ws and ws.connected:
            print(f"worker-xicon - Closing websocket connection")
            ws.close()
        cleanup_input_files(filenames)

    # Build response
    result = {"status": "success"}

    if output_images:
        result["images"] = output_images

    if output_videos:
        result["videos"] = output_videos

    if errors:
        result["errors"] = errors
        print(f"worker-xicon - Job completed with {len(errors)} error(s)")

    if not output_images and not output_videos:
        if errors:
            return {"error": "Job processing failed", "details": errors}
        result["status"] = "success_no_output"
        print(f"worker-xicon - Job completed but produced no output")

    print(f"worker-xicon - Job completed: {len(output_images)} image(s), {len(output_videos)} video(s)")
    return result


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("worker-xicon - Starting XiCON Dance SCAIL handler...")
    runpod.serverless.start({"handler": handler})
