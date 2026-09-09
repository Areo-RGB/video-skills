#!/usr/bin/env python3
"""GTX 1660-tuned YOLO video analysis example.

Fast path: batched YOLO/YOLO-Pose inference on CUDA with FP16 and frame skipping.
Optional sequential tracking is available when stable track IDs matter more than throughput.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

import cv2
import numpy as np
import torch
from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", nargs="?", type=Path, help="Input video")
    p.add_argument("--model", default="yolo11n-pose.pt")
    p.add_argument("--device", default="0", help="CUDA device, e.g. 0")
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--batch", type=int, default=8, help="GTX 1660 starting point: 4-8")
    p.add_argument("--skip", type=int, default=1, help="Analyze every Nth source frame")
    p.add_argument("--conf", type=float, default=0.30)
    p.add_argument("--mode", choices=["detect", "track"], default="detect")
    p.add_argument("--tracker", default="bytetrack.yaml")
    p.add_argument("--fp16", action=argparse.BooleanOptionalAction, default=True)
    p.add_argument("--classes", type=int, nargs="*", default=[0], help="Default: person only")
    p.add_argument("--output", type=Path, default=Path("annotated_nvenc.mp4"))
    p.add_argument("--csv", type=Path, default=Path("detections.csv"))
    p.add_argument("--jump-events", type=Path, default=Path("jump_events.csv"))
    p.add_argument("--count-jumps", action="store_true", help="Single-athlete pose heuristic")
    p.add_argument("--no-video", action="store_true")
    p.add_argument("--allow-cpu", action="store_true", help="Testing only; much slower")
    p.add_argument("--check", action="store_true", help="Print acceleration status and exit")
    return p.parse_args()


def acceleration_status() -> int:
    print(f"torch={torch.__version__} compiled_cuda={torch.version.cuda}")
    print(f"cuda_available={torch.cuda.is_available()} devices={torch.cuda.device_count()}")
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            p = torch.cuda.get_device_properties(i)
            print(f"cuda:{i} {p.name} VRAM={p.total_memory / 2**30:.1f}GB cc={p.major}.{p.minor}")
    try:
        out = subprocess.check_output(
            ["ffmpeg", "-hide_banner", "-encoders"], text=True, stderr=subprocess.STDOUT
        )
        print(f"h264_nvenc={'h264_nvenc' in out} hevc_nvenc={'hevc_nvenc' in out}")
    except Exception as exc:
        print(f"ffmpeg check failed: {exc}")
    return 0


def require_cuda(allow_cpu: bool) -> str:
    if torch.cuda.is_available():
        torch.backends.cudnn.benchmark = True
        torch.set_float32_matmul_precision("high")
        return "cuda"
    if allow_cpu:
        print("WARNING: CUDA unavailable; --allow-cpu enabled.", file=sys.stderr)
        return "cpu"
    raise SystemExit(
        "CUDA PyTorch is not installed. Current build is CPU-only. "
        "Install a CUDA-enabled PyTorch wheel or pass --allow-cpu for a slow test."
    )


def start_nvenc(path: Path, width: int, height: int, fps: float) -> subprocess.Popen:
    path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "warning",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{width}x{height}",
        "-r", f"{fps:.6f}", "-i", "pipe:0", "-an",
        "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "23",
        "-pix_fmt", "yuv420p", str(path),
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def pose_arrays(result, index: int):
    if result.keypoints is None or result.keypoints.xy is None:
        return None, None
    xy = result.keypoints.xy[index].detach().cpu().numpy()
    conf = None
    if result.keypoints.conf is not None:
        conf = result.keypoints.conf[index].detach().cpu().numpy()
    return xy, conf


def center_y(xy: np.ndarray, conf: np.ndarray | None, ids: tuple[int, ...]) -> float | None:
    points = []
    for i in ids:
        if conf is None or conf[i] >= 0.25:
            x, y = xy[i]
            if x > 0 and y > 0:
                points.append(float(y))
    return float(np.mean(points)) if points else None


class JumpCounter:
    """Simple single-athlete, fixed-camera pose heuristic; not a lab-grade metric."""

    def __init__(self, threshold: float = 0.35):
        self.threshold = threshold
        self.baseline_hip: float | None = None
        self.airborne = False
        self.takeoff_t = 0.0
        self.max_rise = 0.0
        self.count = 0
        self.events: list[dict] = []

    def update(self, xy: np.ndarray, conf: np.ndarray | None, t: float) -> None:
        hip = center_y(xy, conf, (11, 12))
        shoulder = center_y(xy, conf, (5, 6))
        ankle = center_y(xy, conf, (15, 16))
        if hip is None or shoulder is None or ankle is None:
            return
        torso = max(20.0, hip - shoulder)
        if self.baseline_hip is None:
            self.baseline_hip = hip
        rise = (self.baseline_hip - hip) / torso
        if not self.airborne:
            self.baseline_hip = 0.97 * self.baseline_hip + 0.03 * hip
            if rise >= self.threshold:
                self.airborne, self.takeoff_t, self.max_rise = True, t, rise
        else:
            self.max_rise = max(self.max_rise, rise)
            if rise <= self.threshold * 0.45:
                duration = t - self.takeoff_t
                if 0.12 <= duration <= 2.0:
                    self.count += 1
                    self.events.append({
                        "jump": self.count,
                        "takeoff_s": round(self.takeoff_t, 3),
                        "landing_s": round(t, 3),
                        "duration_s": round(duration, 3),
                        "max_rise_torso": round(self.max_rise, 3),
                    })
                self.airborne = False
                self.baseline_hip = hip


def prediction_kwargs(args: argparse.Namespace) -> dict:
    return dict(
        imgsz=args.imgsz,
        conf=args.conf,
        classes=args.classes,
        device=args.device if torch.cuda.is_available() else "cpu",
        quantize=16 if (args.fp16 and torch.cuda.is_available()) else None,
        verbose=False,
    )


def infer_detect(model: YOLO, frames: list[np.ndarray], args: argparse.Namespace):
    try:
        return model.predict(frames, **prediction_kwargs(args))
    except torch.cuda.OutOfMemoryError:
        if len(frames) <= 1:
            raise
        torch.cuda.empty_cache()
        mid = len(frames) // 2
        print(f"CUDA OOM at batch={len(frames)}; retrying {mid}+{len(frames)-mid}")
        return infer_detect(model, frames[:mid], args) + infer_detect(model, frames[mid:], args)


def best_person_index(result) -> int | None:
    if result.boxes is None or len(result.boxes) == 0:
        return None
    xyxy = result.boxes.xyxy.detach().cpu().numpy()
    areas = (xyxy[:, 2] - xyxy[:, 0]) * (xyxy[:, 3] - xyxy[:, 1])
    return int(np.argmax(areas))

def rows_for_result(result, source_frame: int, t: float) -> list[dict]:
    rows: list[dict] = []
    if result.boxes is None:
        return rows
    boxes = result.boxes
    xyxy = boxes.xyxy.detach().cpu().numpy()
    confs = boxes.conf.detach().cpu().numpy()
    classes = boxes.cls.detach().cpu().numpy().astype(int)
    ids = boxes.id.detach().cpu().numpy().astype(int) if boxes.id is not None else None
    names = result.names
    for i, (box, score, cls_id) in enumerate(zip(xyxy, confs, classes)):
        kp_xy, kp_conf = pose_arrays(result, i)
        keypoints = None
        if kp_xy is not None:
            keypoints = [
                [round(float(x), 2), round(float(y), 2), round(float(kp_conf[j]), 3) if kp_conf is not None else None]
                for j, (x, y) in enumerate(kp_xy)
            ]
        rows.append({
            "source_frame": source_frame,
            "time_s": round(t, 3),
            "track_id": int(ids[i]) if ids is not None else "",
            "class_id": int(cls_id),
            "class_name": names[int(cls_id)],
            "confidence": round(float(score), 4),
            "x1": round(float(box[0]), 1), "y1": round(float(box[1]), 1),
            "x2": round(float(box[2]), 1), "y2": round(float(box[3]), 1),
            "keypoints_json": json.dumps(keypoints, separators=(",", ":")) if keypoints else "",
        })
    return rows


def annotate(result, jump_count: int | None) -> np.ndarray:
    frame = result.plot()
    if jump_count is not None:
        cv2.putText(frame, f"Jumps: {jump_count}", (20, 45), cv2.FONT_HERSHEY_SIMPLEX,
                    1.2, (255, 255, 255), 3, cv2.LINE_AA)
    return frame

def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["source_frame", "time_s", "track_id", "class_id", "class_name", "confidence",
              "x1", "y1", "x2", "y2", "keypoints_json"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_jump_csv(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["jump", "takeoff_s", "landing_s", "duration_s", "max_rise_torso"]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(events)


def main() -> int:
    args = parse_args()
    if args.check:
        return acceleration_status()
    if args.input is None:
        raise SystemExit("input video is required unless --check is used")
    require_cuda(args.allow_cpu)
    if args.skip < 1 or args.batch < 1:
        raise SystemExit("--skip and --batch must be >= 1")
    if args.mode == "track" and args.batch != 1:
        print("Tracking is sequential; --batch is ignored in track mode.")

    cap = cv2.VideoCapture(str(args.input))
    if not cap.isOpened():
        raise SystemExit(f"cannot open video: {args.input}")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out_fps = fps / args.skip
    model = YOLO(args.model)
    jump_counter = JumpCounter() if args.count_jumps else None
    encoder = None if args.no_video else start_nvenc(args.output, width, height, out_fps)
    all_rows: list[dict] = []
    pending_frames: list[np.ndarray] = []
    pending_meta: list[tuple[int, float]] = []
    source_frame = -1
    analyzed = 0
    started = time.perf_counter()
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()

    def consume(result, frame_no: int, timestamp: float) -> None:
        nonlocal analyzed
        all_rows.extend(rows_for_result(result, frame_no, timestamp))
        if jump_counter is not None:
            idx = best_person_index(result)
            if idx is not None:
                xy, kp_conf = pose_arrays(result, idx)
                if xy is not None:
                    jump_counter.update(xy, kp_conf, timestamp)
        if encoder is not None and encoder.stdin is not None:
            plotted = annotate(result, jump_counter.count if jump_counter else None)
            encoder.stdin.write(np.ascontiguousarray(plotted).tobytes())
        analyzed += 1

    def flush_batch() -> None:
        if not pending_frames:
            return
        results = infer_detect(model, pending_frames, args)
        for result, (frame_no, timestamp) in zip(results, pending_meta):
            consume(result, frame_no, timestamp)
        pending_frames.clear()
        pending_meta.clear()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        source_frame += 1
        if source_frame % args.skip:
            continue
        timestamp = source_frame / fps
        if args.mode == "track":
            results = model.track(
                frame, persist=True, tracker=args.tracker, **prediction_kwargs(args)
            )
            consume(results[0], source_frame, timestamp)
        else:
            pending_frames.append(frame)
            pending_meta.append((source_frame, timestamp))
            if len(pending_frames) >= args.batch:
                flush_batch()

    if args.mode == "detect":
        flush_batch()
    cap.release()
    if encoder is not None and encoder.stdin is not None:
        encoder.stdin.close()
        code = encoder.wait()
        if code != 0:
            raise SystemExit(f"FFmpeg NVENC exited with code {code}")

    write_csv(args.csv, all_rows)
    if jump_counter is not None:
        write_jump_csv(args.jump_events, jump_counter.events)
    elapsed = max(time.perf_counter() - started, 1e-9)
    print(f"Analyzed frames: {analyzed}")
    print(f"Detections: {len(all_rows)}")
    print(f"Analysis throughput: {analyzed / elapsed:.1f} processed fps")
    print(f"Source coverage: every {args.skip} frame(s); output fps={out_fps:.3f}")
    if jump_counter is not None:
        print(f"Estimated jumps: {jump_counter.count} (heuristic, single athlete/fixed camera)")
    if torch.cuda.is_available():
        peak = torch.cuda.max_memory_allocated() / 2**30
        print(f"Peak PyTorch VRAM: {peak:.2f} GB")
    print(f"CSV: {args.csv}")
    if encoder is not None:
        print(f"Annotated NVENC video: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

