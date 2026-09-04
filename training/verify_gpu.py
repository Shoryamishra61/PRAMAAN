"""Verify PyTorch GPU Support and Hardware Capabilities.

Directly satisfies Directive Requirement 3:
- PyTorch version
- CUDA runtime bundled with PyTorch
- torch.cuda.is_available()
- GPU name & total VRAM
- Device used by model tensors
- Peak allocated VRAM during test allocation
"""

from __future__ import annotations

from typing import Any

import torch
import torch.nn as nn


def verify_gpu_environment() -> dict[str, Any]:
    print("=" * 70)
    print("PYTORCH GPU HARDWARE VERIFICATION")
    print("=" * 70)

    pytorch_version = torch.__version__
    cuda_runtime = torch.version.cuda
    cuda_available = torch.cuda.is_available()

    print(f"PyTorch Version:           {pytorch_version}")
    print(f"CUDA Runtime in PyTorch:   {cuda_runtime}")
    print(f"CUDA Available:            {cuda_available}")

    gpu_name = "N/A"
    total_vram_gb = 0.0
    device_used = "cpu"
    peak_vram_mb = 0.0

    if cuda_available:
        device_count = torch.cuda.device_count()
        gpu_name = torch.cuda.get_device_name(0)
        total_vram_bytes = torch.cuda.get_device_properties(0).total_memory
        total_vram_gb = round(total_vram_bytes / (1024**3), 2)
        device = torch.device("cuda:0")
        device_used = str(device)

        print(f"Device Count:              {device_count}")
        print(f"GPU Name:                  {gpu_name}")
        print(f"Total VRAM:                {total_vram_gb} GB ({total_vram_bytes:,} bytes)")

        # Test physical memory allocation on GPU
        torch.cuda.reset_peak_memory_stats(device)
        test_tensor = torch.randn(1000, 1000, device=device, dtype=torch.float32)
        model = nn.Linear(1000, 100).to(device)
        out = model(test_tensor)
        loss = out.sum()
        loss.backward()

        peak_vram_bytes = torch.cuda.max_memory_allocated(device)
        peak_vram_mb = round(peak_vram_bytes / (1024**2), 2)

        print(f"Model & Tensor Device:     {test_tensor.device}")
        print(f"Peak VRAM During Test:     {peak_vram_mb} MB")
        del test_tensor, model, out, loss
        torch.cuda.empty_cache()
    else:
        print("WARNING: CUDA is not available. PyTorch is running on CPU.")
        device_used = "cpu"

    print("=" * 70)

    return {
        "pytorch_version": pytorch_version,
        "cuda_runtime": cuda_runtime,
        "cuda_available": cuda_available,
        "gpu_name": gpu_name,
        "total_vram_gb": total_vram_gb,
        "device_used": device_used,
        "peak_vram_mb": peak_vram_mb,
    }


if __name__ == "__main__":
    verify_gpu_environment()
