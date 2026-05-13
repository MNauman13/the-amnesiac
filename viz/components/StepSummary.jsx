"use client";

export default function StepSummary({ step }) {
  const action = step.action || "WAIT";
  const ok = step.action_result?.success;
  const tokens = step.tokens || {};
  const parseErr = step.parse_error;
  const latency = step.latency_ms ? `${Math.round(step.latency_ms)}ms` : "—";

  return (
    <div style={{
      marginTop: 12, padding: "10px 16px",
      background: "#1e293b", border: "1px solid #334155", borderRadius: 8,
      display: "flex", flexWrap: "wrap", gap: 20, fontSize: 12,
    }}>
      <Cell label="Action">
        <span style={{ color: ok ? "#34d399" : "#f87171", fontWeight: 600 }}>
          {action} {ok ? "✓" : "✗"}
        </span>
      </Cell>

      {step.action_result?.message && (
        <Cell label="Result">
          <span style={{ color: "#94a3b8" }}>{step.action_result.message}</span>
        </Cell>
      )}

      {parseErr && (
        <Cell label="Parse Error">
          <span style={{ color: "#f87171" }}>{parseErr}</span>
        </Cell>
      )}

      <Cell label="Tokens">
        <span style={{ color: "#7dd3fc" }}>
          {tokens.input ?? "?"}↑ / {tokens.output ?? "?"}↓
        </span>
      </Cell>

      <Cell label="Latency">
        <span style={{ color: "#a78bfa" }}>{latency}</span>
      </Cell>

      <Cell label="Goal Progress">
        <span style={{ color: step.goal_complete ? "#22c55e" : "#f59e0b" }}>
          {Math.round((step.goal_progress ?? 0) * 100)}%
          {step.goal_complete ? " (COMPLETE)" : ""}
        </span>
      </Cell>
    </div>
  );
}

function Cell({ label, children }) {
  return (
    <div>
      <div style={{ color: "#475569", fontSize: 10, marginBottom: 2, textTransform: "uppercase" }}>
        {label}
      </div>
      {children}
    </div>
  );
}
