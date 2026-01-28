# XiCON Dance SCAIL Integration Testing Guide

This document provides comprehensive testing procedures for the XiCON Dance SCAIL RunPod serverless endpoint. It covers GPU validation, request handling, video output detection, error handling, and deployment verification.

## Table of Contents

1. [Test Environment Setup](#test-environment-setup)
2. [Pre-Deployment Tests](#pre-deployment-tests)
3. [Integration Tests](#integration-tests)
4. [Performance Testing](#performance-testing)
5. [Troubleshooting](#troubleshooting)
6. [Test Results Reporting](#test-results-reporting)

---

## Test Environment Setup

### Local Testing Prerequisites

1. **Docker and Docker Compose**
   ```bash
   docker --version
   docker-compose --version
   ```

2. **NVIDIA GPU Support**
   ```bash
   nvidia-smi
   ```
   Expected output: NVIDIA driver version and GPU info

3. **Python 3.10+**
   ```bash
   python3 --version
   ```

4. **Required Python Packages** (for test client)
   ```bash
   pip install requests aiohttp python-dotenv
   ```

### Environment Configuration

Create a `.env.test` file for test configuration:

```bash
# RunPod Endpoint
RUNPOD_API_KEY=your_api_key_here
ENDPOINT_ID=your_endpoint_id
COMFY_HOST=127.0.0.1:8188

# Test Images/Videos
TEST_IMAGE_URL=https://example.com/test_image.jpg
TEST_VIDEO_URL=https://example.com/test_video.mp4

# S3 Configuration (if using cloud storage)
BUCKET_ENDPOINT_URL=https://your-s3-endpoint.com
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### Local Development Start

```bash
# Navigate to project directory
cd XiCON/XiCON_Dance_SCAIL

# Build Docker image
docker-compose build

# Start container
docker-compose up
```

Wait for logs showing:
```
worker-xicon - API is reachable
worker-xicon - Websocket connected
```

---

## Pre-Deployment Tests

### Test 1: GPU Validation

**Purpose**: Verify CUDA/GPU is properly initialized before running workflows

**Steps**:

1. **Run GPU Validator Script**
   ```bash
   docker exec -it xicon_dance_scail python /gpu_validator.py
   ```

2. **Check Output**
   ```
   ============================================================
   XiCON Dance SCAIL - GPU/CUDA Validation
   ============================================================

   Status: ✓ SUCCESS
   Message: CUDA validation passed

   Detailed Information:
   --
     nvidia_smi: available
     torch_cuda_available: True
     device_count: 1
     device_names: ['NVIDIA A40']
     vram_total_gb: 48.0
     vram_free_gb: 47.8
     vram_used_gb: 0.2
     cuda_version: 12.1
     cudnn_version: 8800
     cudnn_enabled: True
   ============================================================
   ```

3. **Expected Results**:
   - Status shows SUCCESS
   - `torch_cuda_available: True`
   - `device_count > 0`
   - `vram_free_gb` sufficient (minimum 2GB recommended)
   - CUDA version detected

**Failure Handling**:
- If nvidia-smi not found: NVIDIA driver not installed
- If torch_cuda_available is False: PyTorch CUDA bindings issue
- If device_count is 0: No GPU detected

---

### Test 2: ComfyUI Server Startup

**Purpose**: Verify ComfyUI is running and accessible

**Steps**:

1. **Check Server Health**
   ```bash
   curl http://localhost:8188/
   ```

2. **Expected Response**:
   ```html
   <!DOCTYPE html>
   <html>
     <head>
       <title>ComfyUI</title>
   ```

3. **Check API Endpoints**
   ```bash
   curl http://localhost:8188/api/
   ```

4. **Expected Response**:
   ```json
   {
     "status": "ok"
   }
   ```

**Failure Handling**:
- If connection refused: ComfyUI not started
- If 500 error: Server initialization error

---

### Test 3: Custom Nodes Validation

**Purpose**: Verify all required custom nodes are loaded

**Steps**:

1. **Check Node Registry**
   ```bash
   curl http://localhost:8188/api/nodes | jq '.[] | select(.title | contains("WanVideo"))' | head -20
   ```

2. **Verify Required Nodes Are Present**:
   - `WanVideoModelLoader`
   - `WanVideoDecode`
   - `WanVideoVAELoader`
   - `VHS_LoadVideo`
   - `VHS_VideoCombine`
   - `CLIPVisionLoader`
   - `PoseDetectionVitPoseToDWPose`

3. **Check Node Count**
   ```bash
   curl http://localhost:8188/api/nodes | jq '. | length'
   ```
   Expected: 300+ nodes

**Failure Handling**:
- Missing nodes: Check custom node installation in Dockerfile
- Node loading errors: Check error logs in container

---

### Test 4: Model Files Validation

**Purpose**: Verify all required models are downloaded and accessible

**Steps**:

1. **Check Model Directory**
   ```bash
   docker exec xicon_dance_scail find /comfyui/models -type f -name "*.safetensors" -o -name "*.pth" -o -name "*.onnx" | sort
   ```

2. **Verify Required Models**:
   - `models/diffusion_models/Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors` (14 GB)
   - `models/clip/clip_vision_h.safetensors` (2.5 GB)
   - `models/text_encoders/umt5-xxl-enc-bf16.safetensors` (11.4 GB)
   - `models/vae/Wan2.1_VAE.pth` (508 MB)
   - `models/loras/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors` (739 MB)
   - `models/detection/vitpose_h_wholebody_model.onnx` (600 MB)
   - `models/detection/yolov10m.onnx` (100 MB)
   - `models/checkpoints/nlf_l_multi_0.3.2.torchscript` (300 MB)

3. **Check Total Disk Space**
   ```bash
   docker exec xicon_dance_scail du -sh /comfyui/models
   ```
   Expected: ~30+ GB

4. **Verify Workflow Template**
   ```bash
   docker exec xicon_dance_scail ls -lh /workflow_template.json
   ```

**Failure Handling**:
- Missing models: Re-run Docker build, may need to increase build timeout
- Corrupted files: Delete and rebuild

---

## Integration Tests

### Test 5: Input Validation

**Purpose**: Verify request validation rejects invalid inputs

**Test Cases**:

#### 5.1: Missing Reference Image
```bash
curl -X POST http://localhost:8188/api/handler \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "images": {},
      "videos": {"dance_video": ""},
      "prompt": "a dog dancing",
      "width": 512,
      "height": 896
    }
  }'
```

**Expected Response**:
```json
{
  "error": "Missing 'reference_image' in images"
}
```

#### 5.2: Missing Prompt
```bash
curl -X POST http://localhost:8188/api/handler \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "images": {"reference_image": "https://example.com/img.jpg"},
      "videos": {"dance_video": ""},
      "prompt": "",
      "width": 512,
      "height": 896
    }
  }'
```

**Expected Response**:
```json
{
  "error": "Missing 'prompt' parameter"
}
```

#### 5.3: Invalid Width (Not Divisible by 32)
```bash
curl -X POST http://localhost:8188/api/handler \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "images": {"reference_image": "https://example.com/img.jpg"},
      "videos": {"dance_video": ""},
      "prompt": "a person dancing",
      "width": 500,
      "height": 896
    }
  }'
