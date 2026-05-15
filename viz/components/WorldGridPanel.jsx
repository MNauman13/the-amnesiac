"use client";

const CELL = 48;

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

const OBJ_FULL_LABELS = {
  key:      "Key",
  fragment: "Fragment",
  token:    "Token",
  relic:    "Relic",
  lever:    "Lever",
  box:      "Box",
};

function agentArrowPoints(cx, cy, size = 13) {
  return {
    NORTH: `${cx},${cy - size} ${cx - size * 0.65},${cy + size * 0.55} ${cx + size * 0.65},${cy + size * 0.55}`,
    SOUTH: `${cx},${cy + size} ${cx - size * 0.65},${cy - size * 0.55} ${cx + size * 0.65},${cy - size * 0.55}`,
    EAST:  `${cx + size},${cy} ${cx - size * 0.55},${cy - size * 0.65} ${cx - size * 0.55},${cy + size * 0.65}`,
    WEST:  `${cx - size},${cy} ${cx + size * 0.55},${cy - size * 0.65} ${cx + size * 0.55},${cy + size * 0.65}`,
  };
}

/* Truncate object ID to a readable short label */
function shortId(id) {
  // e.g. FRAGMENT_A -> FRAG_A, KEY_BLUE -> KEY_B, TOKEN_1 -> TOK_1
  const parts = id.split("_");
  if (parts.length === 1) return id.slice(0, 6);
  return parts[0].slice(0, 4) + "_" + parts.slice(1).join("_").slice(0, 3);
}

