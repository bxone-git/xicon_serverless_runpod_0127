# Request Transformer Module

## Overview

The `request_transformer.py` module transforms user's custom request format into ComfyUI workflow format with dynamically injected parameters. It handles:

- **Media Downloads**: Downloads reference images and dance videos from URLs
- **Parameter Mapping**: Maps user parameters to specific ComfyUI workflow nodes
- **Validation**: Validates user input structure and parameter values
- **Workflow Injection**: Injects downloaded filenames and parameters into workflow template

## Architecture

```
User Request (JSON)
       ↓
  Validation
       ↓
Media Download (concurrent)
       ↓
Parameter Mapping
       ↓
Workflow Injection
       ↓
Complete ComfyUI Workflow
```

## Input Format

### User Request Structure

```json
{
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
```

### Required Fields

- `images.reference_image` (string, URL): Reference image for person
- `videos.dance_video` (string, URL): Dance video for motion transfer

### Optional Fields with Defaults

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `prompt` | string | "" | Positive prompt for generation |
| `width` | int | 416 | Output video width |
| `height` | int | 672 | Output video height |
| `steps` | int | 6 | Sampling steps |
| `cfg` | float | 1.0 | CFG scale |
| `seed` | int | -1 | Random seed (-1 = random) |

## Parameter Mapping

Parameters are mapped to specific ComfyUI workflow nodes:

| User Parameter | Workflow Node | Node Field |
|----------------|---------------|------------|
| `reference_image` | 106 | `image` |
| `dance_video` | 130 | `video` |
| `prompt` | 368 | `positive_prompt` |
| `width` | 203 | `value` |
| `height` | 204 | `value` |
| `steps` | 349 | `steps` |
| `cfg` | 238 | `value` |
| `seed` | 348 | `seed` |

## API Reference

### Core Functions

#### `transform_request_to_workflow(user_input, workflow_template)`

Main transformation function.

**Parameters:**
- `user_input` (dict): User request with media URLs and parameters
- `workflow_template` (dict): ComfyUI workflow template with placeholders

**Returns:**
- `dict`: Complete ComfyUI workflow with injected parameters

**Raises:**
- `ValueError`: If validation fails
- `requests.RequestException`: If media download fails

**Example:**
```python
from request_transformer import transform_request_to_workflow, load_workflow_template

# Load template
template = load_workflow_template("workflow_template.json")

# User request
user_input = {
    "images": {"reference_image": "https://example.com/ref.jpg"},
    "videos": {"dance_video": "https://example.com/dance.mp4"},
    "prompt": "dancing person",
    "width": 416,
    "height": 672
}

# Transform
workflow = transform_request_to_workflow(user_input, template)
```

#### `download_media_from_url(url, media_type)`

Downloads media from URL to ComfyUI input directory.

**Parameters:**
- `url` (str): URL of media file
- `media_type` (str): Type of media ("image" or "video")

**Returns:**
- `str`: Filename of saved media

**Raises:**
- `ValueError`: If URL is empty
- `requests.RequestException`: If download fails

**Example:**
```python
filename = download_media_from_url(
    "https://example.com/image.jpg",
    "image"
)
print(f"Downloaded to: {filename}")
```

#### `validate_user_input(user_input)`

Validates user input structure and parameter values.

**Parameters:**
- `user_input` (dict): User request to validate

**Raises:**
- `ValueError`: If validation fails with specific error message

**Example:**
```python
try:
    validate_user_input(user_input)
    print("Validation passed")
except ValueError as e:
    print(f"Validation error: {e}")
```

#### `inject_parameters(workflow, params)`

Replaces `{{placeholders}}` in workflow with actual values.

**Parameters:**
- `workflow` (dict): ComfyUI workflow with placeholders
- `params` (dict): Parameters to inject

**Returns:**
- `dict`: Modified workflow

**Example:**
```python
params = {
    "reference_image_filename": "ref.jpg",
    "dance_video_filename": "dance.mp4",
    "prompt": "dancing",
    "width": 512,
    "height": 768,
    "steps": 10,
    "cfg": 2.0,
    "seed": 42
}

workflow = inject_parameters(template, params)
```

#### `load_workflow_template(template_path)`

Loads workflow template from JSON file.

**Parameters:**
- `template_path` (str): Path to workflow template

**Returns:**
- `dict`: Workflow template

**Raises:**
- `FileNotFoundError`: If template doesn't exist
- `json.JSONDecodeError`: If template is invalid JSON

## Workflow Template Placeholders

The workflow template uses the following placeholders:

```json
{
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
```

## Media Handling

### Download Process

1. Generate unique UUID-based filename
2. Determine file extension (.jpg for images, .mp4 for videos)
3. Create ComfyUI input directory if needed
4. Download with 120-second timeout and streaming
5. Save to `/comfyui/input/{uuid}.{ext}`
6. Return filename for workflow injection

