"use client";

import { useState, useEffect } from "react";
import ScrollPanel from "./ScrollPanel";
import ObservationPanel from "./ObservationPanel";
import StepControls from "./StepControls";
import StepSummary from "./StepSummary";

export default function StepViewer({ steps }) {
  const [idx, setIdx] = useState(0);

  useEffect(() => { setIdx(0); }, [steps]);

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
