# Build and Deployment Guide: XiCON Dance SCAIL

This guide provides step-by-step instructions for building, testing, and deploying the XiCON Dance SCAIL Docker image to RunPod Serverless.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development & Testing](#local-development--testing)
3. [Building the Docker Image](#building-the-docker-image)
4. [Testing the Image Locally](#testing-the-image-locally)
5. [Pushing to a Container Registry](#pushing-to-a-container-registry)
6. [Deploying to RunPod](#deploying-to-runpod)
7. [Verifying the Deployment](#verifying-the-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **Docker**: v20.10+ installed and running
- **Disk Space**: At least 100 GB free (for images, models, and build artifacts)
- **GPU** (optional for local testing): NVIDIA GPU with 24 GB+ VRAM recommended for WanVideo models
- **CUDA/NVIDIA Container Runtime** (optional, for GPU acceleration locally)

### Accounts & Credentials

- **Docker Registry Account**: Docker Hub, GitHub Container Registry, Amazon ECR, or Google Artifact Registry
- **RunPod Account**: Active RunPod account with API key (https://www.runpod.io)
- **GPU Access**: Ensure your RunPod account has sufficient credits for your desired GPU tier

### Environment Variables

Create a `.env` file in the project root or set these environment variables:

```bash
# Container Registry (choose one)
REGISTRY=docker.io  # Docker Hub: docker.io
REGISTRY_USERNAME=your_username
REGISTRY_PASSWORD=your_password  # Or access token

# Alternative: GitHub Container Registry
# REGISTRY=ghcr.io
# REGISTRY_USERNAME=your_github_username
# REGISTRY_PASSWORD=your_github_token

# RunPod Configuration
RUNPOD_API_KEY=your_runpod_api_key
RUNPOD_ENDPOINT_ID=ekd8hom4w7c2k5  # Your endpoint ID
```

---

## Local Development & Testing

### 1. Clone and Setup

```bash
# Navigate to project root
cd /mnt/x/xicon_serverless_runpod_0127

# Verify directory structure
ls -la XiCON/XiCON_Dance_SCAIL/
```

Expected files:
- `Dockerfile` - Container definition
- `handler.py` - RunPod request handler
- `request_transformer.py` - Request/workflow transformation logic
- `workflow_template.json` - ComfyUI workflow template
- `start.sh` - Container startup script
- `gpu_validator.py` - GPU validation on startup

### 2. Understand the Build

The Dockerfile:
- **Base Image**: `runpod/worker-comfyui:5.5.1-base` (ComfyUI + ComfyUI-Manager)
- **Models**: Downloads ~30 GB of WanVideo, CLIP, ViTPose, and YOLO models
- **Custom Nodes**: Installs WanVideoWrapper, SCAIL-Pose, KJNodes, VideoHelperSuite
- **Handler**: Custom RunPod handler for simplified API

Build time: 30-45 minutes (depending on model download speeds)
Final image size: ~60-80 GB

---

## Building the Docker Image

### Build Locally (CPU - Recommended for Development)

```bash
cd /mnt/x/xicon_serverless_runpod_0127

# Build the image
docker build \
  --platform linux/amd64 \
  -t xicon-dance-scail:v1.0 \
  -f XiCON/XiCON_Dance_SCAIL/Dockerfile \
  .

# Verify build succeeded
docker images | grep xicon-dance-scail
```

**Expected Output:**
```
REPOSITORY              TAG     IMAGE ID      CREATED        SIZE
xicon-dance-scail       v1.0    abc1234567    2 minutes ago   75.2GB
```

### Build with BuildKit (Faster, Parallel Layers)

```bash
# Enable BuildKit (faster builds with better caching)
export DOCKER_BUILDKIT=1

docker build \
  --platform linux/amd64 \
  -t xicon-dance-scail:v1.0 \
  -f XiCON/XiCON_Dance_SCAIL/Dockerfile \
  .
```

### Build with Custom Tags

Tag for versioning:

```bash
# Semantic versioning
docker build \
  --platform linux/amd64 \
  -t xicon-dance-scail:v1.0.0 \
  -f XiCON/XiCON_Dance_SCAIL/Dockerfile \
  .

# With date
docker build \
  --platform linux/amd64 \
  -t xicon-dance-scail:$(date +%Y%m%d-%H%M%S) \
  -f XiCON/XiCON_Dance_SCAIL/Dockerfile \
  .
```

### Troubleshooting Build Failures

**Issue: Model Download Timeouts**
```bash
# Retry with increased timeout
docker build \
  --platform linux/amd64 \
  --build-arg BUILDKIT_STEP_LOG_MAX_SIZE=10000000 \
  -t xicon-dance-scail:v1.0 \
  -f XiCON/XiCON_Dance_SCAIL/Dockerfile \
  .
```

**Issue: Out of Disk Space**
```bash
# Clean up Docker resources
docker system prune -a --volumes

# Check available space
df -h /var/lib/docker
```

**Issue: Network Issues During Model Download**
```bash
# The Dockerfile will retry automatically via comfy model download
# If it fails multiple times, manually pre-download models and mount as volume
# See section on Network Volumes in RunPod docs
```

---

## Testing the Image Locally

### Option 1: Interactive Shell (Minimal Testing)

```bash
# Start container with bash shell
docker run -it --rm \
  --platform linux/amd64 \
  xicon-dance-scail:v1.0 \
  /bin/bash

# Inside container, verify installation
ls -la /comfyui/
ls -la /comfyui/custom_nodes/
ls -la /comfyui/models/diffusion_models/

# Exit
exit
```

### Option 2: Test Handler Locally (CPU Simulation)

This tests the handler without GPU:

```bash
# Create a test request file
cat > test_request.json << 'EOF'
{
  "input": {
    "image_url": "https://example.com/input.jpg",
    "video_url": "https://example.com/input.mp4",
    "prompt": "dance animation",
    "num_frames": 16,
    "fps": 8
  }
}
EOF

# Run handler inside container
docker run -it --rm \
  --platform linux/amd64 \
  -e TESTING=true \
  xicon-dance-scail:v1.0 \
  python -c "
import json
from request_transformer import RequestTransformer

request = json.load(open('/dev/stdin'))
transformer = RequestTransformer()
try:
    workflow = transformer.transform(request['input'])
    print('Workflow transformation succeeded')
    print(json.dumps(workflow, indent=2)[:200] + '...')
except Exception as e:
    print(f'ERROR: {e}')
" < test_request.json
```

### Option 3: Run with GPU (If Available)

```bash
# Start the service with GPU (requires nvidia-docker or Docker with GPU support)
docker run -it --rm \
  --platform linux/amd64 \
  --gpus all \
  -p 8188:8188 \
  -p 8000:8000 \
  -e CUDA_VISIBLE_DEVICES=0 \
  xicon-dance-scail:v1.0

# In another terminal, test endpoint
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "workflow": {...}
    }
  }'
```

---

## Pushing to a Container Registry

### Option A: Docker Hub

```bash
# 1. Login to Docker Hub
docker login

# 2. Tag image for Docker Hub
docker tag xicon-dance-scail:v1.0 YOUR_USERNAME/xicon-dance-scail:v1.0

# 3. Push to Docker Hub
docker push YOUR_USERNAME/xicon-dance-scail:v1.0

# Verify push succeeded
docker search YOUR_USERNAME/xicon-dance-scail
```

### Option B: GitHub Container Registry

```bash
# 1. Create GitHub personal access token (PAT) with read:packages, write:packages scopes
# https://github.com/settings/tokens

# 2. Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# 3. Tag for GHCR
docker tag xicon-dance-scail:v1.0 ghcr.io/YOUR_GITHUB_USERNAME/xicon-dance-scail:v1.0

# 4. Push to GHCR
docker push ghcr.io/YOUR_GITHUB_USERNAME/xicon-dance-scail:v1.0
```

### Option C: Amazon ECR

```bash
# 1. Create ECR repository (if not exists)
aws ecr create-repository --repository-name xicon-dance-scail --region us-east-1

# 2. Get login token and login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# 3. Tag for ECR
docker tag xicon-dance-scail:v1.0 \
  YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/xicon-dance-scail:v1.0

# 4. Push to ECR
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/xicon-dance-scail:v1.0
```

### Option D: Google Artifact Registry

```bash
# 1. Configure gcloud
gcloud auth configure-docker us-central1-docker.pkg.dev

# 2. Create repository (if not exists)
gcloud artifacts repositories create xicon-dance-scail \
  --repository-format=docker \
  --location=us-central1

# 3. Tag for GAR
docker tag xicon-dance-scail:v1.0 \
  us-central1-docker.pkg.dev/YOUR_PROJECT_ID/xicon-dance-scail/xicon-dance-scail:v1.0

# 4. Push to GAR
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/xicon-dance-scail/xicon-dance-scail:v1.0
```

---

## Deploying to RunPod

### Method 1: Via RunPod Web Console (Recommended for Beginners)

#### Step 1: Create a Template

1. Go to [RunPod Console](https://www.runpod.io/console/serverless/user/templates)
2. Click **"New Template"**
3. Configure:
   - **Template Name**: `xicon-dance-scail` (or preferred name)
   - **Template Type**: Select **"Serverless"**
   - **Container Image**: Enter your full image URI:
     - Docker Hub: `YOUR_USERNAME/xicon-dance-scail:v1.0`
     - GHCR: `ghcr.io/YOUR_GITHUB_USERNAME/xicon-dance-scail:v1.0`
     - ECR: `YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/xicon-dance-scail:v1.0`
   - **Container Registry Credentials**:
     - If private repo, provide credentials (username/token)
     - Leave blank for public repos
   - **Container Disk**: `100 GB` (minimum for models)
   - **Max Timeout**: `3600` (1 hour for long video generation)
4. Click **"Save Template"**

#### Step 2: Create an Endpoint

1. Go to [Serverless Endpoints](https://www.runpod.io/console/serverless/user/endpoints)
2. Click **"New Endpoint"**
3. Configure:
   - **Endpoint Name**: `xicon-dance-scail` (or preferred name)
   - **Select Template**: Choose the template created above
   - **GPU**: Select your GPU (Recommendations below)
   - **Active Workers**: `0` (scale on demand)
   - **Max Workers**: `2-5` (based on budget and expected load)
   - **GPUs per Worker**: `1`
   - **Idle Timeout**: `5 minutes`
   - **Flash Boot**: `Enabled` (recommended)
4. Click **"Deploy"**
5. Wait for endpoint to initialize (2-5 minutes)
6. Note the **Endpoint ID** from the dashboard

#### GPU Recommendations

| GPU | VRAM | Max Batch | Approx Cost/Hour | Best For |
|-----|------|-----------|------------------|----------|
| RTX 4090 | 24 GB | 1-2 | $2.50 | Production, high quality |
| RTX 4080 | 20 GB | 1 | $1.80 | Balanced performance/cost |
| RTX 4070 Ti | 12 GB | 1 | $1.20 | Cost-effective |
| H100 | 80 GB | 2-4 | $3.50 | Maximum throughput |
| A100 80GB | 80 GB | 2-4 | $2.80 | High performance |

**Minimum recommendation**: RTX 4080 or better (WanVideo needs 24 GB)

### Method 2: Via RunPod API

```bash
#!/bin/bash

RUNPOD_API_KEY="your_runpod_api_key"
REGISTRY_IMAGE="YOUR_USERNAME/xicon-dance-scail:v1.0"
ENDPOINT_NAME="xicon-dance-scail"

# Create template
TEMPLATE_RESPONSE=$(curl -s -X POST "https://api.runpod.io/graphql" \
  -H "Content-Type: application/json" \
  -H "api_key: $RUNPOD_API_KEY" \
  -d '{
    "query": "mutation { saveTemplate(input: {name: \"'"$ENDPOINT_NAME"'\", dockerArgs: \"\", containerDiskInGb: 100, containerRegistryAuthId: null, dockerfile: null, imageUri: \"'"$REGISTRY_IMAGE"'\", isServerless: true, readme: \"XiCON Dance SCAIL\", variableDescription: null, variables: null}) { id name } }"
  }')

TEMPLATE_ID=$(echo $TEMPLATE_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "Template created: $TEMPLATE_ID"

# Create endpoint
ENDPOINT_RESPONSE=$(curl -s -X POST "https://api.runpod.io/graphql" \
  -H "Content-Type: application/json" \
  -H "api_key: $RUNPOD_API_KEY" \
  -d '{
    "query": "mutation { saveEndpoint(input: {gpuCount: 1, gpuIds: null, idleTimeout: 5, gpuTypeId: \"nvidia-rtx-4090\", locations: [], minWorkers: 0, maxWorkers: 2, name: \"'"$ENDPOINT_NAME"'\", networkVolumeId: null, startJetson: false, templateId: \"'"$TEMPLATE_ID"'\", volumeInGb: null}) { id name } }"
  }')

ENDPOINT_ID=$(echo $ENDPOINT_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "Endpoint created: $ENDPOINT_ID"
```

### Method 3: Via GitHub Integration (Auto-Deployment)

1. Push Dockerfile to GitHub repository
2. Go to [RunPod Console](https://www.runpod.io/console/serverless/user/endpoints)
3. Click **"New Endpoint"** → **"Start from GitHub Repo"**
4. Authenticate and select your repository
5. Configure GPU and scaling
6. RunPod automatically builds and deploys

---

## Verifying the Deployment

### 1. Check Endpoint Status

```bash
ENDPOINT_ID="ekd8hom4w7c2k5"
RUNPOD_API_KEY="your_runpod_api_key"

curl -s -X POST "https://api.runpod.io/graphql" \
  -H "Content-Type: application/json" \
  -H "api_key: $RUNPOD_API_KEY" \
  -d '{
    "query": "query { pod(input: {podId: \"'"$ENDPOINT_ID"'\"}) { id status gpuCount costPerHour networkVolume { id } } }"
  }' | jq '.'
```

### 2. Test the Endpoint (Async Request)

```bash
ENDPOINT_ID="ekd8hom4w7c2k5"
RUNPOD_API_KEY="your_runpod_api_key"

# Send request
RESPONSE=$(curl -s -X POST "https://api.runpod.io/v2/$ENDPOINT_ID/run" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "workflow": {
        "1": {
          "inputs": {
            "text": "a dancer performing",
            "clip": ["2", 1]
          },
          "class_type": "CLIPTextEncode"
        }
      }
    }
  }')

REQUEST_ID=$(echo $RESPONSE | jq -r '.id')
echo "Request ID: $REQUEST_ID"

# Poll for results (wait 30-120 seconds)
for i in {1..20}; do
  STATUS=$(curl -s -X GET "https://api.runpod.io/v2/$ENDPOINT_ID/status/$REQUEST_ID" \
    -H "api_key: $RUNPOD_API_KEY" | jq -r '.status')

  if [ "$STATUS" == "COMPLETED" ]; then
    echo "Request completed!"
    curl -s -X GET "https://api.runpod.io/v2/$ENDPOINT_ID/status/$REQUEST_ID" \
      -H "api_key: $RUNPOD_API_KEY" | jq '.output' | head -20
    break
  fi

  echo "Status: $STATUS (attempt $i/20)"
  sleep 6
done
```

### 3. Test the Endpoint (Sync Request)

For requests that complete quickly:

```bash
ENDPOINT_ID="ekd8hom4w7c2k5"
RUNPOD_API_KEY="your_runpod_api_key"

curl -X POST "https://api.runpod.io/v2/$ENDPOINT_ID/runsync" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "workflow": {...}
    }
  }' | jq '.'
```

### 4. Check Health Status

```bash
ENDPOINT_ID="ekd8hom4w7c2k5"

curl -X GET "https://api.runpod.io/v2/$ENDPOINT_ID/health"
```

---

## Troubleshooting

### Build Issues

#### Docker Build Fails with "Out of Memory"
**Solution:**
```bash
# Increase Docker memory limit
# On Linux, edit /etc/docker/daemon.json:
{
  "memory": "64g",
  "memswap": "64g"
}

# Restart Docker
sudo systemctl restart docker
```

#### Model Download Fails During Build
**Solution:**
```bash
# Use a volume-mounted model cache to speed up rebuilds
docker build \
  --platform linux/amd64 \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t xicon-dance-scail:v1.0 \
  -f XiCON/XiCON_Dance_SCAIL/Dockerfile \
  .
```

#### "Cannot connect to registry" when pushing
**Solution:**
```bash
# Verify credentials
docker logout
docker login YOUR_REGISTRY

# Check network connectivity
curl -I https://registry.hub.docker.com/
```

### RunPod Deployment Issues

#### Endpoint stays in "provisioning" state
**Solution:**
- Check RunPod console for error messages
- Verify GPU availability in your region
- Check container registry credentials if using private image
- Increase max timeout (may take 10+ minutes for first boot)

#### "Container fails to start" or "CrashLoopBackOff"
**Solution:**
```bash
# Check container logs via RunPod console
# Common causes:
# 1. GPU not available - check endpoint config
# 2. Image pull failed - verify registry credentials
# 3. Handler crash - check custom handler code

# Debug locally
docker run -it --rm \
  -e DEBUG=true \
  xicon-dance-scail:v1.0 \
  /bin/bash
```

#### Worker times out during video generation
**Solution:**
```bash
# Increase endpoint timeout
# Via console: Endpoint Settings → Max Timeout (set to 3600+ seconds)

# Or via API
curl -X POST "https://api.runpod.io/graphql" \
  -H "api_key: $RUNPOD_API_KEY" \
  -d '{
    "query": "mutation { updateEndpoint(input: {id: \"ekd8hom4w7c2k5\", maxTimeout: 3600}) { id maxTimeout } }"
  }'
```

#### GPU Out of Memory (OOM)
**Solution:**
- Use smaller input videos or frames
- Reduce batch size in workflow
- Upgrade to GPU with more VRAM (H100, A100)
- Enable model offloading (check ComfyUI settings)

#### Models not found at runtime
**Solution:**
```bash
# Option 1: Pre-download models into Network Volume
# See: reference/worker-comfyui/docs/network-volumes.md

# Option 2: Verify model paths in handler
# Check /comfyui/models/ structure inside container
docker run -it xicon-dance-scail:v1.0 \
  find /comfyui/models -type f -name "*.safetensors" | head -20
```

### Request/Response Issues

#### "Unknown custom node" error
**Solution:**
```bash
# Verify all required nodes are installed
# Inside container:
docker run -it xicon-dance-scail:v1.0 \
  ls -la /comfyui/custom_nodes/

# Expected directories:
# - ComfyUI-WanVideoWrapper
# - ComfyUI-SCAIL-Pose
# - ComfyUI-KJNodes
# - ComfyUI-VideoHelperSuite
```

#### "Workflow validation failed"
**Solution:**
```bash
# Validate workflow JSON structure
python -c "
import json
from request_transformer import RequestTransformer

workflow = json.load(open('workflow_template.json'))
transformer = RequestTransformer()
try:
  transformed = transformer.transform({'workflow': workflow})
  print('Workflow is valid')
except Exception as e:
  print(f'Validation error: {e}')
"
```

#### Response returns base64 instead of S3 URL
**Solution:**
```bash
# Configure S3 environment variables in endpoint
# Via console: Endpoint Settings → Environment Variables

# Required:
BUCKET_ENDPOINT_URL=https://s3.amazonaws.com
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
BUCKET_NAME=your_bucket

# Verify S3 credentials are correct
aws s3 ls s3://your_bucket --endpoint-url $BUCKET_ENDPOINT_URL
```

### Performance Issues

#### Jobs taking longer than expected
**Diagnosis:**
```bash
# Check worker logs
# Via RunPod console: Pod details → Logs

# Common causes:
# 1. Model loading time (first request takes 30-60s)
# 2. Insufficient GPU VRAM
# 3. Large input video or many frames
# 4. Network bottleneck downloading models

# Optimization:
# - Use Flash Boot (speeds up cold starts)
# - Keep worker alive with min_workers=1
# - Use network volumes for faster model access
```

#### High memory usage
**Solution:**
```bash
# Enable memory optimization in start.sh
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Use libtcmalloc (already enabled in start.sh)
# Reduce batch size in workflow
```

---

## Environment Variables Reference

Key environment variables for the endpoint:

| Variable | Default | Purpose | Example |
|----------|---------|---------|---------|
| `CUDA_VISIBLE_DEVICES` | 0 | GPU device to use | `0,1` |
| `PYTORCH_CUDA_ALLOC_CONF` | `expandable_segments:True` | GPU memory optimization | - |
| `COMFY_LOG_LEVEL` | `DEBUG` | Log verbosity | `INFO`, `WARNING` |
| `SERVE_API_LOCALLY` | `false` | Run API server locally | `true`, `false` |
| `WEBSOCKET_RECONNECT_ATTEMPTS` | `5` | Retry connection attempts | `10` |
| `WEBSOCKET_RECONNECT_DELAY_S` | `3` | Delay between retries (seconds) | `5` |
| `BUCKET_ENDPOINT_URL` | - | S3 endpoint URL | `https://s3.amazonaws.com` |
| `AWS_ACCESS_KEY_ID` | - | S3 access key | - |
| `AWS_SECRET_ACCESS_KEY` | - | S3 secret key | - |
| `BUCKET_NAME` | - | S3 bucket name | `my-xicon-outputs` |
| `REFRESH_WORKER` | `false` | Refresh ComfyUI on start | `true` |

---

## Performance Benchmarks

Typical performance on recommended GPUs (single worker):

| Metric | RTX 4090 | RTX 4080 | H100 |
|--------|----------|----------|------|
| Cold start (1st request) | 45-60s | 50-65s | 40-55s |
| Warm start | 5-10s | 8-12s | 5-8s |
| 16-frame generation | 2-3 min | 3-4 min | 1-2 min |
| 32-frame generation | 4-6 min | 6-8 min | 2-3 min |
| Concurrent workers | 1-2 | 1 | 2-3 |

**Notes:**
- Times vary with input video size, text prompt complexity, and SCAIL parameters
- Network I/O for model downloads can add 20-40% overhead on first request
- S3 upload time adds 10-30 seconds depending on output size and region

---

## Next Steps

1. **Monitor Deployment**: Use RunPod console to track worker status and logs
2. **Set Up Logging**: Configure CloudWatch or other monitoring for production
3. **Optimize Costs**: Adjust idle timeout and max workers based on usage patterns
4. **Create Backups**: Regularly export endpoint configurations
5. **Scale Up**: Add more workers or use auto-scaling based on queue depth

---

## Additional Resources

- [RunPod Serverless Documentation](https://docs.runpod.io/serverless/overview)
- [ComfyUI Documentation](https://github.com/comfyanonymous/ComfyUI)
- [WanVideo ComfyUI Wrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)
- [SCAIL-Pose Documentation](https://github.com/kijai/ComfyUI-SCAIL-Pose)
- [XiCON Request Transformer README](./REQUEST_TRANSFORMER_README.md)

---

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review RunPod endpoint logs in the console
3. Check custom handler logs: `REQUEST_TRANSFORMER_README.md` for request format details
4. Open an issue in the GitHub repository with:
   - Exact error message
   - RunPod endpoint logs
   - Request payload (sanitized)
   - Expected vs actual behavior
