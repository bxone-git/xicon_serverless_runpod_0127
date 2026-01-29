#!/usr/bin/env bash
# Simulates RunPod container startup flow locally
# Usage: ./scripts/simulate-runpod.sh
#
# This script reproduces the exact execution order from start.sh
# to verify the health check fix works before deploying.

set -e

echo "=== RunPod Startup Simulation ==="
echo "This matches the container flow in XiCON/XiCON_Dance_SCAIL/start.sh"

# 1. Set environment like RunPod
export CUDA_VISIBLE_DEVICES=0
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

# Adjust this path to your local ComfyUI installation
COMFYUI_PATH="${COMFYUI_PATH:-/comfyui}"

# 2. Start ComfyUI in background (matching start.sh line 35)
echo "[SIM $(date +%H:%M:%S.%3N)] Starting ComfyUI in background..."
python -u "${COMFYUI_PATH}/main.py" --disable-auto-launch --disable-metadata --listen &
COMFY_PID=$!
echo "[SIM $(date +%H:%M:%S.%3N)] ComfyUI PID: $COMFY_PID"

# 3. Wait for ComfyUI (THIS IS THE FIX WE'RE TESTING)
echo "[SIM $(date +%H:%M:%S.%3N)] Waiting for ComfyUI readiness..."
COMFY_READY=false
MAX_WAIT=120
ELAPSED=0

while [ "$COMFY_READY" = "false" ] && [ $ELAPSED -lt $MAX_WAIT ]; do
    if wget -q --spider --server-response http://127.0.0.1:8188/system_stats 2>&1 | grep -q "200 OK"; then
        COMFY_READY=true
        echo "[SIM $(date +%H:%M:%S.%3N)] ComfyUI ready after ${ELAPSED}s"
    else
        sleep 1
        ELAPSED=$((ELAPSED + 1))
        if [ $((ELAPSED % 10)) -eq 0 ]; then
            echo "[SIM $(date +%H:%M:%S.%3N)] Still waiting... (${ELAPSED}s)"
        fi
    fi
done

if [ "$COMFY_READY" = "false" ]; then
    echo "[SIM $(date +%H:%M:%S.%3N)] FATAL: ComfyUI timeout after ${MAX_WAIT}s"
    kill $COMFY_PID 2>/dev/null || true
    exit 1
fi

# 4. Now handler would start - simulate with a test request
echo "[SIM $(date +%H:%M:%S.%3N)] Handler would start here"
echo "[SIM $(date +%H:%M:%S.%3N)] Sending test request to verify connectivity..."

# Simple connectivity test
RESPONSE=$(wget -q --spider --server-response http://127.0.0.1:8188/system_stats 2>&1)

if echo "$RESPONSE" | grep -q "200 OK"; then
    echo "[SIM $(date +%H:%M:%S.%3N)] SUCCESS: ComfyUI responding correctly"
    echo "[SIM $(date +%H:%M:%S.%3N)] Response headers: $(echo "$RESPONSE" | head -n1)"
else
    echo "[SIM $(date +%H:%M:%S.%3N)] FAILURE: Unexpected HTTP response"
    echo "[SIM $(date +%H:%M:%S.%3N)] Response: $RESPONSE"
fi

# 5. Cleanup
echo "[SIM $(date +%H:%M:%S.%3N)] Stopping ComfyUI..."
kill $COMFY_PID 2>/dev/null || true
wait $COMFY_PID 2>/dev/null || true

echo "=== Simulation Complete ==="
echo ""
echo "If you saw 'ComfyUI ready after Xs' BEFORE 'Handler would start here',"
echo "the fix is working correctly."
