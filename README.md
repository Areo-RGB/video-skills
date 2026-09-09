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