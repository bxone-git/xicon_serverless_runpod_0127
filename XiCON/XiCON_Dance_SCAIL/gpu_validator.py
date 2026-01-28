#!/usr/bin/env python3
"""
GPU/CUDA validation module for XiCON Dance SCAIL ComfyUI deployment.
Validates GPU availability before ComfyUI startup to prevent runtime failures.
"""

import subprocess
import sys
import torch
from typing import Tuple, Dict, Any


def validate_cuda(timeout_seconds: int = 10) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validates CUDA availability before ComfyUI startup.

    Args:
        timeout_seconds: Maximum time to wait for nvidia-smi command

    Returns:
        Tuple of (success: bool, message: str, details: dict)
        - success: True if all validation checks pass
        - message: Human-readable status message
        - details: Dictionary containing diagnostic information
    """
    details = {}

    # 1. Check NVIDIA driver via nvidia-smi
    try:
        result = subprocess.run(
            ['nvidia-smi'],
            capture_output=True,
            timeout=timeout_seconds,
            text=True
        )
        details['nvidia_smi'] = 'available' if result.returncode == 0 else 'failed'
        if result.returncode != 0:
            return False, f"nvidia-smi failed with code {result.returncode}", details
    except subprocess.TimeoutExpired:
        return False, f"nvidia-smi timed out after {timeout_seconds} seconds", details
    except FileNotFoundError:
        return False, "nvidia-smi not found - NVIDIA driver may not be installed", details
    except Exception as e:
        return False, f"nvidia-smi check failed: {str(e)}", details

    # 2. Check PyTorch CUDA availability
    details['torch_cuda_available'] = torch.cuda.is_available()
    if not torch.cuda.is_available():
        return False, "PyTorch reports CUDA unavailable", details

    # 3. Check CUDA device count
    try:
        device_count = torch.cuda.device_count()
        details['device_count'] = device_count
        if device_count == 0:
            return False, "No CUDA devices found", details

        # Get device names
        device_names = [torch.cuda.get_device_name(i) for i in range(device_count)]
        details['device_names'] = device_names
    except Exception as e:
        return False, f"Failed to query CUDA devices: {str(e)}", details

    # 4. Get VRAM information for primary device
    try:
        vram_free, vram_total = torch.cuda.mem_get_info(0)
        details['vram_free_gb'] = round(vram_free / (1024**3), 2)
        details['vram_total_gb'] = round(vram_total / (1024**3), 2)
        details['vram_used_gb'] = round((vram_total - vram_free) / (1024**3), 2)

        # Warn if less than 2GB free
        if vram_free < 2 * (1024**3):
            details['warning'] = f"Low VRAM available: {details['vram_free_gb']}GB free"
    except Exception as e:
        return False, f"Failed to get VRAM info: {str(e)}", details

    # 5. Get CUDA version
    try:
        cuda_version = torch.version.cuda
        details['cuda_version'] = cuda_version if cuda_version else "unknown"
    except Exception as e:
        details['cuda_version'] = f"error: {str(e)}"

    # 6. Get cuDNN version if available
    try:
        cudnn_version = torch.backends.cudnn.version()
        details['cudnn_version'] = cudnn_version if cudnn_version else "unknown"
        details['cudnn_enabled'] = torch.backends.cudnn.enabled
    except Exception as e:
        details['cudnn_version'] = f"error: {str(e)}"

    return True, "CUDA validation passed", details


def main():
    """Main entry point for standalone execution."""
    print("=" * 60)
    print("XiCON Dance SCAIL - GPU/CUDA Validation")
    print("=" * 60)

    success, message, details = validate_cuda()

    print(f"\nStatus: {'✓ SUCCESS' if success else '✗ FAILURE'}")
    print(f"Message: {message}")
    print(f"\nDetailed Information:")
    print("-" * 60)

    for key, value in details.items():
        if key == 'warning':
            print(f"⚠  {key}: {value}")
        else:
            print(f"  {key}: {value}")

    print("=" * 60)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
