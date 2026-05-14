"use client";

import { useState, useEffect } from "react";
import ScrollPanel from "./ScrollPanel";
import ObservationPanel from "./ObservationPanel";
import StepControls from "./StepControls";
import StepSummary from "./StepSummary";
import WorldGridPanel from "./WorldGridPanel";

export default function StepViewer({ steps, autoPlay = false }) {
  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speedMs, setSpeedMs] = useState(1000);
  const [showObs, setShowObs] = useState(false);

  useEffect(() => {
    setIdx(0);
    setShowObs(false);
    if (autoPlay) setPlaying(true);
  }, [steps, autoPlay]);

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setIdx((i) => {
        if (i >= steps.length - 1) {
          setPlaying(false);
          return i;
        }
        return i + 1;
      });
    }, speedMs);
    return () => clearInterval(id);
  }, [playing, speedMs, steps.length]);

  const step = steps[idx];
  if (!step) return null;

  return (
    <div>
      <StepControls
        current={idx}
        total={steps.length}
        onPrev={() => setIdx((i) => Math.max(0, i - 1))}
        onNext={() => setIdx((i) => Math.min(steps.length - 1, i + 1))}
        onFirst={() => setIdx(0)}
        onLast={() => setIdx(steps.length - 1)}
        onJump={(n) => setIdx(Math.min(Math.max(0, n), steps.length - 1))}
        progress={step.goal_progress}
        goalComplete={step.goal_complete}
        playing={playing}
        onPlayPause={() => setPlaying((p) => !p)}
        speedMs={speedMs}
        onSpeedChange={setSpeedMs}
      />

      {/* Main panels — grid left, scroll right */}
      <div style={{ display: "flex", gap: 16, marginTop: 16, alignItems: "flex-start" }}>
        <WorldGridPanel worldState={step.world_state} />

        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 16, minWidth: 0 }}>
          <ScrollPanel
            scrollBefore={step.scroll_before}
            scrollAfter={step.scroll_after}
            memoryWrite={step.memory_write}
          />
          <StepSummary step={step} />
        </div>
      </div>

      {/* Collapsible observation text */}
      <div style={{ marginTop: 12 }}>
        <button
          onClick={() => setShowObs((v) => !v)}
          style={{
            padding: "5px 14px", background: "#1e293b", border: "1px solid #334155",
            borderRadius: 5, color: "#64748b", cursor: "pointer", fontSize: 12,
            fontFamily: "monospace",
          }}
        >
          {showObs ? "▲ Hide raw observation" : "▼ Show raw observation"}
        </button>
        {showObs && (
          <div style={{ marginTop: 8 }}>
            <ObservationPanel observation={step.observation} />
          </div>
        )}
      </div>
    </div>
  );
}