```

**Expected Behavior**:
- Width automatically adjusted to 480 (divisible by 32)
- Execution continues
- Logs show: "Adjusted width to 480"

#### 5.4: Invalid JSON Format
```bash
curl -X POST http://localhost:8188/api/handler \
  -H "Content-Type: application/json" \
  -d 'invalid json'
```

**Expected Response**:
```json
{
  "error": "Invalid JSON format in input"
}
```

---

### Test 6: Request with Image URL (Single Frame Mode)

**Purpose**: Verify handler accepts image URL, downloads it, and executes workflow

**Test Request**:

```bash
RUNPOD_API_KEY=test_key
ENDPOINT_ID=test_endpoint

curl -X POST "https://api.runpod.io/v2/${ENDPOINT_ID}/run" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "images": {
        "reference_image": "https://inwtsfxxunljfznahixt.supabase.co/storage/v1/object/public/uploads/e93bb31f-98f8-4909-a9cf-e52bb852cf5a/62b3fda0-be88-43bd-8b3c-18ff988eb5ca/2e49ba3ed9fb48adbb4e3f353fa336f3.jpg"
      },
      "videos": {
        "dance_video": ""
      },
      "prompt": "a dog family is dancing",
      "width": 512,
      "height": 896,
      "steps": 6,
      "cfg": 1,
      "seed": 2109184567761813
    }
  }' | jq .
