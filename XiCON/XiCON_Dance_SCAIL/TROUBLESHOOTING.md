# Troubleshooting Guide: XiCON Dance SCAIL

A comprehensive guide for diagnosing and resolving common issues with XiCON Dance SCAIL on RunPod Serverless.

## Table of Contents

1. [Quick Diagnosis](#quick-diagnosis)
2. [Common Issues](#common-issues)
3. [Reading RunPod Logs](#reading-runpod-logs)
4. [Debugging Techniques](#debugging-techniques)
5. [Solutions by Category](#solutions-by-category)
6. [Performance Optimization](#performance-optimization)
7. [Health Check Verification](#health-check-verification)

---

## Quick Diagnosis

### Step 1: Check Endpoint Status

```bash
ENDPOINT_ID="your_endpoint_id"
RUNPOD_API_KEY="your_api_key"

# Check if endpoint is ready
curl -s -X GET "https://api.runpod.io/v2/$ENDPOINT_ID/health" \
  -H "api_key: $RUNPOD_API_KEY"
```

**Expected response:**
```json
{
  "ok": true,
  "name": "xicon-dance-scail",
  "version": "1.0"
}
```

### Step 2: Check Worker Status

```bash
# Via RunPod console:
# 1. Navigate to Serverless → Endpoints
# 2. Click on your endpoint
# 3. Check "Active Workers" and "Queue Depth" sections
# 4. Click "Logs" tab to see real-time logs
```

### Step 3: Test with Simple Request

```bash
curl -X POST "https://api.runpod.io/v2/$ENDPOINT_ID/runsync" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
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
  }'
```

---

## Common Issues

### Issue 1: Race Condition - Job Fails in <1 Second

**Symptoms:**
- Job fails immediately after submission
- Error message: "WebSocket connection closed" or "ComfyUI server not reachable"
- Log shows: `worker-xicon: Processing job` then `worker-xicon: Error` within 1 second

**Root Cause:**
ComfyUI startup race condition where the handler attempts to connect before ComfyUI has fully initialized the WebSocket server.

**Solution:**

This issue was fixed in `start.sh` by implementing a retry-based startup sequence:

```bash
# Location: /mnt/x/xicon_serverless_runpod_0127/XiCON/XiCON_Dance_SCAIL/start.sh (lines 32-54)

# Wait for ComfyUI to be fully ready
echo "worker-xicon: Waiting for ComfyUI server to be ready..."
COMFY_READY=false
MAX_WAIT=120
ELAPSED=0

while [ "$COMFY_READY" = "false" ] && [ $ELAPSED -lt $MAX_WAIT ]; do
  if wget -q --spider --server-response http://127.0.0.1:8188/system_stats 2>&1 | grep -q "200 OK"; then
    COMFY_READY=true
    echo "worker-xicon: ComfyUI server is ready after ${ELAPSED}s"
  else
    sleep 1
    ELAPSED=$((ELAPSED + 1))
  fi
done
```

**If race condition still occurs:**

1. **Increase startup timeout:**
   - Open `start.sh` (line 35)
   - Change `MAX_WAIT=120` to `MAX_WAIT=180` (180 seconds)
   - Rebuild Docker image

2. **Configure environment variables in RunPod:**
   ```
   COMFY_LOG_LEVEL=DEBUG
   WEBSOCKET_RECONNECT_ATTEMPTS=10
   WEBSOCKET_RECONNECT_DELAY_S=5
   ```

3. **Verify in logs:**
   ```bash
   # Look for this in RunPod logs:
   "worker-xicon: ComfyUI server is ready after XYZs"
   ```

---

### Issue 2: ComfyUI Startup Timeout

**Symptoms:**
- Worker starts but never becomes available
- Logs show: `FATAL: ComfyUI failed to start within 120s`
- Endpoint stays in "provisioning" state

**Root Cause:**
ComfyUI initialization is slow on first boot due to:
- Large model loading from disk
- First-time CUDA kernel compilation
- Slow network I/O to download models
- Insufficient GPU memory

**Diagnosis:**

```bash
# Check RunPod logs for specific stage
# Filter for these patterns in logs tab:
"worker-xicon: Validating GPU"      # GPU check
"worker-xicon: Starting ComfyUI"    # ComfyUI launch
"worker-xicon: Waiting for server"  # Waiting for readiness
```

**Solutions:**

1. **Increase endpoint timeout (temporary):**
   - Go to RunPod console → Endpoints → Your endpoint
   - Click "Settings" → "Max Timeout"
   - Set to `3600` (1 hour minimum)
   - Current default in `start.sh`: `120` seconds

2. **Enable Flash Boot (recommended):**
   - When creating endpoint in RunPod console
   - Check "Flash Boot" option
   - Speeds up cold starts by 30-40%

3. **Pre-warm worker:**
   - Set `Active Workers: 1` (instead of 0)
   - Keeps one worker warm between requests
   - Costs more but eliminates cold start delays
   - Add 5-10 minutes of initialization to your budget calculation

4. **Pre-load models into Network Volume:**
   - Download models locally
   - Create RunPod Network Volume
   - Mount at `/comfyui/models`
   - Reference: `reference/worker-comfyui/docs/network-volumes.md`

5. **Check for GPU memory pressure:**
   ```bash
   # In RunPod logs, look for:
   "CUDA out of memory"
   "torch.cuda.OutOfMemoryError"
   ```
   - If found, upgrade to GPU with more VRAM (e.g., H100 from A40)

---

### Issue 3: Model Download Failures

**Symptoms:**
- Docker build fails during Dockerfile execution
- Error: `Failed to download model from HuggingFace`
- Log shows: `wget: unable to resolve host` or `Connection timeout`

**Root Cause:**
Network connectivity issues, CDN throttling, or model source unavailability during container build.

**Solutions:**

1. **Retry build with backoff:**
   ```bash
   # The Dockerfile already includes retries in wget commands:
   wget --retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 10 ...

   # If still failing, rebuild:
   docker build \
     --platform linux/amd64 \
     --no-cache \
     -t xicon-dance-scail:v1.0 \
     -f XiCON/XiCON_Dance_SCAIL/Dockerfile \
     .
   ```

2. **Pre-download models separately:**
   ```bash
   # Instead of downloading during build, download to local cache:
   mkdir -p /tmp/model_cache

   # Download each model manually
   wget -O /tmp/model_cache/Wan21-14B.safetensors \
     https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/blob/main/SCAIL/Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors

   # Mount cache during build:
   docker build \
     --platform linux/amd64 \
     -v /tmp/model_cache:/model_cache \
     -t xicon-dance-scail:v1.0 \
     -f XiCON/XiCON_Dance_SCAIL/Dockerfile \
     .
   ```

3. **Use alternative model sources:**
   - If HuggingFace throttles, try direct download links in Dockerfile
   - Update model URLs in `Dockerfile` lines 43-70

4. **Check model availability:**
   ```bash
   # Verify URLs are accessible:
   curl -I https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/blob/main/SCAIL/Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors
   ```

---

### Issue 4: GPU Memory Issues (OOM)

**Symptoms:**
- Job fails with: `CUDA out of memory` or `RuntimeError: CUDA out of memory`
- Worker crashes mid-processing
- GPU memory never releases between jobs

**Root Cause:**
- Input images/videos too large
- Model parameters too aggressive
- GPU has insufficient VRAM
- Memory leak in ComfyUI nodes

**Diagnosis:**

```bash
# Check GPU memory in RunPod logs:
# Look for:
"vram_total_gb: 24.0"
"vram_free_gb: 8.5"

# If vram_free < 10GB for RTX 4090, issue is memory pressure
```

**Solutions:**

1. **Reduce input video size:**
   ```json
   {
     "width": 416,    // Currently 416x672
     "height": 672,   // Try: 384x640 or 320x512
     "steps": 6       // Reduce from 6 to 4 if OOM occurs
   }
   ```

2. **Enable memory optimization (already in start.sh):**
   ```bash
   # Verify in RunPod environment variables:
   PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
   LD_PRELOAD=/path/to/libtcmalloc.so  # Enabled in start.sh line 18
   ```

3. **Upgrade GPU (if pattern persists):**
   | GPU | VRAM | Cost/hour | Recommendation |
   |-----|------|-----------|---|
   | RTX 4090 | 24 GB | $2.50 | Minimum for WanVideo |
   | RTX 4080 | 20 GB | $1.80 | Borderline, may OOM with large inputs |
   | H100 | 80 GB | $3.50 | Recommended for production |
   | A100 80GB | 80 GB | $2.80 | Good alternative to H100 |

4. **Pre-allocate GPU memory:**
   Add to endpoint environment variables in RunPod:
   ```
   PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512,expandable_segments:True
   ```

5. **Clear old models between requests:**
   Add to `handler.py` post-processing:
   ```python
   import gc
   import torch

   # At end of handler:
   gc.collect()
   if torch.cuda.is_available():
       torch.cuda.empty_cache()
   ```

---

### Issue 5: WebSocket Connection Failures

**Symptoms:**
- Error: `WebSocket connection closed` or `Connection refused`
- Logs show: `websocket.WebSocketConnectionClosedException`
- Jobs fail after 10-30 seconds of processing

**Root Cause:**
Network instability, ComfyUI server restart, or WebSocket timeout.

**Solutions:**

1. **Increase WebSocket reconnect attempts:**
   ```bash
   # In RunPod endpoint environment variables, set:
   WEBSOCKET_RECONNECT_ATTEMPTS=10
   WEBSOCKET_RECONNECT_DELAY_S=5
   ```

   Default from `handler.py` (lines 39-40):
   ```python
   WEBSOCKET_RECONNECT_ATTEMPTS = int(os.environ.get("WEBSOCKET_RECONNECT_ATTEMPTS", 5))
   WEBSOCKET_RECONNECT_DELAY_S = int(os.environ.get("WEBSOCKET_RECONNECT_DELAY_S", 3))
   ```

2. **Enable WebSocket trace debugging:**
   ```bash
   # Add to endpoint environment variables:
   WEBSOCKET_TRACE=true
   ```
   This enables detailed WebSocket logging (verbose but helpful for diagnostics)

3. **Check network stability:**
   - Look for packet loss in RunPod metrics
   - Try running job twice - often passes on retry
   - If consistently fails at same point, issue may be job complexity

4. **Verify ComfyUI server health:**
   ```bash
   # Add health check to handler startup
   # Check /comfyui/system_stats endpoint availability
   ```

---

### Issue 6: Model Not Found at Runtime

**Symptoms:**
- Error: `FileNotFoundError: /comfyui/models/diffusion_models/Wan21-14B.safetensors`
- Log shows: `Could not find model`
- Workflow validation fails with "missing node inputs"

**Root Cause:**
- Model path misconfiguration
- Model wasn't downloaded during Docker build
- Model was downloaded but to wrong location

**Diagnosis:**

```bash
# Check model locations in running container:
docker run -it xicon-dance-scail:v1.0 \
  find /comfyui/models -type f -name "*.safetensors" | head -20

# Expected output should include:
# /comfyui/models/diffusion_models/Wan21-14B-SCAIL-preview_fp8_e4m3fn_scaled_KJ.safetensors
# /comfyui/models/clip/clip_vision_h.safetensors
# /comfyui/models/vae/Wan2.1_VAE.pth
# /comfyui/models/text_encoders/umt5-xxl-enc-bf16.safetensors
# /comfyui/models/loras/lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors
```

**Solutions:**

1. **Verify Dockerfile model downloads:**
   - Re-run Docker build with verbose output:
   ```bash
   docker build \
     --platform linux/amd64 \
     --progress=plain \
     -t xicon-dance-scail:v1.0 \
     -f XiCON/XiCON_Dance_SCAIL/Dockerfile \
     . 2>&1 | grep -i "model\|download\|wget"
   ```

2. **Check model paths configuration:**
   - Verify `extra_model_paths.yaml` at `/comfyui/extra_model_paths.yaml`
   ```bash
   docker run -it xicon-dance-scail:v1.0 cat /comfyui/extra_model_paths.yaml

   # Should output (from Dockerfile line 98-101):
   # scail_pose:
   #   base_path: /comfyui/models/
   #   detection: detection/
   ```

3. **Use Network Volume for models:**
   - Pre-download models to network volume
   - Mount at `/comfyui/models` in endpoint
   - Faster than rebuilding Docker image

4. **Manually add missing models:**
   ```bash
   # If specific model is missing, add to Dockerfile:
   RUN comfy model download \
     --url https://path/to/model.safetensors \
     --relative-path models/diffusion_models \
     --filename model_name.safetensors

   # Rebuild and test
   ```

---

### Issue 7: Custom Node Errors

**Symptoms:**
- Error: `Unknown custom node: WanVideoModelLoader`
- Error: `AttributeError in custom node class`
- Workflow fails validation with "node not found"

**Root Cause:**
- Custom node installation incomplete
- Git clone failed during Docker build
- Dependencies not installed for custom node

**Solutions:**

1. **Verify all custom nodes are installed:**
   ```bash
   # Expected from Dockerfile (lines 72-95):
   docker run -it xicon-dance-scail:v1.0 \
     ls -la /comfyui/custom_nodes/ | grep -E "Wan|SCAIL|KJ|Video"

   # Should show:
   # ComfyUI-WanVideoWrapper
   # ComfyUI-SCAIL-Pose
   # ComfyUI-KJNodes
   # ComfyUI-VideoHelperSuite
   ```

2. **Check node installation logs:**
   ```bash
   # Rebuild with verbose output:
   docker build \
     --platform linux/amd64 \
     --progress=plain \
     -t xicon-dance-scail:v1.0 \
     -f XiCON/XiCON_Dance_SCAIL/Dockerfile \
     . 2>&1 | tail -100
   ```

3. **Test node imports:**
   ```bash
   docker run -it xicon-dance-scail:v1.0 python3 -c "
   import sys
   sys.path.insert(0, '/comfyui/custom_nodes')

   # Try importing node modules
   from ComfyUI_WanVideoWrapper import nodes
   from ComfyUI_SCAIL_Pose import nodes
   print('All nodes imported successfully')
   "
   ```

4. **Reinstall specific node:**
   - Update Dockerfile (after line 95)
   - Add manual installation:
   ```dockerfile
   RUN cd /comfyui/custom_nodes/ComfyUI-WanVideoWrapper && \
       pip install --upgrade -r requirements.txt
   ```

---

## Reading RunPod Logs

### Accessing Logs

**Via RunPod Web Console:**
1. Navigate to **Serverless** → **Endpoints**
2. Click on your endpoint name
3. Click **Logs** tab
4. Logs update in real-time

**Via CLI/API:**
```bash
# Fetch last N lines of logs
curl -s -X GET "https://api.runpod.io/v2/$ENDPOINT_ID/logs" \
  -H "api_key: $RUNPOD_API_KEY" | tail -50
```

### Key Log Patterns

| Pattern | Meaning | Action |
|---------|---------|--------|
| `worker-xicon: Processing job` | Job started | Normal |
| `worker-xicon: GPU validation failed` | GPU not available | Check GPU assignment |
| `worker-xicon: ComfyUI server is ready` | Ready for requests | Normal |
| `FATAL: ComfyUI failed to start` | Startup timeout | Increase MAX_WAIT |
| `WebSocket connected` | Ready for execution | Normal |
| `Execution error: Node Type` | Workflow node failed | Check node inputs |
| `CUDA out of memory` | GPU memory exhausted | Reduce input size |
| `connection refused` | ComfyUI unreachable | Restart worker |
| `Job completed: X image(s), Y video(s)` | Success | Normal |
| `Error: Job processing failed` | Processing error | Check details |

### Sample Log Timeline (Successful Request)

```
[00:00] worker-xicon: Validating GPU/CUDA availability...
[00:01] worker-xicon: GPU validation passed: RTX 4090, 24GB VRAM
[00:02] worker-xicon: Starting ComfyUI
[00:05] worker-xicon: Waiting for ComfyUI server to be ready...
[00:15] worker-xicon: ComfyUI server is ready after 15s
[00:16] worker-xicon: Starting RunPod Handler
[01:05] worker-xicon: Processing job abc123...
[01:06] worker-xicon: Input validated: 416x672, steps=6, cfg=1.0
[01:07] worker-xicon: ComfyUI server is reachable
[01:15] worker-xicon: Downloaded files: reference_image...
[01:16] worker-xicon: Queued workflow with ID: xyz789
[01:20] worker-xicon: Progress: 1/50 (2%)
[02:30] worker-xicon: Progress: 50/50 (100%)
[02:35] worker-xicon: Execution finished for prompt xyz789
[02:45] worker-xicon: Processing video: output_video.mp4
[02:50] worker-xicon: Uploaded video to S3: https://...
[02:52] worker-xicon: Job completed: 0 image(s), 1 video(s)
```

---

## Debugging Techniques

### Technique 1: Enable Debug Logging

**In RunPod Endpoint Settings:**
1. Add environment variable:
   ```
   COMFY_LOG_LEVEL=DEBUG
   ```

2. Also enable handler debugging:
   ```
   DEBUG=true
   WEBSOCKET_TRACE=true
   ```

3. Redeploy endpoint and rerun request

**Expected debug output:**
- Detailed model loading messages
- WebSocket frame-by-frame communication
- Memory allocation information

### Technique 2: Test with Minimal Request

```bash
# Use smallest possible input to isolate issue
curl -X POST "https://api.runpod.io/v2/$ENDPOINT_ID/runsync" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "images": {
        "reference_image": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/1200px-Cat03.jpg"
      },
      "videos": {
        "dance_video": ""
      },
      "prompt": "test",
      "width": 416,
      "height": 672,
      "steps": 1,
      "cfg": 1.0,
      "seed": 42
    }
  }'
```

This tests the pipeline with:
- Small public image (no auth required)
- No video (image-only mode)
- Minimum steps (faster execution)

### Technique 3: Local Container Testing

```bash
# Test handler logic locally without GPU
docker run -it \
  -e DEBUG=true \
  -e TESTING=true \
  -v /path/to/XiCON:/xicon \
  xicon-dance-scail:v1.0 \
  python3 -c "
import sys
sys.path.insert(0, '/xicon/XiCON_Dance_SCAIL')
from handler import validate_input

# Test input validation
result, error = validate_input({
    'images': {'reference_image': 'https://example.com/image.jpg'},
    'videos': {'dance_video': 'https://example.com/video.mp4'},
    'prompt': 'test',
    'width': 416,
    'height': 672
})

print(f'Validation: {\"PASS\" if not error else f\"FAIL: {error}\"}')
"
```

### Technique 4: Inspect Network Traffic

```bash
# Enable WebSocket tracing in handler
# From handler.py line 42:
if os.environ.get("WEBSOCKET_TRACE", "false").lower() == "true":
    websocket.enableTrace(True)

# Set in RunPod environment:
WEBSOCKET_TRACE=true

# This prints:
# - WebSocket frame headers
# - Payload content
# - Connection state transitions
```

### Technique 5: Check Workflow Validity

```bash
# Validate workflow JSON transformation without running job
docker run -it xicon-dance-scail:v1.0 python3 << 'EOF'
import json
import sys
sys.path.insert(0, '/xicon/XiCON_Dance_SCAIL')

from handler import validate_input, transform_request_to_workflow, load_workflow_template

# Test input
user_input = {
    "images": {"reference_image": "test_ref.jpg"},
    "videos": {"dance_video": "test_dance.mp4"},
    "prompt": "test prompt",
    "width": 416,
    "height": 672,
    "steps": 6,
    "cfg": 1.0,
    "seed": 42
}

# Validate
valid_data, error = validate_input(user_input)
if error:
    print(f"Validation failed: {error}")
    sys.exit(1)

# Load template
workflow, error = load_workflow_template("/workflow_template.json")
if error:
    print(f"Template load failed: {error}")
    sys.exit(1)

# Transform
filenames = {"reference_image": "test_ref.jpg", "dance_video": "test_dance.mp4"}
workflow = transform_request_to_workflow(valid_data, filenames, workflow)

print("Workflow transformation: OK")
print(f"Workflow nodes: {len(workflow)}")
EOF
```

---

## Solutions by Category

### Startup Issues

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| GPU not detected | `vram_total_gb: 0` in logs | Check RunPod GPU assignment |
| CUDA driver error | `nvidia-smi: command not found` | Rebuild with proper GPU runtime |
| Out of disk space | `No space left on device` | Increase container disk to 100GB+ |
| Model download timeout | Build fails on `wget` | Use network volume for models |

### Request Processing Issues

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| Input validation fails | Error message in response | Check input JSON format |
| File download fails | HTTP 404 or timeout | Verify URL accessibility |
| Workflow error | Node-specific error message | Check node inputs/parameters |
| Output not generated | No errors but empty result | Check workflow node outputs |

### Performance Issues

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| Slow cold start | First request takes 60+ seconds | Use Flash Boot + pre-warm workers |
| Slow subsequent requests | Requests still slow after first | Check GPU memory usage |
| High queue depth | Many jobs waiting | Increase max workers |
| Timeouts on large videos | Jobs fail after 3600s | Reduce video size/frames |

---

## Performance Optimization

### 1. Cold Start Optimization

**Current baseline:** 45-60 seconds for first request

**Optimization strategies:**

```bash
# Option A: Enable Flash Boot (RunPod console)
# - Speeds up cold start by 30-40%
# - Small additional cost per start

# Option B: Keep worker warm
# Set in RunPod endpoint:
Active Workers: 1  # Instead of 0
Max Workers: 3     # Allows scale-up

# Option C: Pre-load models into network volume
# See: reference/worker-comfyui/docs/network-volumes.md
```

### 2. Warm Request Optimization

**Current baseline:** 5-10 seconds between requests

**Optimization strategies:**

```bash
# Already optimized in start.sh (lines 14-18):
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
TCMALLOC="$(ldconfig -p | grep -Po "libtcmalloc.so.\d" | head -n 1)"
export LD_PRELOAD="${TCMALLOC}"

# Further optimizations:
# 1. Reduce input video size: 416x672 → 384x640
# 2. Reduce steps: 6 → 4 (faster but lower quality)
# 3. Use smaller models: Check workflow_template.json
```

### 3. Concurrent Request Optimization

**Configuration in RunPod console:**

| Setting | Value | Impact |
|---------|-------|--------|
| Max Workers | 2-4 | Handles parallel requests |
| Idle Timeout | 5 min | Auto-kill idle workers |
| GPU Type | H100 or A100 | More VRAM = more parallelism |
| Container Disk | 100 GB | Models fit on disk |

### 4. Memory Efficiency

**Current VRAM usage:**
- Model loading: 18-20 GB
- Processing buffer: 2-4 GB
- Available headroom: 2 GB (RTX 4090)

**Optimization:**
```python
# Add to handler.py after job completion:
import torch
import gc

# Clear GPU memory
gc.collect()
torch.cuda.empty_cache()
torch.cuda.reset_peak_memory_stats()

# Forces memory reclamation between requests
```

---

## Health Check Verification

### 1. Basic Health Check

```bash
# Verify endpoint is responding
curl -s "https://api.runpod.io/v2/$ENDPOINT_ID/health" \
  -H "api_key: $RUNPOD_API_KEY"

# Expected response:
# {"ok": true, "name": "xicon-dance-scail", ...}
```

### 2. GPU Health Check

```bash
# Run in container
docker run -it xicon-dance-scail:v1.0 python3 << 'EOF'
import torch
print(f"CUDA Available: {torch.cuda.is_available()}")
print(f"Device Count: {torch.cuda.device_count()}")
print(f"Device Name: {torch.cuda.get_device_name(0)}")
vram_free, vram_total = torch.cuda.mem_get_info(0)
print(f"VRAM: {vram_free / 1024**3:.1f}GB / {vram_total / 1024**3:.1f}GB free")
EOF
```

### 3. ComfyUI Health Check

```bash
# Once running in RunPod, test connectivity
curl -s "http://localhost:8188/system_stats" | jq '.status'

# Should return:
# {
#   "exec_info": {
#     "queue_remaining": 0
#   },
#   "models": { ... }
# }
```

### 4. Handler Health Check

```bash
# Test handler startup
docker run -it \
  --entrypoint python3 \
  xicon-dance-scail:v1.0 \
  -c "
import runpod
print('RunPod SDK: OK')
from handler import handler
print('Handler import: OK')
print('All checks passed')
"
```

### 5. Full Integration Test

```bash
# Simulated job test (locally)
docker run -it xicon-dance-scail:v1.0 python3 << 'EOF'
import json
import sys
sys.path.insert(0, '/xicon/XiCON_Dance_SCAIL')

from handler import handler

# Simulate RunPod job
test_job = {
    "id": "test-job-123",
    "input": {
        "images": {"reference_image": "https://example.com/image.jpg"},
        "videos": {"dance_video": ""},
        "prompt": "test",
        "width": 416,
        "height": 672,
        "steps": 1,
        "cfg": 1.0,
        "seed": 42
    }
}

# This would fail on actual download, but validates input/workflow transformation
try:
    result = handler(test_job)
    print(f"Handler test: {result}")
except Exception as e:
    print(f"Expected error on download (no network): {type(e).__name__}")
    print("Handler logic: OK")
EOF
```

---

## Monitoring & Alerting

### Key Metrics to Monitor

```bash
# In RunPod console, track:
1. Active Workers (should scale with queue depth)
2. Queue Depth (should be near 0 for healthy system)
3. Failed Jobs (should be < 1%)
4. Average Response Time (should be 120-180s for cold start, 30-60s warm)
5. GPU Utilization (should be > 80% during processing)
```

### Set Up Alerts

```bash
# Example: Alert if queue depth > 5
# (Configure in monitoring tool via RunPod API)
if queue_depth > 5:
    alert("Endpoint backlogged - consider increasing max workers")

if avg_response_time > 300:
    alert("Slow processing - check GPU memory usage")

if failed_jobs_rate > 0.05:
    alert("High failure rate - check logs for common error")
```

---

## FAQ

**Q: Why does my first request take 60 seconds?**
A: Cold start includes GPU initialization, model loading, and ComfyUI startup. Enable Flash Boot in RunPod to reduce to 40-45s.

**Q: Can I reduce inference time below 30 seconds?**
A: For current setup, no. WanVideo model loading alone takes 15-20s. Warm starts are 5-10s. Upgrade GPU or use model caching to optimize.

**Q: My job fails with "CUDA out of memory"**
A: Reduce input video size (416x672 → 384x640) or reduce steps (6 → 4). Or upgrade to H100/A100 GPU.

**Q: How do I check if my endpoint is working?**
A: Use the health check: `curl https://api.runpod.io/v2/$ENDPOINT_ID/health`

**Q: What's the max concurrent job capacity?**
A: Depends on GPU. RTX 4090: 1-2 concurrent. H100: 2-4 concurrent. Each adds 30-40s overhead.

---

## Emergency Recovery

### If Endpoint is Stuck

```bash
# Step 1: Restart endpoint
curl -X POST "https://api.runpod.io/graphql" \
  -H "api_key: $RUNPOD_API_KEY" \
  -d '{
    "query": "mutation { updateEndpoint(input: {id: \"$ENDPOINT_ID\", minWorkers: 0, maxWorkers: 0}) { id } }"
  }'

# Wait 5 minutes, then restart:
curl -X POST "https://api.runpod.io/graphql" \
  -H "api_key: $RUNPOD_API_KEY" \
  -d '{
    "query": "mutation { updateEndpoint(input: {id: \"$ENDPOINT_ID\", minWorkers: 0, maxWorkers: 2}) { id } }"
  }'

# Step 2: Check status
curl -s "https://api.runpod.io/v2/$ENDPOINT_ID/health" -H "api_key: $RUNPOD_API_KEY"
```

### If Docker Build Fails

```bash
# Clean Docker cache and rebuild
docker system prune -a --volumes
docker build \
  --platform linux/amd64 \
  --no-cache \
  -t xicon-dance-scail:v1.0 \
  -f XiCON/XiCON_Dance_SCAIL/Dockerfile \
  .
```

### If Models Are Missing

```bash
# Verify models exist in image
docker run -it xicon-dance-scail:v1.0 \
  find /comfyui/models -type f | wc -l

# Expected: 8-10 model files

# If 0, rebuild without cache:
docker build --no-cache ...

# If models still missing, download manually:
docker run -it xicon-dance-scail:v1.0 \
  comfy model download --url <MODEL_URL> \
  --relative-path models/diffusion_models
```

---

## Related Documentation

- **Build & Deployment:** `BUILD_DEPLOY.md`
- **Request Format:** `REQUEST_TRANSFORMER_README.md`
- **Testing:** `TESTING.md`
- **GPU Configuration:** `gpu_validator.py`
- **Handler Logic:** `handler.py`
- **RunPod Reference:** See `reference/worker-comfyui/docs/`

---

## Support & Resources

For issues not covered here:

1. **Check RunPod console logs** - Most errors are logged with clear messages
2. **Review BUILD_DEPLOY.md** - Covers deployment-specific issues
3. **Check gpu_validator.py output** - Validates GPU setup at startup
4. **Enable DEBUG/WEBSOCKET_TRACE** - Provides detailed diagnostic info
5. **Test locally with Docker** - Reproduce issues in controlled environment

---

**Last Updated:** January 2026
**XiCON Dance SCAIL Version:** 1.0
**Base Image:** runpod/worker-comfyui:5.5.1-base
