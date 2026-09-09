#!/usr/bin/env python3
"""GPU acceleration examples for video/CV workloads on this PC.

Supports:
- hardware/software diagnostics
- FFmpeg CUDA decode + NVENC encode
- CUDA verification/benchmark with PyTorch
- Ultralytics YOLO inference on the NVIDIA GPU
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print("$", " ".join(str(x) for x in cmd))
    return subprocess.run(cmd, check=check)


def print_diagnostics() -> None:
    print("=== NVIDIA ===")
    if command_exists("nvidia-smi"):
        run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total,compute_cap", "--format=csv,noheader"])
    else:
        print("nvidia-smi: not found")

    print("\n=== PyTorch ===")
    try:
        import torch

        print("torch:", torch.__version__)
        print("compiled CUDA:", torch.version.cuda)
        print("CUDA available:", torch.cuda.is_available())
        if torch.cuda.is_available():
            print("device:", torch.cuda.get_device_name(0))
            print("compute capability:", torch.cuda.get_device_capability(0))
        else:
            print("NOTE: this PyTorch build is CPU-only; install a CUDA-enabled wheel.")
    except ImportError:
        print("torch: not installed")

    print("\n=== OpenCV ===")
    try:
        import cv2

        cuda_count = cv2.cuda.getCudaEnabledDeviceCount() if hasattr(cv2, "cuda") else 0
        print("opencv:", cv2.__version__)
        print("OpenCV CUDA devices:", cuda_count)
        print("cudacodec available:", hasattr(cv2, "cudacodec"))
        if cuda_count == 0:
            print("NOTE: standard pip OpenCV wheels are normally built without CUDA.")
    except ImportError:
        print("opencv: not installed")

    print("\n=== FFmpeg ===")
    if command_exists("ffmpeg"):
        run(["ffmpeg", "-hide_banner", "-hwaccels"], check=False)
    else:
        print("ffmpeg: not found")


def torch_benchmark(size: int = 4096) -> None:
    try:
        import torch
    except ImportError as exc:
        raise SystemExit("PyTorch is not installed.") from exc

    if not torch.cuda.is_available():
        raise SystemExit(
            "CUDA is not available in this PyTorch build. "
            "Install a CUDA-enabled PyTorch wheel first."
        )

    device = torch.device("cuda:0")
    print(f"Benchmarking on {torch.cuda.get_device_name(0)}")
    a = torch.randn((size, size), device=device)
    b = torch.randn((size, size), device=device)
    torch.cuda.synchronize()
    start = time.perf_counter()
    _ = a @ b
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - start
    print(f"{size}x{size} matrix multiply: {elapsed:.3f}s")
    allocated = torch.cuda.memory_allocated() / 1024**2
    print(f"CUDA memory allocated: {allocated:.1f} MiB")


def ffmpeg_nvenc(input_path: Path, output_path: Path) -> None:
    if not command_exists("ffmpeg"):
        raise SystemExit("ffmpeg is not on PATH.")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    base = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning"]
    gpu_cmd = base + [
        "-hwaccel", "cuda", "-i", str(input_path),
        "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "23",
        "-c:a", "copy", str(output_path),
    ]
    result = run(gpu_cmd, check=False)
    if result.returncode == 0:
        print("GPU decode + H.264 NVENC encode succeeded.")
        return

    print("CUDA decode failed; retrying with CPU decode + NVENC encode.")
    fallback_cmd = base + [
        "-i", str(input_path),
        "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "23",
        "-c:a", "copy", str(output_path),
    ]
    run(fallback_cmd, check=True)


def yolo_gpu(source: Path, model_name: str, conf: float) -> None:
    try:
        import torch
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("Install torch and ultralytics first.") from exc

    if not torch.cuda.is_available():
        raise SystemExit(
            "YOLO cannot use the GPU because the installed PyTorch build has no CUDA."
        )

    print(f"Running {model_name} on {torch.cuda.get_device_name(0)}")
    model = YOLO(model_name)
    frames = 0
    detections = 0
    for result in model.predict(
        source=str(source), device=0, stream=True, conf=conf, verbose=False
    ):
        frames += 1
        if result.boxes is not None:
            detections += len(result.boxes)

    print(f"Processed {frames} frames; total detections: {detections}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("info", help="show GPU/software acceleration status")

    bench = sub.add_parser("benchmark", help="verify PyTorch CUDA with a small benchmark")
    bench.add_argument("--size", type=int, default=4096)

    transcode = sub.add_parser("transcode", help="GPU-accelerated H.264 transcode with FFmpeg/NVENC")
    transcode.add_argument("input", type=Path)
    transcode.add_argument("output", type=Path)

    yolo = sub.add_parser("yolo", help="run Ultralytics YOLO inference on CUDA GPU 0")
    yolo.add_argument("source", type=Path)
    yolo.add_argument("--model", default="yolo11n.pt")
    yolo.add_argument("--conf", type=float, default=0.25)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "info":
        print_diagnostics()
    elif args.command == "benchmark":
        torch_benchmark(args.size)
    elif args.command == "transcode":
        ffmpeg_nvenc(args.input, args.output)
    elif args.command == "yolo":
        yolo_gpu(args.source, args.model, args.conf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