```

**Steps**:

1. **Monitor Handler Logs**
   ```bash
   docker logs -f xicon_dance_scail | grep "worker-xicon"
   ```

2. **Expected Log Sequence**:
   ```
   worker-xicon - Processing job abc123def
   worker-xicon - Input validated: 512x896, steps=6, cfg=1
   worker-xicon - Checking API server at http://127.0.0.1:8188/
   worker-xicon - API is reachable
   worker-xicon - Downloading reference_image from https://...
   worker-xicon - Downloaded reference_image: 245678 bytes -> ref_abc123def.jpg
   worker-xicon - Downloaded files: {'reference_image': 'ref_abc123def.jpg', 'dance_video': ''}
   worker-xicon - Loaded workflow template from /workflow_template.json
   worker-xicon - Connecting to websocket: ws://127.0.0.1:8188/ws?clientId=xyz
   worker-xicon - Websocket connected
   worker-xicon - Queued workflow with ID: prompt_xyz
   worker-xicon - Waiting for workflow execution (prompt_xyz)...
   worker-xicon - Progress: 1/6 (16%)
   worker-xicon - Progress: 2/6 (33%)
   worker-xicon - Progress: 3/6 (50%)
   worker-xicon - Progress: 4/6 (66%)
   worker-xicon - Progress: 5/6 (83%)
   worker-xicon - Progress: 6/6 (100%)
   worker-xicon - Execution finished for prompt prompt_xyz
   worker-xicon - Fetching history for prompt prompt_xyz...
   worker-xicon - Processing 2 output nodes...
   worker-xicon - Node 139 contains 1 video(s)
   worker-xicon - Processing video: 1323_00001.mp4, format: video/h264-mp4
   worker-xicon - Uploaded video 1323_00001.mp4 to S3: https://s3-url/video.mp4
   worker-xicon - Job completed: 0 image(s), 1 video(s)
   ```

3. **Check Response Status**
   ```bash
   curl -X GET "https://api.runpod.io/v2/${ENDPOINT_ID}/status/${RUN_ID}" \
     -H "Authorization: Bearer ${RUNPOD_API_KEY}" | jq .
   ```

4. **Expected Response Structure**:
   ```json
   {
     "id": "run_abc123def",
     "status": "COMPLETED",
     "output": {
       "status": "success",
       "videos": [
         {
           "filename": "1323_00001.mp4",
           "type": "s3_url",
           "data": "https://your-bucket.s3.amazonaws.com/...",
           "format": "video/h264-mp4"
         }
       ]
     }
   }
   ```

**Validation Checklist**:
- [ ] Image downloaded successfully
- [ ] Workflow queued with valid prompt ID
- [ ] Progress updates received (0-100%)
- [ ] Execution completed without errors
- [ ] Video output generated
- [ ] Video uploaded to S3 (if configured)
- [ ] Response contains video URL

---

### Test 7: Request with Both Image and Video

**Purpose**: Verify handler accepts image + video, runs pose detection, and combines outputs

**Test Request**:

```bash
curl -X POST "https://api.runpod.io/v2/${ENDPOINT_ID}/run" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "images": {
        "reference_image": "https://inwtsfxxunljfznahixt.supabase.co/storage/v1/object/public/uploads/reference.jpg"
      },
      "videos": {
        "dance_video": "https://inwtsfxxunljfznahixt.supabase.co/storage/v1/object/public/uploads/dance.mp4"
      },
      "prompt": "a person dancing gracefully",
      "negative_prompt": "low quality, blurry",
      "width": 512,
      "height": 896,
      "steps": 8,
      "cfg": 1.5,
      "seed": 42
    }
  }' | jq .
