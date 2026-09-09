# video-skills

Curated collection of agent/LLM skills and plugins for video editing, video analysis, computer vision, YOLO, OpenCV, pose estimation, action recognition, and multimodal video understanding.

## Topics

### Video analysis
- `video-analysis/video-analyzer-skill` — frame extraction, scene detection, keyframes, Whisper/transcript-aware analysis.
- `video-analysis/video-expert-analyzer` — scene detection, multimodal frame scoring, subtitles, best-shot extraction.

### Computer vision / OpenCV
- `computer-vision/image-processing-skills` — OpenCV fundamentals, preprocessing, thresholding, morphology, contours, YOLO pipeline, MediaPipe tracking.
- `computer-vision/roboflow-computer-vision-skills` — inference, datasets, training/evaluation, batch processing, Universe and Roboflow workflows.

### YOLO / detection / tracking
- `yolo-detection-tracking/ultralytics-skills` — official Ultralytics skills for YOLO models, datasets, training, tuning, inference/tracking, and export.

### Pose estimation / action recognition
- `pose-action-recognition/nvidia-tao-pose-classification` — NVIDIA TAO pose classification skill using temporal skeleton/keypoint workflows.
- `pose-action-recognition/nvidia-tao-action-recognition` — NVIDIA TAO action recognition skill for temporal video classification.

### Video editing
- `video-editing/ffmpeg-skill` — FFmpeg-focused agent skill/tooling for editing, transforms, audio, captions, motion, QC, and batch workflows.
- `video-editing/mcp-video-editing` — MCP video editing toolkit with media inspection, editing, subtitles, effects, thumbnails/storyboards, and validation.

### LLM video understanding
- `llm-video-understanding/gemini-video-analysis-gist` — Gemini-oriented native video analysis skill with yt-dlp/FFmpeg preparation.
- `llm-video-understanding/gemini-video-understanding-skillsbench` — SkillsBench Gemini video-understanding skill, including configurable frame sampling for visual analysis.

## Useful entry points

- OpenCV/YOLO pipeline: `computer-vision/image-processing-skills/skills/06-yolo-pipeline/SKILL.md`
- MediaPipe tracking: `computer-vision/image-processing-skills/skills/07-mediapipe-tracking/SKILL.md`
- YOLO inference/tracking: `yolo-detection-tracking/ultralytics-skills/skills/yolo-inference/SKILL.md`
- NVIDIA pose classification: `pose-action-recognition/nvidia-tao-pose-classification/SKILL.md`
- NVIDIA action recognition: `pose-action-recognition/nvidia-tao-action-recognition/SKILL.md`
- FFmpeg editing: `video-editing/ffmpeg-skill/SKILL.md`
- MCP video editing: `video-editing/mcp-video-editing/skills/mcp-video/SKILL.md`
- General video analysis: `video-analysis/video-analyzer-skill/SKILL.md`

## Clone

Most upstream projects are Git submodules, so clone with:

```bash
git clone --recurse-submodules https://github.com/Areo-RGB/video-skills.git
```

For an existing clone:

```bash
git submodule update --init --recursive
```

## Upstream / licensing

This repository is an aggregation. Upstream projects remain linked as submodules where practical, preserving their own history and licenses. The two NVIDIA skills and the single SkillsBench skill are vendored as focused folders to avoid pulling very large source trees; their upstream commit references and license files are included alongside them.
## GPU acceleration example

This repo includes a machine-specific reference for `DESKTOP-FRP61Q7` and a reusable Python example:

- `hardware/DESKTOP-FRP61Q7.md` — GTX 1660 / CUDA / FFmpeg / Python capability snapshot.
- `examples/gpu_accel.py` — diagnostics, PyTorch CUDA benchmark, Ultralytics YOLO GPU inference, and FFmpeg NVENC transcoding.

```powershell
py examples/gpu_accel.py info
py examples/gpu_accel.py transcode input.mp4 output.mp4
py examples/gpu_accel.py benchmark
py examples/gpu_accel.py yolo input.mp4 --model yolo11n.pt
```

On the captured machine, FFmpeg NVENC works now. The installed PyTorch build is CPU-only, so the `benchmark` and `yolo` commands intentionally refuse to claim GPU acceleration until CUDA-enabled PyTorch is installed.

### GTX 1660 optimized YOLO video analysis

- `examples/yolo_video_gtx1660.py` — batched CUDA/FP16 YOLO or YOLO-Pose, frame skipping, optional ByteTrack, CSV detections/keypoints, simple jump counting, and H.264 NVENC annotated output.
- `examples/README.md` — tuned defaults and the verified CUDA PyTorch installation command for this machine.

```powershell
py examples/yolo_video_gtx1660.py drill.mp4 --model yolo11n-pose.pt --batch 8 --skip 2 --count-jumps
```
