# GPU video-analysis examples

## GTX 1660 YOLO / YOLO-Pose

`yolo_video_gtx1660.py` is tuned around the captured `DESKTOP-FRP61Q7` hardware: GTX 1660 6 GB, compute capability 7.5.

Recommended starting settings:

- `--imgsz 640`
- `--batch 8` for detection/pose; lower to 4 for larger models
- FP16 enabled by default on CUDA
- `--skip 2` or `--skip 3` when full-frame temporal resolution is unnecessary
- `yolo11n-pose.pt` for athlete pose + the included simple jump heuristic
- `yolo11n.pt` for maximum person-detection throughput

The script automatically splits an inference batch if CUDA runs out of memory.
### Install CUDA PyTorch on this machine

The current Python environment has `torch 2.14.0+cpu`. The CUDA 13.0 wheel index was verified to contain `torch 2.14.0+cu130`:

```powershell
py -m pip uninstall -y torch torchvision torchaudio
py -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
py examples/yolo_video_gtx1660.py --check
```

The NVIDIA 610.88 driver is new enough for this CUDA wheel; the locally installed full CUDA toolkit is not required for PyTorch wheels.

### Fast athlete / pose analysis

```powershell
py examples/yolo_video_gtx1660.py drill.mp4 --model yolo11n-pose.pt --batch 8 --skip 2 --count-jumps
```

Outputs `detections.csv`, `jump_events.csv`, and `annotated_nvenc.mp4` by default.
### Maximum detection throughput

```powershell
py examples/yolo_video_gtx1660.py drill.mp4 --model yolo11n.pt --batch 8 --skip 3
```

### Persistent tracking

```powershell
py examples/yolo_video_gtx1660.py drill.mp4 --model yolo11n.pt --mode track --batch 1 --skip 1
```

Tracking is intentionally sequential so ByteTrack state remains meaningful. Use batched detection/pose when stable IDs are not needed.

### Jump-count caveat

`--count-jumps` is an example heuristic for one dominant athlete and a mostly fixed camera. It uses pose landmarks and normalized vertical hip motion. For robust multi-athlete jump counting, use track IDs plus per-athlete pose histories and calibrate takeoff/landing against feet or ground contact.
