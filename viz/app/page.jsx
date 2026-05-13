"use client";

import { useState, useCallback } from "react";
import StepViewer from "../components/StepViewer";

export default function Home() {
  const [steps, setSteps] = useState([]);
  const [error, setError] = useState("");

  const handleFile = useCallback((e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const text = evt.target.result;
        const parsed = text
          .trim()
          .split("\n")
          .filter(Boolean)
          .map((line) => JSON.parse(line));
        setSteps(parsed);
        setError("");
      } catch (err) {
        setError("Failed to parse JSONL: " + err.message);
        setSteps([]);
      }
    };
    reader.readAsText(file);
  }, []);

  return (
    <div style={{ maxWidth: 1400, margin: "0 auto", padding: "24px 16px" }}>
      <header style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, color: "#7dd3fc", margin: "0 0 4px" }}>
          THE AMNESIAC — Run Replay
        </h1>
        <p style={{ color: "#64748b", fontSize: 13, margin: 0 }}>
          Load a JSONL log file from <code>logs/</code> to replay a run step-by-step.
        </p>
      </header>

      <div style={{ marginBottom: 20 }}>
        <label
          htmlFor="logfile"
          style={{
            display: "inline-block", padding: "8px 16px",
            background: "#1e293b", border: "1px solid #334155",
            borderRadius: 6, cursor: "pointer", fontSize: 13, color: "#94a3b8",
          }}
        >
          📂 Load JSONL log file
        </label>
        <input
          id="logfile" type="file" accept=".jsonl,.json"
          onChange={handleFile}
          style={{ display: "none" }}
        />
        {steps.length > 0 && (
          <span style={{ marginLeft: 12, color: "#22c55e", fontSize: 13 }}>
            ✓ {steps.length} steps loaded
          </span>
        )}
        {error && (
          <span style={{ marginLeft: 12, color: "#f87171", fontSize: 13 }}>{error}</span>
        )}
      </div>

      {steps.length > 0 ? (
        <StepViewer steps={steps} />
      ) : (
        <div style={{
          padding: "40px 24px", textAlign: "center",
          border: "1px dashed #334155", borderRadius: 8, color: "#475569"
        }}>
          <p style={{ fontSize: 14 }}>No log loaded. Run a task first:</p>
          <code style={{ color: "#7dd3fc", fontSize: 13 }}>python main.py t1 --seed 42</code>
          <p style={{ fontSize: 13, marginTop: 8 }}>Then load the file from <code>logs/run_t1.jsonl</code></p>
        </div>
      )}
    </div>
  );
}
