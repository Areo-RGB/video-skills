#!/usr/bin/env python3
"""Convert jump-event and optional tracking CSV files into AE-friendly JSON.

Expected events CSV columns:
    player,time_s
Optional:
    player_name,type,confidence,count

Expected tracking CSV columns:
    player,time_s,x,y
Optional:
    confidence

Example:
    py export_ae_overlay_data.py events.csv \
      --tracking-csv pose_tracks.csv \
      --source-video training.mp4 \
      --fps 60 --width 3840 --height 2160 \
      --sample-hz 10 \
      --output overlay_data.json
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def read_csv(path: str) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def as_float(row: dict[str, str], key: str, default=None):
    value = row.get(key, "")
    if value in (None, ""):
        return default
    return float(value)


def player_key(row: dict[str, str]) -> str:
    value = row.get("player") or row.get("athlete_id") or row.get("player_id")
    if value in (None, ""):
        raise ValueError("CSV needs player, athlete_id, or player_id column")
    return str(value)


def main() -> None:
    ap = argparse.ArgumentParser(description="Export sports-analysis CSV data for After Effects overlays.")
    ap.add_argument("events_csv")
    ap.add_argument("--tracking-csv")
    ap.add_argument("--source-video", default="")
    ap.add_argument("--fps", type=float, required=True)
    ap.add_argument("--width", type=int, required=True)
    ap.add_argument("--height", type=int, required=True)
    ap.add_argument("--duration", type=float)
    ap.add_argument("--sample-hz", type=float, default=10.0, help="Maximum tracking samples/sec in output JSON.")
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    event_rows = read_csv(args.events_csv)
    players: dict[str, dict] = {}
    counts = defaultdict(int)

    # Events become cumulative counts per player unless the source already
    # provides an explicit count value.
    for row in sorted(event_rows, key=lambda r: (player_key(r), float(r["time_s"]))):
        pid = player_key(row)
        p = players.setdefault(pid, {
            "id": pid,
            "name": row.get("player_name") or f"Player {pid}",
            "events": [],
            "track": [],
        })
        explicit = row.get("count")
        if explicit not in (None, ""):
            count = int(float(explicit))
            counts[pid] = max(counts[pid], count)
        else:
            counts[pid] += 1
            count = counts[pid]

        ev = {
            "time_s": round(float(row["time_s"]), 6),
            "type": row.get("type") or "jump",
            "count": count,
        }
        conf = as_float(row, "confidence")
        if conf is not None:
            ev["confidence"] = round(conf, 6)
        p["events"].append(ev)

    if args.tracking_csv:
        tracking = read_csv(args.tracking_csv)
        by_player: dict[str, list[dict]] = defaultdict(list)
        for row in tracking:
            pid = player_key(row)
            if row.get("x", "") == "" or row.get("y", "") == "":
                continue
            by_player[pid].append(row)
            players.setdefault(pid, {
                "id": pid,
                "name": row.get("player_name") or f"Player {pid}",
                "events": [],
                "track": [],
            })

        min_dt = 0.0 if args.sample_hz <= 0 else 1.0 / args.sample_hz
        for pid, rows in by_player.items():
            rows.sort(key=lambda r: float(r["time_s"]))
            kept = []
            last_t = None
            for row in rows:
                t = float(row["time_s"])
                if last_t is not None and t - last_t < min_dt:
                    continue
                point = {
                    "time_s": round(t, 6),
                    "x": round(float(row["x"]), 3),
                    "y": round(float(row["y"]), 3),
                }
                conf = as_float(row, "confidence")
                if conf is not None:
                    point["confidence"] = round(conf, 6)
                kept.append(point)
                last_t = t
            players[pid]["track"] = kept

    duration = args.duration
    if duration is None:
        times = [ev["time_s"] for p in players.values() for ev in p["events"]]
        track_times = [pt["time_s"] for p in players.values() for pt in p["track"]]
        all_times = times + track_times
        duration = max(all_times) if all_times else 0.0

    data = {
        "schema": "video-skills.ae-overlay.v1",
        "source": {
            "video": args.source_video,
            "fps": args.fps,
            "width": args.width,
            "height": args.height,
            "duration_s": round(float(duration), 6),
        },
        "players": sorted(players.values(), key=lambda p: p["id"]),
        "style": {
            "counter_prefix": "",
            "font_size": 64,
            "track_offset": [0, -90],
        },
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(out.resolve())


if __name__ == "__main__":
    main()
