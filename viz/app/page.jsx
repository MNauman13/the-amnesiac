"use client";

import { useState, useEffect, useCallback } from "react";
import StepViewer from "../components/StepViewer";

const DIFFICULTY_COLORS = {
  Easy:   "#22c55e",
  Medium: "#eab308",
  Hard:   "#f97316",
  Expert: "#a855f7",
};

function ExampleCard({ example, selected, loading, onClick }) {
  const color = DIFFICULTY_COLORS[example.difficulty] || "#94a3b8";
  const isSelected = selected === example.id;

  return (
    <button
      onClick={onClick}
      style={{
        flex: "1 1 220px", minWidth: 200, maxWidth: 320,
        padding: "16px 18px", textAlign: "left", cursor: "pointer",
        background: isSelected ? "#0f2035" : "#1e293b",
        border: `1px solid ${isSelected ? "#0ea5e9" : "#334155"}`,
        borderRadius: 10, transition: "border-color 0.15s, background 0.15s",
        position: "relative", overflow: "hidden",
      }}
    >
      {isSelected && (
        <div style={{
          position: "absolute", top: 0, left: 0, right: 0, height: 2,
          background: "linear-gradient(90deg, #0ea5e9, #7dd3fc)",
        }} />
      )}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 8 }}>
        <span style={{ fontSize: 14, fontWeight: 700, color: "#e2e8f0" }}>{example.label}</span>
        <span style={{
          fontSize: 11, fontWeight: 600, padding: "2px 7px", borderRadius: 12,
          background: color + "22", color, border: `1px solid ${color}55`,
        }}>
          {example.difficulty}
        </span>
      </div>
      <p style={{ fontSize: 12, color: "#64748b", margin: "0 0 12px", lineHeight: 1.5 }}>
        {example.description}
      </p>
      <div style={{ display: "flex", gap: 16 }}>
        <span style={{ fontSize: 12, color: "#7dd3fc" }}>
          Score: <strong>{example.score.toFixed(3)}</strong>
        </span>
        <span style={{ fontSize: 12, color: "#94a3b8" }}>
          {example.steps} steps
        </span>
      </div>
      {loading === example.id && (
        <div style={{
          position: "absolute", inset: 0, background: "#0f1117bb",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 13, color: "#7dd3fc",
        }}>
          Loading…
        </div>
      )}
    </button>
  );
}

export default function Home() {
  const [examples, setExamples] = useState([]);
  const [steps, setSteps] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loadingId, setLoadingId] = useState(null);
  const [error, setError] = useState("");
  const [autoPlay, setAutoPlay] = useState(false);

  useEffect(() => {
    fetch("/examples/manifest.json")
      .then((r) => r.json())
      .then(setExamples)
      .catch(() => {});
  }, []);

  const loadExample = useCallback(async (example) => {
    if (loadingId) return;
    setLoadingId(example.id);
    setError("");
    try {
      const res = await fetch(`/examples/${example.file}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const text = await res.text();
      const parsed = text.trim().split("\n").filter(Boolean).map((l) => JSON.parse(l));
      setSteps(parsed);
      setSelectedId(example.id);
      setAutoPlay(true);
    } catch (e) {
      setError(`Failed to load ${example.label}: ${e.message}`);
    } finally {
      setLoadingId(null);
    }
  }, [loadingId]);

  const handleFile = useCallback((e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const parsed = evt.target.result
          .trim().split("\n").filter(Boolean)
          .map((l) => JSON.parse(l));
        setSteps(parsed);
        setSelectedId(null);
        setAutoPlay(true);
        setError("");
      } catch (err) {
        setError("Failed to parse JSONL: " + err.message);
      }
    };
    reader.readAsText(file);
  }, []);

  return (
    <div style={{ maxWidth: 1400, margin: "0 auto", padding: "32px 16px" }}>
      <header style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 26, fontWeight: 700, color: "#7dd3fc", margin: "0 0 6px", letterSpacing: "-0.5px" }}>
          THE AMNESIAC
        </h1>
        <p style={{ color: "#475569", fontSize: 14, margin: 0, maxWidth: 600 }}>
          An LLM agent that forgets everything between every step and must design its own memory to survive.
          Select a pre-recorded run below to watch it play back live.
        </p>
      </header>

      {examples.length > 0 && (
        <section style={{ marginBottom: 28 }}>
          <h2 style={{ fontSize: 13, fontWeight: 600, color: "#475569", textTransform: "uppercase",
            letterSpacing: "0.08em", margin: "0 0 12px" }}>
            Example Runs
          </h2>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            {examples.map((ex) => (
              <ExampleCard
                key={ex.id}
                example={ex}
                selected={selectedId}
                loading={loadingId}
                onClick={() => loadExample(ex)}
              />
            ))}
          </div>
        </section>
      )}

      <section style={{ marginBottom: 24 }}>
        <h2 style={{ fontSize: 13, fontWeight: 600, color: "#475569", textTransform: "uppercase",
          letterSpacing: "0.08em", margin: "0 0 12px" }}>
          Or Load Your Own Log
        </h2>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
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
          <input id="logfile" type="file" accept=".jsonl,.json" onChange={handleFile} style={{ display: "none" }} />
          <span style={{ fontSize: 12, color: "#334155" }}>
            Run <code style={{ color: "#7dd3fc" }}>python main.py t3 --seed 7</code> then load <code style={{ color: "#7dd3fc" }}>logs/run_t3.jsonl</code>
          </span>
        </div>
        {error && <p style={{ color: "#f87171", fontSize: 13, marginTop: 8 }}>{error}</p>}
      </section>

      {steps.length > 0 ? (
        <StepViewer key={selectedId ?? "file"} steps={steps} autoPlay={autoPlay} />
      ) : (
        <div style={{
          padding: "48px 24px", textAlign: "center",
          border: "1px dashed #1e293b", borderRadius: 10, color: "#334155",
        }}>
          <p style={{ fontSize: 15, marginBottom: 8 }}>Select an example above to start watching.</p>
          <p style={{ fontSize: 13 }}>The agent replays step by step — you can pause, scrub, and inspect the memory scroll at every moment.</p>
        </div>
      )}
    </div>
  );
}
