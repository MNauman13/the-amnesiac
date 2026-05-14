"use client";

import { useState } from "react";

const btn = {
  padding: "6px 12px", background: "#1e293b", border: "1px solid #334155",
  borderRadius: 5, color: "#94a3b8", cursor: "pointer", fontSize: 13, fontFamily: "monospace",
};

const SPEEDS = [
  { label: "0.5x", ms: 2000 },
  { label: "1x",   ms: 1000 },
  { label: "2x",   ms: 500  },
  { label: "4x",   ms: 250  },
];

export default function StepControls({
  current, total, onPrev, onNext, onFirst, onLast, onJump,
  progress, goalComplete,
  playing, onPlayPause, speedMs, onSpeedChange,
}) {
  const [jumpVal, setJumpVal] = useState("");

  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap",
      padding: "12px 16px", background: "#1e293b", borderRadius: 8,
      border: "1px solid #334155",
    }}>
      <button
        style={{ ...btn, minWidth: 80, color: playing ? "#fbbf24" : "#22c55e",
          borderColor: playing ? "#92400e" : "#14532d",
          background: playing ? "#1c1107" : "#0d1f0d" }}
        onClick={onPlayPause}
      >
        {playing ? "⏸ Pause" : "▶ Play"}
      </button>

      <div style={{ display: "flex", alignItems: "center", gap: 2 }}>
        {SPEEDS.map((s) => (
          <button
            key={s.label}
            style={{
              ...btn,
              padding: "4px 8px",
              background: speedMs === s.ms ? "#0ea5e9" : "#1e293b",
              color: speedMs === s.ms ? "#fff" : "#64748b",
              borderColor: speedMs === s.ms ? "#0284c7" : "#334155",
            }}
            onClick={() => onSpeedChange(s.ms)}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div style={{ width: 1, height: 20, background: "#334155", margin: "0 4px" }} />

      <button style={btn} onClick={onFirst}>⏮</button>
      <button style={btn} onClick={onPrev} disabled={current === 0}>◀</button>

      <span style={{ color: "#e2e8f0", fontSize: 14, fontWeight: 600, padding: "0 8px" }}>
        Step {current + 1} / {total}
      </span>

      <button style={btn} onClick={onNext} disabled={current === total - 1}>▶</button>
      <button style={btn} onClick={onLast}>⏭</button>

      <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
        <input
          type="number" min={1} max={total} placeholder="Jump…"
          value={jumpVal}
          onChange={(e) => setJumpVal(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") { onJump(parseInt(jumpVal, 10) - 1); setJumpVal(""); }
          }}
          style={{
            width: 70, padding: "5px 8px", background: "#0f1117",
            border: "1px solid #334155", borderRadius: 5, color: "#e2e8f0",
            fontSize: 13, fontFamily: "monospace",
          }}
        />
      </div>

      <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 10 }}>
        <span style={{ fontSize: 13, color: "#64748b" }}>Progress:</span>
        <div style={{ width: 120, height: 8, background: "#0f1117", borderRadius: 4, border: "1px solid #334155" }}>
          <div style={{
            height: "100%", borderRadius: 4,
            width: `${Math.round(progress * 100)}%`,
            background: goalComplete ? "#22c55e" : "#7dd3fc",
            transition: "width 0.3s",
          }} />
        </div>
        <span style={{ fontSize: 13, color: goalComplete ? "#22c55e" : "#7dd3fc" }}>
          {Math.round(progress * 100)}%{goalComplete ? " ✓" : ""}
        </span>
      </div>
    </div>
  );
}
