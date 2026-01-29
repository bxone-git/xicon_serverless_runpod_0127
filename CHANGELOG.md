# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.0] - 2026-01-29

### Fixed

#### Critical Race Condition in Handler Startup

**Problem:** Handler process started immediately after ComfyUI background process launched, without waiting for server readiness. This caused jobs to fail with connection errors within 0.132 seconds.

**Root Cause:** No health check mechanism to verify ComfyUI was fully initialized and accepting HTTP requests.

**Solution:** Implemented robust health check polling in startup sequence:
- Polls `/system_stats` endpoint every second
- Maximum wait time: 120 seconds
- Progress logging every 10 seconds for visibility
- Uses `wget` (available in base image) for compatibility
- Blocks Handler startup until ComfyUI responds with 200 OK

**Files Modified:**
- `XiCON/XiCON_Dance_SCAIL/start.sh` - Added health check loop (lines 32-54 and 61-83)
- `scripts/simulate-runpod.sh` - Created local testing simulation

**Evidence:** Jobs now properly initialize with full ComfyUI readiness verification before request processing begins.

**Impact:**
- Eliminates immediate connection failures
- Prevents race conditions between ComfyUI startup and request handling
- Improves job stability and reliability

### Changed

#### Asynchronous Download Replacement

**Changed:** Replaced asynchronous model downloads with synchronous `wget` calls in Dockerfile

**Rationale:**
- Simplifies build process and removes dependency on async frameworks
- Provides explicit retry logic with connection timeouts
- Uses standard `wget` options: `--retry-connrefused --waitretry=1 --read-timeout=20 --timeout=15 -t 10`
- Ensures all models are fully downloaded before build continues

**Files Modified:**
- `Dockerfile` - Lines 52-55 and 58-61 (text encoders and LoRA models)

#### ComfyUI Model Download Method

**Changed:** Large model downloads now use direct `wget` instead of `comfy model download` command

**Rationale:**
- Provides better timeout control and retry behavior
- Explicit progress feedback during build
- More reliable for large files (11.4GB text encoder, 739MB LoRA)

**Files Modified:**
- `Dockerfile` - Text encoder download (lines 52-55)
- `Dockerfile` - LightX2V LoRA download (lines 58-61)

### Added

#### Health Check Implementation

**Feature:** Automated server readiness verification in container startup

**Details:**
- Polling mechanism with HTTP 200 OK validation
- Configurable maximum wait time (120 seconds)
- Debug logging at regular intervals (every 10 seconds)
- Graceful failure with clear error messages if timeout exceeded

**Configuration:**
- `MAX_WAIT=120` - Maximum seconds to wait for ComfyUI
- `ELAPSED` - Tracks elapsed time with 1-second resolution
- Conditional progress output: every 10 seconds to reduce log spam

**Files Added:**
- `scripts/simulate-runpod.sh` - Local testing script that reproduces RunPod startup flow
  - Tests health check fix before deployment
  - Provides timing information for debugging
  - Includes cleanup and validation logic

#### Deployment Documentation Reference

**Added:** Reference to deployment guide from main README

**Location:** `README.md` line 58 points to `DEPLOYMENT.md` for detailed deployment procedures

**See Also:**
- Build & Deploy Guide: `XiCON/XiCON_Dance_SCAIL/BUILD_DEPLOY.md`
- Testing Guide: `XiCON/XiCON_Dance_SCAIL/TESTING.md`

## [1.0.0] - 2026-01-29

### Added

#### Initial XiCON Dance SCAIL RunPod Implementation

**Feature:** Complete serverless deployment for XiCON Dance SCAIL AI video generation

**Components:**
- Docker container with ComfyUI base image
- Custom RunPod Handler for workflow processing
- Request transformer for API compatibility
- GPU validation for CUDA availability
- Support for both local API serving and serverless modes

**Models Included (~30GB):**
- Wan21-14B-SCAIL checkpoint (7GB) - Video generation model
- umt5-xxl-enc text encoder (11.4GB) - Text to embedding conversion
- clip_vision_h (1.2GB) - Vision encoding
- Wan2.1_VAE (508MB) - Latent space variational autoencoder
- ViTPose detection model - Pose estimation
- YOLOv10m detection model - Object detection
- LightX2V LoRA (739MB) - Motion enhancement