```

**Steps**:

1. **Monitor Pose Detection Stage**
   ```bash
   docker logs -f xicon_dance_scail | grep -E "(NLFPredict|Pose|VHS_VideoCombine)"
   ```

2. **Expected Processing**:
   - Video loaded and frames extracted
   - Pose detection runs on video frames
   - Pose embeddings created
   - Reference image pose extracted
   - SCAIL model processes poses
   - Video combined from generated frames

3. **Expected Logs**:
   ```
   worker-xicon - Downloaded files: {'reference_image': 'ref_abc123.jpg', 'dance_video': 'dance_abc123.mp4'}
   worker-xicon - Node 334 (NLFPredict) processing video frames
   worker-xicon - Node 362 (RenderNLFPoses) rendering poses
   worker-xicon - Node 139 (VHS_VideoCombine) combining frames into video
   ```

**Validation Checklist**:
- [ ] Both image and video downloaded
- [ ] Video frames extracted
- [ ] Pose detection executed
- [ ] Reference image pose extracted
- [ ] Final video generated with combined poses
- [ ] Video output returned in response

---

### Test 8: Video Output Detection

**Purpose**: Verify handler correctly detects and returns VHS_VideoCombine outputs

**Steps**:

1. **Capture Response JSON** (from Test 6 or 7)
   ```bash
   RESPONSE=$(curl -X GET "https://api.runpod.io/v2/${ENDPOINT_ID}/status/${RUN_ID}" \
     -H "Authorization: Bearer ${RUNPOD_API_KEY}")
   echo "$RESPONSE" | jq '.output'
   ```

2. **Validate Video Output Structure**:
   ```json
   {
     "status": "success",
     "videos": [
       {
         "filename": "1323_00001.mp4",
         "type": "s3_url",
         "data": "https://your-bucket.s3.amazonaws.com/videos/...",
         "format": "video/h264-mp4"
       }
     ]
   }
   ```

3. **Verify Video URL is Accessible**:
   ```bash
   VIDEO_URL="https://your-bucket.s3.amazonaws.com/videos/..."
   curl -I "$VIDEO_URL" | head -5
   ```
   Expected: HTTP 200 OK

4. **Download and Verify Video File**:
   ```bash
   curl -o test_output.mp4 "$VIDEO_URL"
   ffprobe test_output.mp4 -show_format -show_streams
   ```
   Expected: Valid MP4 with video stream

**Validation Checklist**:
- [ ] Response contains `"videos"` array
- [ ] Video object has `filename`, `type`, `data`, `format` fields
- [ ] `type` is `"s3_url"` or `"base64"`
- [ ] S3 URL is valid and accessible
- [ ] Downloaded file is valid MP4

---

### Test 9: Error Handling - Network Timeout

**Purpose**: Verify graceful handling of image download timeouts

**Simulated Test**:

```bash
curl -X POST "https://api.runpod.io/v2/${ENDPOINT_ID}/run" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "images": {
        "reference_image": "https://httpbin.org/delay/400"
      },
      "videos": {"dance_video": ""},
      "prompt": "test",
      "width": 512,
      "height": 896
    }
  }' | jq .
```

**Expected Response** (after 300 second timeout):
```json
{
  "error": "Timeout downloading reference_image from https://httpbin.org/delay/400"
}
```

**Validation Checklist**:
- [ ] Timeout error returned (not crash)
- [ ] Error message is descriptive
- [ ] Handler cleans up partial files
- [ ] No hanging connections

---

### Test 10: Error Handling - Invalid Image Format

**Purpose**: Verify handling of non-image files

**Test Request**:

```bash
# Create a text file
echo "This is not an image" > fake_image.txt

# Upload to temporary server
# Then reference the URL in request
curl -X POST "https://api.runpod.io/v2/${ENDPOINT_ID}/run" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "images": {
        "reference_image": "https://example.com/fake_image.txt"
      },
      "videos": {"dance_video": ""},
      "prompt": "test",
      "width": 512,
      "height": 896
    }
  }' | jq .
