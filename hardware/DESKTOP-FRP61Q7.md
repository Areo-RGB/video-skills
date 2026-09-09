# DESKTOP-FRP61Q7 GPU/video analysis profile

Captured on 2026-09-09 from the Windows machine used for this repository.

## Hardware

- OS: Windows 11 Home 64-bit, version `10.0.26200`
- CPU: Intel Core i5-11400F, 6 cores / 12 threads
- RAM: 47.88 GiB (~48 GB)
- GPU: NVIDIA GeForce GTX 1660
- VRAM: 6144 MiB (6 GB)
- CUDA compute capability: 7.5
- NVIDIA driver: 610.88
- CUDA UMD reported by `nvidia-smi`: 13.3

## Verified acceleration

FFmpeg exposes CUDA plus Windows hardware acceleration backends. Actual smoke tests on this GPU:

- `h264_nvenc`: **working**
- `hevc_nvenc`: **working**
- `av1_nvenc`: **not supported by GTX 1660**

For video pipelines, prefer NVIDIA NVDEC/CUDA decode where the source codec is supported and NVENC for H.264/HEVC output.

## Current Python environment

- Python: 3.12.10
- PyTorch: 2.14.0+cpu — **CPU-only build; CUDA unavailable**
- OpenCV: 5.0.0 — CUDA device count 0; no `cudacodec`
- Ultralytics: 8.4.145
- CuPy: not installed

## Recommended Python GPU path

For YOLO and most ML/video-analysis work on this machine, use CUDA-enabled PyTorch rather than trying to make the standard OpenCV wheel handle GPU compute.

After installing a CUDA-enabled PyTorch build, verify it with:

```powershell
py -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

Expected device: `NVIDIA GeForce GTX 1660`.

Standard `opencv-python` wheels do not provide CUDA acceleration. If OpenCV CUDA APIs are specifically required, install/build an OpenCV distribution compiled with CUDA; otherwise use OpenCV for I/O/CPU preprocessing and PyTorch/Ultralytics for GPU inference.

See `examples/gpu_accel.py` for diagnostics, a CUDA benchmark, YOLO inference on GPU 0, and an FFmpeg NVENC transcode example.
