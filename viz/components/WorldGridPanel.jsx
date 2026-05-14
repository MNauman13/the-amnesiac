"use client";

const CELL = 34;

const OBJ_COLORS = {
  key:      "#eab308",
  fragment: "#a855f7",
  token:    "#06b6d4",
  relic:    "#f97316",
  lever:    "#6366f1",
  box:      "#78716c",
};

const OBJ_LABELS = {
  key:      "K",
  fragment: "F",
  token:    "T",
  relic:    "R",
  lever:    "L",
  box:      "B",
};

function agentArrowPoints(cx, cy, size = 10) {
  return {
    NORTH: `${cx},${cy - size} ${cx - size * 0.65},${cy + size * 0.55} ${cx + size * 0.65},${cy + size * 0.55}`,
    SOUTH: `${cx},${cy + size} ${cx - size * 0.65},${cy - size * 0.55} ${cx + size * 0.65},${cy - size * 0.55}`,
    EAST:  `${cx + size},${cy} ${cx - size * 0.55},${cy - size * 0.65} ${cx - size * 0.55},${cy + size * 0.65}`,
    WEST:  `${cx - size},${cy} ${cx + size * 0.55},${cy - size * 0.65} ${cx + size * 0.55},${cy + size * 0.65}`,
  };
}

export default function WorldGridPanel({ worldState }) {
  if (!worldState) {
    return (
      <div style={{
        background: "#0d1117", border: "1px solid #1e293b", borderRadius: 10,
        padding: 24, minWidth: 200, color: "#334155", fontSize: 13, textAlign: "center",
      }}>
        <div style={{ marginBottom: 8, fontSize: 20 }}>🗺</div>
        Grid view not available.
        <div style={{ fontSize: 11, marginTop: 6, color: "#1e293b" }}>
          Regenerate logs to enable
        </div>
      </div>
    );
  }

  const { room_name, width, height, grid, agent, objects, doors, inventory, zone } = worldState;
  const svgW = width * CELL;
  const svgH = height * CELL;

  const doorMap = {};
  doors.forEach((d) => { doorMap[`${d.x},${d.y}`] = d; });
  const objMap = {};
  objects.forEach((o) => { objMap[`${o.x},${o.y}`] = o; });

  const arrows = agentArrowPoints(0, 0);

  return (
    <div style={{
      background: "#0d1117", border: "1px solid #1e293b", borderRadius: 10, padding: 16,
      display: "inline-flex", flexDirection: "column", gap: 12, minWidth: svgW + 32,
    }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <span style={{ fontSize: 15, fontWeight: 700, color: "#7dd3fc" }}>{room_name}</span>
          <span style={{ fontSize: 11, color: "#334155", marginLeft: 8 }}>{width} × {height}</span>
        </div>
        <div style={{ fontSize: 12, color: "#475569", display: "flex", gap: 10 }}>
          <span>
            pos <span style={{ color: "#e2e8f0" }}>({agent.x},{agent.y})</span>
          </span>
          <span style={{ color: "#93c5fd", fontWeight: 600 }}>{agent.facing}</span>
        </div>
      </div>

      {/* Grid */}
      <svg
        width={svgW}
        height={svgH}
        style={{ display: "block", borderRadius: 6, border: "1px solid #1a2535" }}
      >
        {/* Background */}
        <rect width={svgW} height={svgH} fill="#070b10" />

        {grid.map((row, y) =>
          row.map((cell, x) => {
            const isWall = cell === "wall";
            const isAgent = agent.x === x && agent.y === y;
            const door = doorMap[`${x},${y}`];
            const obj = objMap[`${x},${y}`];
            const isZone = zone && zone.x === x && zone.y === y;
            const cx = x * CELL + CELL / 2;
            const cy = y * CELL + CELL / 2;

            return (
              <g key={`${x}-${y}`}>
                {/* Base cell */}
                <rect
                  x={x * CELL} y={y * CELL}
                  width={CELL} height={CELL}
                  fill={isWall ? "#0a0d12" : "#111827"}
                  stroke="#0d1117"
                  strokeWidth={1}
                />

                {/* Wall shading */}
                {isWall && (
                  <>
                    <rect
                      x={x * CELL + 1} y={y * CELL + 1}
                      width={CELL - 2} height={CELL - 2}
                      fill="#080b10"
                    />
                    {/* Cross-hatch lines for walls */}
                    <line
                      x1={x * CELL + 4} y1={y * CELL + 4}
                      x2={x * CELL + CELL - 4} y2={y * CELL + CELL - 4}
                      stroke="#151a22" strokeWidth={1}
                    />
                    <line
                      x1={x * CELL + CELL - 4} y1={y * CELL + 4}
                      x2={x * CELL + 4} y2={y * CELL + CELL - 4}
                      stroke="#151a22" strokeWidth={1}
                    />
                  </>
                )}

                {/* Zone marker — dashed gold border */}
                {isZone && !isAgent && (
                  <rect
                    x={x * CELL + 3} y={y * CELL + 3}
                    width={CELL - 6} height={CELL - 6}
                    fill="#1a160a"
                    stroke="#eab308"
                    strokeWidth={1.5}
                    strokeDasharray="4,3"
                    rx={2}
                  />
                )}

                {/* Door */}
                {door && !isAgent && (
                  <>
                    <rect
                      x={x * CELL + 2} y={y * CELL + 2}
                      width={CELL - 4} height={CELL - 4}
                      fill={door.locked ? "#2a0a0a" : "#0a1f0f"}
                      stroke={door.locked ? "#dc2626" : "#16a34a"}
                      strokeWidth={1.5}
                      rx={3}
                    />
                    {/* Door symbol */}
                    {door.locked ? (
                      <>
                        {/* Lock body */}
                        <rect x={cx - 4} y={cy - 1} width={8} height={7} fill={door.locked ? "#dc2626" : "#16a34a"} rx={1} />
                        {/* Lock shackle */}
                        <path
                          d={`M${cx - 3} ${cy - 1} L${cx - 3} ${cy - 5} Q${cx} ${cy - 8} ${cx + 3} ${cy - 5} L${cx + 3} ${cy - 1}`}
                          fill="none" stroke="#dc2626" strokeWidth={2}
                        />
                      </>
                    ) : (
                      /* Open door arrow */
                      <polygon
                        points={`${cx + 6},${cy} ${cx - 2},${cy - 5} ${cx - 2},${cy + 5}`}
                        fill="#16a34a"
                      />
                    )}
                    {/* Room label */}
                    <text
                      x={cx} y={y * CELL + CELL - 5}
                      textAnchor="middle"
                      fontSize={7} fill={door.locked ? "#fca5a5" : "#86efac"}
                      fontFamily="monospace"
                    >
                      {door.to_room_name.split(" ").map(w => w[0]).join("")}
                    </text>
                  </>
                )}

                {/* Object (not under agent) */}
                {obj && !isAgent && (
                  <>
                    <circle
                      cx={cx} cy={cy - 2}
                      r={9}
                      fill={OBJ_COLORS[obj.type] || "#94a3b8"}
                      opacity={0.85}
                    />
                    <text
                      x={cx} y={cy - 1}
                      textAnchor="middle" dominantBaseline="middle"
                      fontSize={9} fontWeight="bold"
                      fill="#000"
                      fontFamily="monospace"
                    >
                      {OBJ_LABELS[obj.type] || "?"}
                    </text>
                    {/* Object ID label below */}
                    <text
                      x={cx} y={y * CELL + CELL - 3}
                      textAnchor="middle"
                      fontSize={6} fill={OBJ_COLORS[obj.type] || "#94a3b8"}
                      fontFamily="monospace" opacity={0.8}
                    >
                      {obj.id.replace(/_[A-Z0-9]+$/, m => m.length < 4 ? m : "")}
                    </text>
                  </>
                )}

                {/* Agent */}
                {isAgent && (
                  <>
                    {/* Agent glow */}
                    <circle cx={cx} cy={cy} r={14} fill="#1d4ed8" opacity={0.25} />
                    {/* Agent body */}
                    <circle cx={cx} cy={cy} r={11} fill="#1d4ed8" />
                    {/* Direction arrow */}
                    <polygon
                      points={agentArrowPoints(cx, cy, 8)[agent.facing] || agentArrowPoints(cx, cy, 8).NORTH}
                      fill="#7dd3fc"
                    />
                    {/* Object on same cell as agent */}
                    {obj && (
                      <circle cx={cx + 9} cy={cy - 9} r={5} fill={OBJ_COLORS[obj.type] || "#94a3b8"} />
                    )}
                  </>
                )}
              </g>
            );
          })
        )}
      </svg>

      {/* Inventory bar */}
      {inventory.length > 0 && (
        <div style={{
          padding: "6px 10px", background: "#0a1a0a",
          border: "1px solid #14532d", borderRadius: 6,
          fontSize: 12, display: "flex", alignItems: "center", gap: 8,
        }}>
          <span style={{ color: "#475569" }}>Carrying:</span>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {inventory.map((id) => (
              <span key={id} style={{
                color: "#22c55e", background: "#0d2b0d",
                padding: "1px 7px", borderRadius: 10, fontSize: 11,
                border: "1px solid #166534",
              }}>
                {id}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Legend */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
        <LegendItem color="#1d4ed8" label="Agent" circle />
        <LegendItem color="#111827" border="#334155" label="Floor" />
        <LegendItem color="#0a0d12" border="#1e293b" label="Wall" hatch />
        <LegendItem color="#2a0a0a" border="#dc2626" label="Locked door" />
        <LegendItem color="#0a1f0f" border="#16a34a" label="Open door" />
        {zone && <LegendItem color="#1a160a" border="#eab308" label="Zone" dashed />}
        {[...new Set(objects.map((o) => o.type))].map((type) => (
          <LegendItem key={type} color={OBJ_COLORS[type] || "#94a3b8"} label={type} circle />
        ))}
      </div>
    </div>
  );
}

function LegendItem({ color, border, label, circle, dashed, hatch }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
      {circle ? (
        <svg width={12} height={12}>
          <circle cx={6} cy={6} r={5} fill={color} />
        </svg>
      ) : (
        <div style={{
          width: 12, height: 12,
          background: color,
          border: `1.5px ${dashed ? "dashed" : "solid"} ${border || color}`,
          borderRadius: 2,
        }} />
      )}
      <span style={{ fontSize: 11, color: "#475569" }}>{label}</span>
    </div>
  );
}