```

**Expected Behavior**:
- File downloads successfully
- Workflow execution fails when trying to load as image
- ComfyUI returns validation error
- Handler captures and returns error

**Expected Response**:
```json
{
  "error": "Job processing failed",
  "details": [
    "Workflow execution error: Node Type: LoadImage, Node ID: 106, Message: Invalid image file"
  ]
}
```

**Validation Checklist**:
- [ ] Error caught and reported
- [ ] Execution doesn't crash
- [ ] Error message is descriptive

---

## Performance Testing

### Test 11: Execution Time Measurement

**Purpose**: Baseline performance metrics for optimization

**Steps**:

1. **Single Request Timing**
   ```bash
   time curl -X POST "https://api.runpod.io/v2/${ENDPOINT_ID}/run" \
     -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{
       "input": {
         "images": {"reference_image": "https://example.com/img.jpg"},
         "videos": {"dance_video": ""},
         "prompt": "test",
         "width": 512,
         "height": 896,
         "steps": 6,
         "cfg": 1,
         "seed": 42
       }
     }' > /dev/null
   ```

2. **Record Metrics**:
   - Queue time (request → job ID)
   - Download time (image + video)
   - Workflow execution time
   - Output processing time
   - Total time

3. **Expected Times** (A40 GPU, 512x896, 6 steps):
   - Download: 10-30 seconds
   - Workflow execution: 60-90 seconds
   - Output processing: 10-20 seconds
   - **Total: 80-140 seconds**

### Test 12: Concurrent Requests

**Purpose**: Verify handler stability under load

**Steps**:

1. **Submit Multiple Requests**
   ```bash
   for i in {1..5}; do
     curl -X POST "https://api.runpod.io/v2/${ENDPOINT_ID}/run" \
       -H "Authorization: Bearer ${RUNPOD_API_KEY}" \
       -H "Content-Type: application/json" \
       -d "{\"input\": {...}}" &
   done
   wait
   ```

2. **Monitor Queue**
   ```bash
   curl -s http://localhost:8188/queue | jq '.queue_pending'
   ```

3. **Expected Behavior**:
   - All requests queued successfully
   - No dropped requests
   - No out-of-memory errors
   - No VRAM allocation failures

4. **Check Handler Logs**:
   ```bash
   docker logs xicon_dance_scail | grep "Processing job" | wc -l
   ```
   Should show all job IDs

---

### Test 13: Resource Usage

**Purpose**: Monitor GPU and memory usage

**Monitoring Commands**:

```bash
# Real-time GPU usage
watch -n 1 'nvidia-smi --query-gpu=index,name,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv,noheader'

# During workflow execution
docker stats xicon_dance_scail --no-stream

# VRAM during execution
docker exec xicon_dance_scail nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader
```

**Expected Metrics** (A40, 48GB VRAM):
- GPU Utilization: 90-100% during sampling
- Memory Used: 40-48 GB
- Memory Free: <1 GB
- No OOM errors

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: CUDA Out of Memory

**Symptoms**:
```
RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB
```

**Solutions**:
1. Reduce generation resolution
2. Reduce number of steps
3. Use smaller model precision (FP8 vs FP16)
4. Enable model offloading in workflow
5. Use GPU with more VRAM

**Check VRAM**:
```bash
docker exec xicon_dance_scail python -c "import torch; print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB')"
```

#### Issue: Custom Node Not Found

**Symptoms**:
```
Node class 'WanVideoModelLoader' not found
```

**Solutions**:
1. Check custom node installation in logs
2. Verify Git clone succeeded
3. Check requirements.txt installation
4. Rebuild Docker image

**Verify Installation**:
```bash
docker exec xicon_dance_scail ls -la /comfyui/custom_nodes/ComfyUI-WanVideoWrapper/
```

#### Issue: Model Download Fails

**Symptoms**:
```
HTTP Error 404 downloading model
```

**Solutions**:
1. Verify HuggingFace URL is correct
2. Check file still exists at source
3. Increase Docker build timeout
4. Manual download and copy

**Check Model Path**:
```bash
docker exec xicon_dance_scail find /comfyui/models -name "*.safetensors" | grep -i wan
```

#### Issue: WebSocket Connection Fails

**Symptoms**:
```
worker-xicon - Websocket connection closed unexpectedly
```

**Solutions**:
1. Check ComfyUI server is running
2. Increase WEBSOCKET_RECONNECT_ATTEMPTS
3. Check firewall allows WebSocket
4. Verify port 8188 is accessible

**Test WebSocket**:
```bash
docker exec xicon_dance_scail python -c "
import websocket
try:
    ws = websocket.WebSocket()
    ws.connect('ws://127.0.0.1:8188/ws?clientId=test')
    print('WebSocket connected')
    ws.close()
except Exception as e:
    print(f'WebSocket failed: {e}')
"
```

#### Issue: Workflow Validation Error

**Symptoms**:
```
ComfyUI returned 400. Response body: {"error": {...}, "node_errors": {...}}
```

**Solutions**:
1. Check workflow template JSON syntax
2. Verify node IDs in template exist
3. Check placeholder replacement worked
4. Verify parameter types match workflow expectations

**Validate Workflow**:
```bash
docker exec xicon_dance_scail python -c "
import json
with open('/workflow_template.json') as f:
    workflow = json.load(f)
    print('Workflow nodes:', len(workflow))
    print('Sample node:', list(workflow.items())[0])
"
```

---

## Test Results Reporting

### Test Execution Template

Use this template to document test runs:

```markdown
## Test Run Report - [DATE]

