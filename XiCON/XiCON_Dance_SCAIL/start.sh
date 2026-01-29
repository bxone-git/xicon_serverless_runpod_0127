#!/usr/bin/env bash
set -e

# GPU Validation
echo "worker-xicon: Validating GPU/CUDA availability..."
python /gpu_validator.py
if [ $? -ne 0 ]; then
    echo "FATAL: GPU validation failed. Check RunPod GPU configuration."
    exit 1
fi

# CUDA Configuration
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Use libtcmalloc for better memory management
TCMALLOC="$(ldconfig -p | grep -Po "libtcmalloc.so.\d" | head -n 1)"
export LD_PRELOAD="${TCMALLOC}"

# Ensure ComfyUI-Manager runs in offline network mode
comfy-manager-set-mode offline || echo "worker-xicon - Could not set ComfyUI-Manager network_mode" >&2

echo "worker-xicon: Starting ComfyUI"

# Allow operators to tweak verbosity; default is DEBUG
: "${COMFY_LOG_LEVEL:=DEBUG}"

# Serve the API and don't shutdown the container
if [ "$SERVE_API_LOCALLY" == "true" ]; then
    python -u /comfyui/main.py --disable-auto-launch --disable-metadata --listen --verbose "${COMFY_LOG_LEVEL}" --log-stdout &

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
            if [ $((ELAPSED % 10)) -eq 0 ]; then
                echo "worker-xicon: Still waiting for ComfyUI... (${ELAPSED}s elapsed)"
            fi
        fi
    done

    if [ "$COMFY_READY" = "false" ]; then
        echo "FATAL: ComfyUI failed to start within ${MAX_WAIT}s"
        exit 1
    fi

    echo "worker-xicon: Starting RunPod Handler"
    python -u /handler.py --rp_serve_api --rp_api_host=0.0.0.0
else
    python -u /comfyui/main.py --disable-auto-launch --disable-metadata --verbose "${COMFY_LOG_LEVEL}" --log-stdout &

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
            if [ $((ELAPSED % 10)) -eq 0 ]; then
                echo "worker-xicon: Still waiting for ComfyUI... (${ELAPSED}s elapsed)"
            fi
        fi
    done

    if [ "$COMFY_READY" = "false" ]; then
        echo "FATAL: ComfyUI failed to start within ${MAX_WAIT}s"
        exit 1
    fi

    echo "worker-xicon: Starting RunPod Handler"
    python -u /handler.py
fi