export default function WorldGridPanel({ worldState }) {
  if (!worldState) {
    return (
      <div style={{
        background: "#0d1117", border: "1px solid #1e293b", borderRadius: 10,
        padding: 32, minWidth: 220, color: "#334155", fontSize: 13, textAlign: "center",
      }}>
        <div style={{ marginBottom: 8, fontSize: 24 }}>🗺</div>
        Grid view not available.
        <div style={{ fontSize: 11, marginTop: 6, color: "#1e293b" }}>
          Regenerate logs to enable
        </div>
      </div>
    );
  }

  const { room_name, width, height, grid, agent, objects, doors, inventory, zone } = worldState;

  /* Leave margin for axis labels */
  const MARGIN = 22;
  const svgW = width  * CELL + MARGIN;
  const svgH = height * CELL + MARGIN;
  const gx = MARGIN; /* grid x offset */
  const gy = MARGIN; /* grid y offset */

  const doorMap = {};
  doors.forEach((d) => { doorMap[`${d.x},${d.y}`] = d; });
  const objMap = {};
  objects.forEach((o) => { objMap[`${o.x},${o.y}`] = o; });

  return (
    <div style={{
      background: "#0d1117", border: "1px solid #1e293b", borderRadius: 10, padding: 16,
      display: "inline-flex", flexDirection: "column", gap: 12,
    }}>
      {/* ── Header ── */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16 }}>
        <div>
          <span style={{ fontSize: 16, fontWeight: 700, color: "#7dd3fc" }}>{room_name}</span>
          <span style={{ fontSize: 11, color: "#475569", marginLeft: 8 }}>{width} × {height} grid</span>
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <span style={{ fontSize: 12, color: "#64748b" }}>
            pos <span style={{ color: "#e2e8f0", fontWeight: 600 }}>({agent.x}, {agent.y})</span>
          </span>
          <span style={{
            fontSize: 12, fontWeight: 700, color: "#7dd3fc",
            background: "#0c1a2e", border: "1px solid #1e3a5f",
            padding: "2px 8px", borderRadius: 4,
          }}>
            {agent.facing}
          </span>
        </div>
      </div>

      {/* ── Grid SVG ── */}
      <svg
        width={svgW}
        height={svgH}
        style={{ display: "block", borderRadius: 6, border: "1px solid #1a2535" }}
      >
        {/* Background */}
        <rect width={svgW} height={svgH} fill="#070b10" />

        {/* Column labels (x axis) */}
        {Array.from({ length: width }, (_, x) => (
          <text
            key={`xl-${x}`}
            x={gx + x * CELL + CELL / 2}
            y={14}
            textAnchor="middle"
            fontSize={10}
            fill="#334155"
            fontFamily="monospace"
          >
            {x}
          </text>
        ))}

        {/* Row labels (y axis) */}
        {Array.from({ length: height }, (_, y) => (
          <text
            key={`yl-${y}`}
            x={10}
            y={gy + y * CELL + CELL / 2 + 4}
            textAnchor="middle"
            fontSize={10}
            fill="#334155"
            fontFamily="monospace"
          >
            {y}
          </text>
        ))}

        {/* Cells */}
        {grid.map((row, y) =>
          row.map((cell, x) => {
            const isWall  = cell === "wall";
            const isAgent = agent.x === x && agent.y === y;
            const door    = doorMap[`${x},${y}`];
            const obj     = objMap[`${x},${y}`];
            const isZone  = zone && zone.x === x && zone.y === y;
            const cx = gx + x * CELL + CELL / 2;
            const cy = gy + y * CELL + CELL / 2;

            return (
              <g key={`${x}-${y}`}>
                {/* Base cell */}
                <rect
                  x={gx + x * CELL} y={gy + y * CELL}
                  width={CELL} height={CELL}
                  fill={isWall ? "#0a0d14" : "#111827"}
                  stroke="#0d1117"
                  strokeWidth={1}
                />

                {/* Wall — cross-hatch texture */}
                {isWall && (
                  <>
                    <rect
                      x={gx + x * CELL + 1} y={gy + y * CELL + 1}
                      width={CELL - 2} height={CELL - 2}
                      fill="#080b11"
                    />
                    <line x1={gx + x * CELL + 5}        y1={gy + y * CELL + 5}
                          x2={gx + x * CELL + CELL - 5} y2={gy + y * CELL + CELL - 5}
                          stroke="#161d28" strokeWidth={1.5} />
                    <line x1={gx + x * CELL + CELL - 5} y1={gy + y * CELL + 5}
                          x2={gx + x * CELL + 5}        y2={gy + y * CELL + CELL - 5}
                          stroke="#161d28" strokeWidth={1.5} />
                    {/* Subtle "W" hint */}
                    <text x={cx} y={cy + 4} textAnchor="middle" fontSize={9}
                          fill="#1e2a38" fontFamily="monospace" fontWeight="bold">W</text>
                  </>
                )}

                {/* Zone — dashed gold highlight */}
                {isZone && !isAgent && (
                  <>
                    <rect
                      x={gx + x * CELL + 3} y={gy + y * CELL + 3}
                      width={CELL - 6} height={CELL - 6}
                      fill="#1f1900"
                      stroke="#eab308"
                      strokeWidth={2}
                      strokeDasharray="5,3"
                      rx={3}
                    />
                    <text x={cx} y={cy + 4} textAnchor="middle" fontSize={10}
                          fill="#ca8a04" fontFamily="monospace" fontWeight="bold">ZONE</text>
                  </>
                )}

                {/* Door */}
                {door && !isAgent && (
                  <>
                    <rect
                      x={gx + x * CELL + 2} y={gy + y * CELL + 2}
                      width={CELL - 4} height={CELL - 4}
                      fill={door.locked ? "#200808" : "#081a0e"}
                      stroke={door.locked ? "#dc2626" : "#16a34a"}
                      strokeWidth={2}
                      rx={4}
                    />

                    {door.locked ? (
                      /* Padlock icon — scaled up */
                      <>
                        <rect x={cx - 6} y={cy - 1} width={12} height={10}
                              fill="#dc2626" rx={2} />
                        <path d={`M${cx - 4.5} ${cy - 1} L${cx - 4.5} ${cy - 7}
                                  Q${cx} ${cy - 12} ${cx + 4.5} ${cy - 7} L${cx + 4.5} ${cy - 1}`}
                              fill="none" stroke="#dc2626" strokeWidth={2.5} strokeLinecap="round" />
                        <text x={cx} y={gy + y * CELL + CELL - 6}
                              textAnchor="middle" fontSize={8}
                              fill="#fca5a5" fontFamily="monospace">LOCKED</text>
                      </>
                    ) : (
                      /* Open door — arrow + label */
                      <>
                        <polygon points={`${cx + 9},${cy} ${cx - 3},${cy - 7} ${cx - 3},${cy + 7}`}
                                 fill="#16a34a" />
                        <text x={cx} y={gy + y * CELL + CELL - 6}
                              textAnchor="middle" fontSize={8}
                              fill="#86efac" fontFamily="monospace">OPEN</text>
                      </>
                    )}

                    {/* Destination room label — top of cell */}
                    <text
                      x={cx} y={gy + y * CELL + 13}
                      textAnchor="middle"
                      fontSize={8}
                      fill={door.locked ? "#f87171" : "#4ade80"}
                      fontFamily="monospace"
                      fontWeight="bold"
                    >
                      {door.to_room_name.length > 10
                        ? door.to_room_name.split(" ").map(w => w[0]).join("")
                        : door.to_room_name}
                    </text>
                  </>
                )}

                {/* Object (not under agent) */}
                {obj && !isAgent && (
                  <>
                    <circle
                      cx={cx} cy={cy - 4}
                      r={13}
                      fill={OBJ_COLORS[obj.type] || "#94a3b8"}
                      opacity={0.9}
                    />
                    <text
                      x={cx} y={cy - 3}
                      textAnchor="middle" dominantBaseline="middle"
                      fontSize={12} fontWeight="bold"
                      fill="#000"
                      fontFamily="monospace"
                    >
                      {OBJ_LABELS[obj.type] || "?"}
                    </text>
                    {/* Object short-ID label */}
                    <text
                      x={cx} y={gy + y * CELL + CELL - 4}
                      textAnchor="middle"
                      fontSize={7}
                      fill={OBJ_COLORS[obj.type] || "#94a3b8"}
                      fontFamily="monospace"
                      opacity={0.9}
                    >
                      {shortId(obj.id)}
                    </text>
                  </>
                )}

                {/* Agent */}
                {isAgent && (
                  <>
                    {/* Outer glow */}
                    <circle cx={cx} cy={cy} r={20} fill="#1d4ed8" opacity={0.18} />
                    {/* Body */}
                    <circle cx={cx} cy={cy} r={15} fill="#1d4ed8" />
                    {/* Direction arrow */}
                    <polygon
                      points={agentArrowPoints(cx, cy, 10)[agent.facing] || agentArrowPoints(cx, cy, 10).NORTH}
                      fill="#bfdbfe"
                    />
                    {/* "YOU" label */}
                    <text x={cx} y={gy + y * CELL + CELL - 4}
                          textAnchor="middle" fontSize={8}
                          fill="#93c5fd" fontFamily="monospace" fontWeight="bold">YOU</text>
                    {/* Object indicator if on same cell */}
                    {obj && (
                      <>
                        <circle cx={cx + 13} cy={cy - 13} r={7}
                                fill={OBJ_COLORS[obj.type] || "#94a3b8"}
                                stroke="#0d1117" strokeWidth={1.5} />
                        <text x={cx + 13} y={cy - 12}
                              textAnchor="middle" dominantBaseline="middle"
                              fontSize={7} fontWeight="bold" fill="#000" fontFamily="monospace">
                          {OBJ_LABELS[obj.type] || "?"}
                        </text>
                      </>
                    )}
                  </>
                )}
              </g>
            );
          })
        )}
      </svg>

      {/* ── Inventory bar ── */}
      {inventory.length > 0 && (
        <div style={{
          padding: "8px 12px", background: "#0a1a0a",
          border: "1px solid #14532d", borderRadius: 6,
          fontSize: 12, display: "flex", alignItems: "center", gap: 8,
        }}>
          <span style={{ color: "#475569", fontFamily: "monospace" }}>Carrying:</span>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {inventory.map((id) => (
              <span key={id} style={{
                color: "#22c55e", background: "#0d2b0d",
                padding: "2px 9px", borderRadius: 10, fontSize: 11,
                border: "1px solid #166534", fontFamily: "monospace",
              }}>
                {id}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* ── Legend ── */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
        <LegendItem color="#1d4ed8" label="Agent (YOU)" circle />
        <LegendItem color="#111827" border="#334155" label="Floor" />
        <LegendItem color="#0a0d14" border="#1e293b" label="Wall" hatch />
        <LegendItem color="#200808" border="#dc2626" label="Locked door" />
        <LegendItem color="#081a0e" border="#16a34a" label="Open door" />
        {zone && <LegendItem color="#1f1900" border="#eab308" label="Assembly zone" dashed />}
        {[...new Set(objects.map((o) => o.type))].map((type) => (
          <LegendItem key={type} color={OBJ_COLORS[type] || "#94a3b8"}
                      label={OBJ_FULL_LABELS[type] || type} circle />
        ))}
      </div>
    </div>
  );
}

function LegendItem({ color, border, label, circle, dashed, hatch }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
      {circle ? (
        <svg width={14} height={14}>
          <circle cx={7} cy={7} r={6} fill={color} />
        </svg>
      ) : (
        <div style={{
          width: 14, height: 14,
          background: color,
          border: `2px ${dashed ? "dashed" : "solid"} ${border || color}`,
          borderRadius: 2,
        }} />
      )}
      <span style={{ fontSize: 11, color: "#64748b" }}>{label}</span>
    </div>
  );
}
