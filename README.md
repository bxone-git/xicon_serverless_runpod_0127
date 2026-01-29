# XiCON Serverless RunPod

RunPod Serverless implementations for XiCON AI video generation workflows.

## 📦 Available Implementations

### XiCON Dance SCAIL

AI-powered dance video generation using WanVideo SCAIL technology.

**Location:** `XiCON/XiCON_Dance_SCAIL/`

**Documentation:**
- [Build & Deploy Guide](XiCON/XiCON_Dance_SCAIL/BUILD_DEPLOY.md)
- [Testing Guide](XiCON/XiCON_Dance_SCAIL/TESTING.md)
- [Request Transformer](XiCON/XiCON_Dance_SCAIL/REQUEST_TRANSFORMER_README.md)

---

## 🚀 Quick Start - RunPod Deployment

### Option 1: Direct GitHub Repository Build (Recommended)

1. Go to [RunPod Serverless](https://www.runpod.io/console/serverless)
2. Click **New Endpoint**
3. Configure:
   ```
   Container Image Source: GitHub Repository
   Repository: https://github.com/bxone-git/xicon_serverless_runpod_0127
   Branch: master
   Dockerfile Path: Dockerfile (or leave blank)
   ```
4. Select GPU: RTX 4090 / A100
5. Deploy

### Option 2: Pre-built Image (Coming Soon)

```
ghcr.io/bxone-git/xicon-dance-scail:latest
```

---

## 📋 Recent Updates

### v1.1.0 - Race Condition Fix (2026-01-29)

**Fixed:** Critical race condition where Handler started before ComfyUI was ready, causing jobs to fail in 0.132s.

**Changes:**
- Added health check wait loop in `start.sh` (polls `/system_stats` endpoint)
- Wait up to 120 seconds for ComfyUI to be fully initialized
- Progress logging every 10 seconds for debugging
- Uses `wget` (available in base image) instead of `curl`

**Impact:** Jobs now properly wait for ComfyUI readiness before processing requests.

**Documentation:** See [DEPLOYMENT.md](./DEPLOYMENT.md) for deployment guide.

---

## 🛠️ Local Development

### Build Locally

```bash
# XiCON Dance SCAIL
docker build -t xicon-dance-scail:latest -f Dockerfile .
```

### Test Locally

```bash
docker run --gpus all -p 8000:8000 xicon-dance-scail:latest
```

---

## 📊 Models & Requirements

### XiCON Dance SCAIL

**Models (~30GB total):**
- Wan21-14B-SCAIL checkpoint (7GB)
- umt5-xxl-enc text encoder (11.4GB)
- clip_vision_h (1.2GB)
- Wan2.1_VAE (508MB)
- Detection models (vitpose, yolov10m)

**GPU Requirements:**
- Minimum: RTX 4090 (24GB VRAM)
- Recommended: A100 (40GB/80GB VRAM)

**Build Time:**
- First build: ~30-35 minutes
- Cached builds: ~5-10 minutes

---

## 📝 API Usage

### Request Format

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

### Response Format

```json
{
  "output": {
    "video_url": "https://...",
    "frames": 81,
    "duration": 3.375
  }
}
```

---

## 🔍 Troubleshooting

### Build Issues

**Timeout during model download:**
- RunPod servers have faster download speeds than local
- If build fails, retry - models are cached

**Dockerfile not found:**
- Ensure Dockerfile path is: `Dockerfile` (root) or blank
- Build context should be `.` or repository root

### Runtime Issues

See [XiCON Dance SCAIL Testing Guide](XiCON/XiCON_Dance_SCAIL/TESTING.md)

---

## 📚 Documentation

- [RunPod Serverless Docs](runpod_serverless_docs/)
- [Agent Documentation](agents/)
- [Skills](skills/)

---

## 🤝 Contributing

This project uses automated workflows with Claude Code.

**Generated with [Claude Code](https://claude.com/claude-code)**

---

## 📄 License

See individual implementation directories for licenses.
