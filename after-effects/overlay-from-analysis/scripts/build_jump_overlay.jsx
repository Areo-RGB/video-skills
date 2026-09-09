/*
 * build_jump_overlay.jsx
 *
 * Generic ExtendScript template for creating editable jump counters from
 * video-skills.ae-overlay.v1 JSON.
 *
 * Intended usage:
 *   1. Set AE_OVERLAY_JSON_PATH and optionally AE_OVERLAY_COMP_NAME in the
 *      calling JSX/MCP context, then evaluate this file; OR
 *   2. Copy buildOverlayFromJson() into an MCP run_jsx/batch operation.
 *
 * This script creates one text layer per player, Source Text keyframes for
 * cumulative counts, and optional Position keyframes from exported tracks.
 */

function _readTextFile(path) {
    var f = new File(path);
    if (!f.exists) throw new Error("Overlay JSON not found: " + path);
    if (!f.open("r")) throw new Error("Cannot open overlay JSON: " + path);
    var text = f.read();
    f.close();
    return text;
}

function _findComp(name) {
    if (name) {
        for (var i = 1; i <= app.project.numItems; i++) {
            var item = app.project.item(i);
            if (item instanceof CompItem && item.name === name) return item;
        }
    }
    if (app.project.activeItem instanceof CompItem) return app.project.activeItem;
    throw new Error("No target composition found. Set AE_OVERLAY_COMP_NAME or activate a comp.");
}

function _scalePoint(source, comp, x, y) {
    return [
        x * comp.width / source.width,
        y * comp.height / source.height
    ];
}

function _textDocFor(layer, value, fontSize) {
    var prop = layer.property("ADBE Text Properties").property("ADBE Text Document");
    var doc = prop.value;
    doc.text = String(value);
    doc.fontSize = fontSize || 64;
    doc.justification = ParagraphJustification.CENTER_JUSTIFY;
    return doc;
}

function _createCounter(comp, source, player, style, index) {
    var layer = comp.layers.addText("0");
    layer.name = "P" + player.id + "_JUMP_COUNT";

    var textProp = layer.property("ADBE Text Properties").property("ADBE Text Document");
    textProp.setValue(_textDocFor(layer, "0", style.font_size || 64));

    // Count updates are cumulative values from analysis data.
    for (var i = 0; i < player.events.length; i++) {
        var ev = player.events[i];
        if (ev.type !== "jump" && ev.type !== "hop" && ev.type !== "rep") continue;
        textProp.setValueAtTime(ev.time_s, _textDocFor(layer, ev.count, style.font_size || 64));
    }

    var pos = layer.property("ADBE Transform Group").property("ADBE Position");
    var offset = style.track_offset || [0, -90];

    if (player.track && player.track.length) {
        for (var t = 0; t < player.track.length; t++) {
            var pt = player.track[t];
            var xy = _scalePoint(source, comp, pt.x, pt.y);
            pos.setValueAtTime(pt.time_s, [xy[0] + offset[0], xy[1] + offset[1]]);
        }
    } else {
        // Useful fallback layout when tracking is absent.
        var columns = Math.max(1, Math.ceil(Math.sqrt(4)));
        var x = comp.width * (0.20 + (index % columns) * 0.30);
        var y = comp.height * (0.12 + Math.floor(index / columns) * 0.18);
        pos.setValue([x, y]);
    }

    return layer;
}

function buildOverlayFromJson(jsonPath, compName) {
    app.beginUndoGroup("Build analysis overlay");
    try {
        var data = JSON.parse(_readTextFile(jsonPath));
        if (!data || data.schema !== "video-skills.ae-overlay.v1") {
            throw new Error("Unsupported overlay JSON schema");
        }

        var comp = _findComp(compName);
        var source = data.source;
        var style = data.style || {};

        // Optional convenience: align comp FPS with source when they differ.
        if (source.fps && Math.abs(comp.frameRate - source.fps) > 0.001) {
            comp.frameRate = source.fps;
        }

        var created = [];
        for (var i = 0; i < data.players.length; i++) {
            created.push(_createCounter(comp, source, data.players[i], style, i));
        }

        return {
            ok: true,
            comp: comp.name,
            layersCreated: created.length
        };
    } finally {
        app.endUndoGroup();
    }
}

// Optional auto-run when globals are injected by an MCP/runner.
if (typeof AE_OVERLAY_JSON_PATH !== "undefined" && AE_OVERLAY_JSON_PATH) {
    buildOverlayFromJson(
        AE_OVERLAY_JSON_PATH,
        (typeof AE_OVERLAY_COMP_NAME !== "undefined") ? AE_OVERLAY_COMP_NAME : null
    );
}