**Custom Nodes:**
- ComfyUI-WanVideoWrapper - WanVideo model wrapper nodes
- ComfyUI-SCAIL-Pose - SCAIL pose estimation nodes
- ComfyUI-KJNodes - Utility nodes for image manipulation
- ComfyUI-VideoHelperSuite - Video processing and combination

**Files Included:**
- `Dockerfile` - Multi-stage build with model optimization
- `XiCON/XiCON_Dance_SCAIL/start.sh` - Container startup script
- `XiCON/XiCON_Dance_SCAIL/handler.py` - RunPod request handler
- `XiCON/XiCON_Dance_SCAIL/request_transformer.py` - API payload transformation
- `XiCON/XiCON_Dance_SCAIL/workflow_template.json` - ComfyUI workflow template
- `XiCON/XiCON_Dance_SCAIL/gpu_validator.py` - CUDA/GPU validation

**GPU Requirements:**
- Minimum: RTX 4090 (24GB VRAM)
- Recommended: A100 (40GB/80GB VRAM)

**Build Time:**
- First build: ~30-35 minutes
- Cached builds: ~5-10 minutes

**Deployment Options:**
1. Direct GitHub Repository Build (Recommended)
   - Automatic builds from repository
   - GitHub workflow integration
   - Direct endpoint creation on RunPod

2. Pre-built Docker Image (Coming Soon)
   - GHCR image: `ghcr.io/bxone-git/xicon-dance-scail:latest`

#### API Integration

**Feature:** Full API support for video generation requests

**Request Format:**
```json
{
  "input": {
    "workflow": {
      "prompt": "A dancer performing ballet",
      "reference_image": "https://example.com/dancer.jpg",
      "num_frames": 81,
      "width": 720,
      "height": 480
    }
  }
}
```

**Response Format:**
```json
{
  "output": {
    "video_url": "https://...",
    "frames": 81,
    "duration": 3.375
  }
}
```

**Features:**
- Automatic request validation
- Workflow payload transformation
- Video output generation and storage
- Error handling and detailed error messages

#### Development & Testing

**Features:**
- Local Docker build support
- Container testing with GPU passthrough
- Simulation script for health check validation
- Comprehensive testing guide

**Documentation:**
- Build & Deploy Guide
- Testing Guide
- Request Transformer Documentation
- Troubleshooting Guide

---

## Upgrading

### From v1.0.0 to v1.1.0

No breaking changes. Simply redeploy the container to benefit from:
- Race condition fixes
- Improved stability
- Better startup logging

The API interface remains unchanged.

---

## Related Documentation

- **Build & Deploy:** See [XiCON/XiCON_Dance_SCAIL/BUILD_DEPLOY.md](XiCON/XiCON_Dance_SCAIL/BUILD_DEPLOY.md)
- **Testing:** See [XiCON/XiCON_Dance_SCAIL/TESTING.md](XiCON/XiCON_Dance_SCAIL/TESTING.md)
- **API Details:** See [XiCON/XiCON_Dance_SCAIL/REQUEST_TRANSFORMER_README.md](XiCON/XiCON_Dance_SCAIL/REQUEST_TRANSFORMER_README.md)
- **Deployment:** See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Main README:** See [README.md](README.md)

---

## Notes for Contributors

### Commit Message Format

When making changes to this project, use these categories in your commit messages:

- `fix:` - Bug fixes (non-breaking)
- `feat:` - New features
- `breaking:` - Breaking API changes
- `docs:` - Documentation updates
- `refactor:` - Code refactoring without feature changes
- `perf:` - Performance improvements
- `test:` - Test additions or modifications
- `build:` - Build system changes
- `ci:` - CI/CD workflow changes

Example: `fix: Replace async download with synchronous requests`

### Verification Checklist

Before submitting changes:
- [ ] All tests pass
- [ ] No new warnings or errors introduced
- [ ] CHANGELOG.md updated with changes
- [ ] Documentation updated if needed
- [ ] Dockerfile builds successfully
- [ ] Container starts without errors
- [ ] Health check passes (if startup-related)

