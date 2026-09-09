# After Effects / LLM automation

This branch adds After Effects-focused agent skills and MCP servers so visual overlays can move out of OpenCV/Python and into editable After Effects compositions.

## Recommended order

1. `engine-room-after-effects-mcp` — primary choice for direct AE control, batch operations, JSX escape hatches, screenshots/contact sheets, expressions, text, shapes, animation and rendering.
2. `heroic-swan-after-effects-mcp` — useful reference for deterministic scene construction, visual QA and motion-template workflows.
3. `ishu86-after-effects-mcp` — another compact AE MCP implementation with rendering/inspection tools.
4. `ae-agent-skills` — dedicated After Effects agent skills and CLI/declarative workflows.
5. `terminalskills` — large general skill collection; see its After Effects skill for ExtendScript/CEP/expressions/aerender guidance.
6. `adobe-agent-skills` — Adobe-focused agent skills with useful ExtendScript patterns and project-introspection ideas.

All upstream projects are included as git submodules and remain under their own licenses.

## Preferred sports-analysis architecture

```text
Python / CV
├── MediaPipe or RTMPose
├── athlete tracking / lane IDs
├── jump detection
├── event timestamps
└── overlay_data.json
          ↓
After Effects
├── import footage
├── athlete labels
├── jump counters
├── event flashes
├── tracked positions
├── shapes / lower thirds
├── animation / expressions
└── final render
```

Python should own **analysis and data**. After Effects should own **presentation**.

Do not burn polished counters, labels or design-heavy graphics into frames with OpenCV when the same information can be exported as structured data and rendered as editable AE layers.

## Local overlay skill

`overlay-from-analysis/` contains a small local skill and templates for the handoff:

- `SKILL.md` — workflow and AE rules.
- `scripts/export_ae_overlay_data.py` — convert jump-event/tracking CSV data into AE-friendly JSON.
- `scripts/build_jump_overlay.jsx` — ExtendScript template that creates player counter layers and optional position keyframes from that JSON.
- `assets/overlay-data.example.json` — example schema.

## Clone this branch

```bash
git clone --branch ae --recurse-submodules https://github.com/Areo-RGB/video-skills.git
```

For an existing clone:

```bash
git switch ae
git submodule update --init --recursive
```
