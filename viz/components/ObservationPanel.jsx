"use client";

const SECTION_COLORS = {
  POSITION: "#7dd3fc",
  SURROUNDINGS: "#a78bfa",
  INVENTORY: "#34d399",
  "WORLD EVENTS SINCE LAST STEP": "#f59e0b",
  "GOAL REMINDER": "#f472b6",
  SYSTEM: "#f87171",
  "INSPECT RESULT": "#fbbf24",
};

function colorizeObservation(text) {
  if (!text) return [];
  return text.split("\n").map((line, i) => {
    const headerMatch = line.match(/^\[([^\]]+)\]/);
    let color = "#94a3b8";
    if (line.startsWith("===")) color = "#7dd3fc";
    else if (headerMatch) color = SECTION_COLORS[headerMatch[1]] || "#e2e8f0";
    else if (line.startsWith("  - ") || line.startsWith("  •")) color = "#e2e8f0";
    else if (line.trim().startsWith("(")) color = "#475569";
    return { line, color, key: i };
  });
}

export default function ObservationPanel({ observation }) {
  const lines = colorizeObservation(observation);
  return (
    <div style={{
      background: "#0f1117", border: "1px solid #334155", borderRadius: 8,
      overflow: "hidden",
    }}>
      <div style={{
        padding: "8px 14px", background: "#1e293b",
        borderBottom: "1px solid #334155", fontSize: 12, color: "#7dd3fc", fontWeight: 600,
      }}>
        OBSERVATION
      </div>
      <pre style={{
        margin: 0, padding: "12px 14px", fontSize: 12, lineHeight: 1.6,
        overflowY: "auto", maxHeight: 480, whiteSpace: "pre-wrap", wordBreak: "break-word",
      }}>
        {lines.map(({ line, color, key }) => (
          <span key={key} style={{ color, display: "block" }}>{line || " "}</span>
        ))}
      </pre>
    </div>
  );
}
