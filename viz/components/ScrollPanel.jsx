"use client";

import { useState } from "react";

const HEADER_RE = /^\[([^\]]+)\]/;

function colorizeScroll(text) {
  if (!text || !text.trim()) return [{ line: "(empty)", color: "#475569", key: 0 }];
  return text.split("\n").map((line, i) => {
    const m = line.match(HEADER_RE);
    return {
      line,
      color: m ? "#7dd3fc" : line.trim().startsWith("-") ? "#e2e8f0" : "#94a3b8",
      key: i,
    };
  });
}

export default function ScrollPanel({ scrollBefore, scrollAfter, memoryWrite }) {
  const [showBefore, setShowBefore] = useState(false);
  const text = showBefore ? scrollBefore : scrollAfter;
  const lines = colorizeScroll(text);
  const bytes = scrollAfter ? new TextEncoder().encode(scrollAfter).length : 0;
  const pct = Math.min(100, Math.round((bytes / 2048) * 100));
  const barColor = pct > 90 ? "#f87171" : pct > 70 ? "#f59e0b" : "#22c55e";

  return (
    <div style={{
      background: "#0f1117", border: "1px solid #334155", borderRadius: 8,
      overflow: "hidden",
    }}>
      <div style={{
        padding: "8px 14px", background: "#1e293b",
        borderBottom: "1px solid #334155",
        display: "flex", alignItems: "center", gap: 10,
      }}>
        <span style={{ fontSize: 12, color: "#f59e0b", fontWeight: 600, flex: 1 }}>
          MEMORY SCROLL
        </span>
        <div style={{ display: "flex", gap: 4 }}>
          {["AFTER", "BEFORE"].map((label) => (
            <button
              key={label}
              onClick={() => setShowBefore(label === "BEFORE")}
              style={{
                padding: "2px 8px", fontSize: 11, fontFamily: "monospace",
                background: (label === "BEFORE") === showBefore ? "#334155" : "transparent",
                border: "1px solid #334155", borderRadius: 4,
                color: (label === "BEFORE") === showBefore ? "#e2e8f0" : "#475569",
                cursor: "pointer",
              }}
            >
              {label}
            </button>
          ))}
        </div>
        <span style={{ fontSize: 11, color: "#64748b" }}>{bytes}B / 2048B</span>
      </div>

      <div style={{ padding: "6px 14px", borderBottom: "1px solid #1e293b" }}>
        <div style={{ height: 5, background: "#1e293b", borderRadius: 3 }}>
          <div style={{
            height: "100%", borderRadius: 3, width: `${pct}%`,
            background: barColor, transition: "width 0.2s",
          }} />
        </div>
      </div>

      <pre style={{
        margin: 0, padding: "12px 14px", fontSize: 12, lineHeight: 1.6,
        overflowY: "auto", maxHeight: 455, whiteSpace: "pre-wrap", wordBreak: "break-word",
      }}>
        {lines.map(({ line, color, key }) => (
          <span key={key} style={{ color, display: "block" }}>{line || " "}</span>
        ))}
      </pre>
    </div>
  );
}