### File Naming Convention

- **Images**: `{uuid}.jpg` (e.g., `a1b2c3d4-1234-5678-90ab-cdef12345678.jpg`)
- **Videos**: `{uuid}.mp4` (e.g., `e5f6g7h8-9012-3456-78ab-cdef90123456.mp4`)

### Error Handling

- **Invalid URL**: Raises `ValueError`
- **Download timeout**: Raises `requests.Timeout`
- **HTTP errors**: Raises `requests.HTTPError`
- **Network issues**: Raises `requests.RequestException`

## Validation Rules

### Required Fields

- `images.reference_image` must be present and non-empty
- `videos.dance_video` must be present and non-empty

### Numeric Constraints

| Parameter | Constraint |
|-----------|------------|
| `width` | Must be > 0 |
| `height` | Must be > 0 |
| `steps` | Must be integer > 0 |
| `cfg` | Must be >= 0 |
| `seed` | Any integer |

## Testing

### Run Unit Tests

```bash
cd XiCON/XiCON_Dance_SCAIL
python3 -m unittest test_request_transformer.py -v
```

### Test Coverage

The test suite includes:

- ✅ String parameter injection
- ✅ Numeric parameter injection
- ✅ Default parameter values
- ✅ Input validation (success cases)
- ✅ Input validation (missing reference_image)
- ✅ Input validation (missing dance_video)
- ✅ Input validation (invalid width)
- ✅ Input validation (invalid steps)
- ✅ Media download success
- ✅ Media download with empty URL
- ✅ Template loading success
- ✅ Template loading with missing file
- ✅ Complete transformation workflow

### Sample Test Output

```
Ran 13 tests in 0.003s

OK
```

## Integration Example

### With RunPod Handler

```python
from request_transformer import transform_request_to_workflow, load_workflow_template
import json

# Load template once at startup
template = load_workflow_template("workflow_template.json")

def handler(job):
    """RunPod handler function"""
    try:
        # Get user input
        user_input = job["input"]

        # Transform to workflow
        workflow = transform_request_to_workflow(user_input, template)

        # Submit to ComfyUI
        result = submit_workflow(workflow)

        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

### With FastAPI

```python
from fastapi import FastAPI, HTTPException
from request_transformer import transform_request_to_workflow, load_workflow_template

app = FastAPI()
template = load_workflow_template("workflow_template.json")

@app.post("/transform")
async def transform(user_input: dict):
    try:
        workflow = transform_request_to_workflow(user_input, template)
        return {"workflow": workflow}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Performance Considerations

### Optimization Strategies

1. **Template Caching**: Load template once at startup
2. **Concurrent Downloads**: Download reference image and dance video in parallel
3. **Streaming Downloads**: Use `iter_content()` for memory efficiency
4. **Timeout Configuration**: 120-second timeout prevents hanging

### Benchmarks (Approximate)

| Operation | Duration |
|-----------|----------|
| Validation | < 1ms |
| Parameter injection | < 5ms |
| Image download (10MB) | 2-5s |
| Video download (100MB) | 10-30s |
| Total transformation | 12-35s (depends on media size) |

## Error Handling Guide

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `ValueError: reference_image is required` | Missing reference image URL | Ensure `images.reference_image` is provided |
| `ValueError: Invalid width` | Width <= 0 | Provide positive integer for width |
| `requests.Timeout` | Download taking too long | Check URL, increase timeout, or use smaller media |
| `requests.HTTPError: 404` | URL not found | Verify URL is accessible |
| `FileNotFoundError` | Template missing | Ensure `workflow_template.json` exists |

### Logging

The module uses Python's `logging` module:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

**Log levels:**
- `INFO`: Successful operations (downloads, transformations)
- `ERROR`: Failed operations with details

## Dependencies

```python
json       # Workflow serialization
os         # File operations
uuid       # Unique filename generation
logging    # Operation logging
pathlib    # Path handling
typing     # Type hints
requests   # HTTP downloads
urllib     # URL parsing
```

Install dependencies:
```bash
pip install requests
```

## Configuration

### Environment Variables

```bash
# Optional: Override ComfyUI input directory
export COMFYUI_INPUT_DIR="/custom/path/to/input"
```

### Constants

Modify in `request_transformer.py`:

```python
# Download timeout (seconds)
DOWNLOAD_TIMEOUT = 120

# Chunk size for streaming downloads (bytes)
CHUNK_SIZE = 8192
```

## Future Enhancements

### Planned Features

- [ ] Async/await support for concurrent downloads
- [ ] Progress callbacks for large downloads
- [ ] Retry logic with exponential backoff
- [ ] Support for base64-encoded media
- [ ] Workflow validation before submission
- [ ] Caching of downloaded media (by hash)
- [ ] Support for additional media types (GIF, WebM)

## License

Part of XiCON serverless RunPod project.

## Support

For issues or questions, refer to the main project documentation.