### Environment
- GPU: [MODEL]
- CUDA Version: [VERSION]
- ComfyUI Version: [VERSION]
- Handler Version: [COMMIT/TAG]

### Pre-Deployment Tests
- [ ] Test 1: GPU Validation - PASS/FAIL
- [ ] Test 2: ComfyUI Startup - PASS/FAIL
- [ ] Test 3: Custom Nodes - PASS/FAIL
- [ ] Test 4: Model Files - PASS/FAIL

### Integration Tests
- [ ] Test 5: Input Validation - PASS/FAIL
- [ ] Test 6: Image URL Request - PASS/FAIL
- [ ] Test 7: Image + Video Request - PASS/FAIL
- [ ] Test 8: Video Output Detection - PASS/FAIL
- [ ] Test 9: Network Error Handling - PASS/FAIL
- [ ] Test 10: Invalid Format Handling - PASS/FAIL

### Performance Tests
- [ ] Test 11: Execution Time - PASS/FAIL
  - Average time: ___ seconds
  - Min: ___ seconds
  - Max: ___ seconds

- [ ] Test 12: Concurrent Requests - PASS/FAIL
  - Requests processed: ___
  - Failed: ___
  - Queued correctly: YES/NO

- [ ] Test 13: Resource Usage - PASS/FAIL
  - Max GPU Usage: ___%
  - Max Memory: ___ GB
  - OOM Errors: YES/NO

### Issues Found
1. [Issue description]
   - Impact: HIGH/MEDIUM/LOW
   - Resolution: [Solution applied]
   - Status: RESOLVED/PENDING

### Sign-Off
- Tested by: [Name]
- Date: [Date]
- Ready for Deployment: YES/NO
```

### CI/CD Integration

For automated testing in GitHub Actions:

```yaml
name: Test XiCON Handler

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Build Docker Image
        run: docker-compose -f XiCON/XiCON_Dance_SCAIL/docker-compose.yml build

      - name: Start Container
        run: docker-compose -f XiCON/XiCON_Dance_SCAIL/docker-compose.yml up -d

      - name: Wait for Server
        run: |
          for i in {1..60}; do
            if curl -s http://localhost:8188 > /dev/null; then
              echo "Server ready"
              exit 0
            fi
            sleep 1
          done
          exit 1

      - name: Test Input Validation
        run: |
          curl -X POST http://localhost:8188/api/handler \
            -H "Content-Type: application/json" \
            -d '{"input": {"images": {}, "prompt": "test"}}' \
            | grep -q "error"

      - name: Cleanup
        if: always()
        run: docker-compose -f XiCON/XiCON_Dance_SCAIL/docker-compose.yml down
```

---

## Verification Checklist for Deployment

Before deploying to RunPod, complete this checklist:

### Pre-Deployment
- [ ] All GPU validation tests pass
- [ ] ComfyUI starts without errors
- [ ] All custom nodes loaded
- [ ] All models downloaded successfully
- [ ] Workflow template is valid JSON

### Code Quality
- [ ] Handler.py has no syntax errors
- [ ] Request validation covers all edge cases
- [ ] Error handling includes all failure paths
- [ ] Logging is comprehensive and informative
- [ ] Code follows project conventions

### Security
- [ ] Input URLs are validated
- [ ] File paths are sanitized
- [ ] No hardcoded credentials
- [ ] Environment variables used for sensitive config
- [ ] Temporary files cleaned up

### Performance
- [ ] Execution time within SLA
- [ ] Memory usage stable
- [ ] No memory leaks over time
- [ ] WebSocket reconnection works
- [ ] S3 upload completes reliably

### Documentation
- [ ] README.md updated with API format
- [ ] TESTING.md complete (this file)
- [ ] Error codes documented
- [ ] Configuration options documented
- [ ] Known limitations listed

---

## Additional Resources

- **ComfyUI WebSocket Protocol**: https://github.com/comfyanonymous/ComfyUI/blob/master/web/scripts/websocket.js
- **VHS VideoCombine Docs**: https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite
- **WanVideo Nodes**: https://github.com/kijai/ComfyUI-WanVideoWrapper
- **RunPod API Docs**: https://docs.runpod.io/serverless/overview

---

**Document Version**: 1.0
**Last Updated**: 2026-01-28
**Status**: Ready for Testing
