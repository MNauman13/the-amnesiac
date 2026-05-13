"use client";

import { useState } from "react";

const btn = {
  padding: "6px 12px", background: "#1e293b", border: "1px solid #334155",
  borderRadius: 5, color: "#94a3b8", cursor: "pointer", fontSize: 13, fontFamily: "monospace",
};

export default function StepControls({
  current, total, onPrev, onNext, onFirst, onLast, onJump, progress, goalComplete,
}) {
  const [jumpVal, setJumpVal] = useState("");

  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap",
      padding: "12px 16px", background: "#1e293b", borderRadius: 8,
      border: "1px solid #334155"
    }}>
      <button style={btn} onClick={onFirst}>⏮ First</button>
      <button style={btn} onClick={onPrev} disabled={current === 0}>◀ Prev</button>

      <span style={{ color: "#e2e8f0", fontSize: 14, fontWeight: 600, padding: "0 8px" }}>
        Step {current + 1} / {total}
      </span>

      <button style={btn} onClick={onNext} disabled={current === total - 1}>Next ▶</button>
      <button style={btn} onClick={onLast}>Last ⏭</button>

      <div style={{ display: "flex", alignItems: "center", gap: 4, marginLeft: 8 }}>
        <input
          type="number" min={1} max={total} placeholder="Jump to…"
          value={jumpVal}
          onChange={(e) => setJumpVal(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") { onJump(parseInt(jumpVal, 10) - 1); setJumpVal(""); } }}
          style={{
            width: 80, padding: "5px 8px", background: "#0f1117",
            border: "1px solid #334155", borderRadius: 5, color: "#e2e8f0",
            fontSize: 13, fontFamily: "monospace",
          }}
        />
      </div>

      <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ fontSize: 13, color: "#64748b" }}>
          Progress:
        </div>
        <div style={{ width: 120, height: 8, background: "#1e293b", borderRadius: 4, border: "1px solid #334155" }}>
          <div style={{
            height: "100%", borderRadius: 4,
            width: `${Math.round(progress * 100)}%`,
            background: goalComplete ? "#22c55e" : "#7dd3fc",
            transition: "width 0.2s",
          }} />
        </div>
        <span style={{ fontSize: 13, color: goalComplete ? "#22c55e" : "#7dd3fc" }}>
          {Math.round(progress * 100)}%{goalComplete ? " ✓" : ""}
        </span>
      </div>
    </div>
  );
}
