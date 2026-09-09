---
name: after-effects-overlay-from-analysis
description: Turn structured sports/video-analysis data from Python, MediaPipe, RTMPose or tracking pipelines into editable After Effects overlays. Use for jump counters, athlete labels, tracked badges, event flashes, lower thirds and final AE rendering. Prefer an After Effects MCP for project manipulation and use batch/JSX operations for large keyframe sets.
---

# After Effects Overlay from Analysis Data

## Goal

Keep computer vision and event detection in Python, but move polished overlay creation into After Effects.

Preferred pipeline:

```text
video + CV analysis
      ↓
overlay_data.json
      ↓
After Effects MCP / ExtendScript
      ↓
editable layers + keyframes
      ↓
visual QA
      ↓
render
```

## Inputs

Prefer one JSON file containing:

- source video path
- source FPS / duration
- player IDs and names
- event timestamps and cumulative counts
- optional tracked X/Y positions
- optional confidence values
- optional style hints

Use `scripts/export_ae_overlay_data.py` to convert analysis CSVs into this schema.

## AE control surface

Preferred control surface: `../engine-room-after-effects-mcp`.

Useful alternatives/references:

- `../heroic-swan-after-effects-mcp`
- `../ishu86-after-effects-mcp`
- `../ae-agent-skills`
- `../terminalskills`
- `../adobe-agent-skills`

Do not depend on one MCP-specific command name in the data format. Keep the JSON adapter-neutral.

## Composition workflow

1. Inspect the AE project and source footage.
2. Create or select the target composition using the source dimensions/FPS.
3. Import and place the source footage.
4. Create a dedicated overlay precomp or clearly named overlay layer group.
5. Create one logical layer set per athlete.
6. Build counters from event timestamps.
7. If tracking is present, animate overlay position from sampled track points.
8. Add design/styling only after timing and identity are verified.
9. Capture representative frames/contact sheets from AE.
10. Correct timing, occlusion or layout problems before final render.

## Counter construction

For each athlete:

- create one text layer, e.g. `P01_JUMP_COUNT`
- initialize Source Text to `0`
- set Source Text keyframes at accepted event timestamps
- write the cumulative count, not just `+1`

Example event data:

```json
{"time_s": 1.82, "type": "jump", "count": 1}
```

The AE layer should become `1` at 1.82 s.

Do not create a separate layer for every number unless the design specifically requires it.

## Position tracking

When the analysis pipeline provides tracked positions:

```json
{"time_s": 1.5, "x": 824.2, "y": 390.6}
```

animate the overlay Position property.

Do not keyframe every source frame by default. Sample/simplify the path first unless frame-perfect tracking is required.

For a 60 FPS video, 6–15 tracking keyframes per second is often a better starting point for a smooth badge than 60 raw keyframes per second.

Keep player identity fixed. Never let a temporary detection swap cause the AE overlay to jump to another athlete.

## Coordinate rules

Analysis data should use source-video pixel coordinates.

If AE composition dimensions differ from the analysis source, scale coordinates explicitly:

```text
x_ae = x_source * comp_width / source_width
y_ae = y_source * comp_height / source_height
```

Do not assume 1920×1080.

## Presentation rules

Use AE for:

- typography
- shape layers
- badges
- counters
- lower thirds
- glow/flash feedback
- masks
- motion blur
- easing
- transitions
- final color/style integration

Keep Python/OpenCV overlays for diagnostics only.

## Efficient agent execution

Avoid hundreds of individual MCP calls for repetitive keyframes.

Prefer:

1. inspect comp/project using normal MCP tools
2. generate the complete intended operation set
3. apply with a batch tool or one reviewed JSX operation
4. inspect representative rendered frames
5. repair only what is wrong

Use `scripts/build_jump_overlay.jsx` as a generic ExtendScript starting point when a batch API is inconvenient.

## Visual QA

Always inspect the actual AE result, not only project-property readbacks.

Check frames:

- before first event
- exactly around several event timestamps
- during maximum athlete movement
- during overlaps/occlusions
- near the final event

Verify:

- correct athlete ↔ counter identity
- count increments once per accepted event
- label does not cover face/body unnecessarily
- position tracking is smooth
- no text appears outside safe bounds
- source and AE timing/FPS agree

## Debug vs final layers

Keep debug and presentation graphics separate.

Recommended naming:

```text
DEBUG_P01_TRACK
DEBUG_EVENT_MARKERS
P01_JUMP_COUNT
P01_NAME
P01_BADGE_BG
```

Debug layers may show confidence, raw position or event markers and can be disabled before final render.

## Data correction rule

After Effects must not invent or repair missing analysis events.

If a count/timestamp is wrong, correct the Python/CV analysis output and regenerate the overlay data. AE may adjust visual timing only when explicitly intended as a presentation offset.

## Completion checklist

- [ ] source FPS and comp FPS match or conversion is explicit
- [ ] overlay JSON loaded successfully
- [ ] player identities match analysis data
- [ ] every accepted event produces one count increment
- [ ] optional tracking coordinates map correctly into comp space
- [ ] representative AE frames inspected
- [ ] polished layers remain editable
- [ ] debug layers can be disabled independently
- [ ] final render is done from AE, not OpenCV
