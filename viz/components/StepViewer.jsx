"use client";

import { useState, useEffect } from "react";
import ScrollPanel from "./ScrollPanel";
import ObservationPanel from "./ObservationPanel";
import StepControls from "./StepControls";
import StepSummary from "./StepSummary";

export default function StepViewer({ steps, autoPlay = false }) {
  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speedMs, setSpeedMs] = useState(1000);

  useEffect(() => {
    setIdx(0);
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

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 16 }}>
        <ObservationPanel observation={step.observation} />
        <ScrollPanel
          scrollBefore={step.scroll_before}
          scrollAfter={step.scroll_after}
          memoryWrite={step.memory_write}
        />
      </div>

      <StepSummary step={step} />
    </div>
  );
}
