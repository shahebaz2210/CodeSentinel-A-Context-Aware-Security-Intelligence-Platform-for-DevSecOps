"use client";
import { useEffect, useRef } from "react";

export type TraceStage = {
  id: string;
  label: string;
  status: "pending" | "active" | "complete" | "error";
};

interface ScanTraceProps {
  stages: TraceStage[];
}

/**
 * T-126: ScanTrace — 5-node pipeline progress visualization.
 * - pending: dim outline
 * - active: accent-ai fill + scale pulse glow + aria-live announcement
 * - complete: solid fill, static ring
 * - error: critical outline, no glow
 * Matches DesignDoc.md §4.3
 */
export default function ScanTrace({ stages }: ScanTraceProps) {
  const liveRef = useRef<HTMLDivElement>(null);

  // T-162: Announce active stage to screen readers
  useEffect(() => {
    const active = stages.find((s) => s.status === "active");
    if (active && liveRef.current) {
      liveRef.current.textContent = `${active.label} in progress`;
    }
    const complete = stages.filter((s) => s.status === "complete").at(-1);
    if (complete && liveRef.current) {
      liveRef.current.textContent = `${complete.label} complete`;
    }
  }, [stages]);

  const nodeColor = (status: TraceStage["status"]) => {
    switch (status) {
      case "complete": return "var(--cs-accent)";
      case "active":   return "var(--cs-accent)";
      case "error":    return "var(--cs-critical)";
      default:         return "var(--cs-border)";
    }
  };

  const completedCount = stages.filter((s) => s.status === "complete").length;

  return (
    <div style={{ width: "100%" }}>
      {/* T-162: aria-live region for agent stage announcements */}
      <div
        ref={liveRef}
        aria-live="polite"
        aria-atomic="true"
        style={{ position: "absolute", width: 1, height: 1, overflow: "hidden", clip: "rect(0,0,0,0)" }}
      />

      {/* Track line + nodes */}
      <div style={{ position: "relative", display: "flex", alignItems: "center" }}>
        {/* Background track */}
        <div style={{ position: "absolute", top: "50%", left: 0, right: 0, height: 2, background: "var(--cs-border)", transform: "translateY(-50%)", zIndex: 0 }} />
        {/* Progress fill */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: 0,
            height: 2,
            background: "linear-gradient(90deg, var(--cs-accent), #5c9bff)",
            transform: "translateY(-50%)",
            width: stages.length > 1
              ? `${(completedCount / (stages.length - 1)) * 100}%`
              : "0%",
            transition: "width 0.5s ease",
            zIndex: 1,
          }}
        />

        {/* Nodes */}
        <div style={{ display: "flex", justifyContent: "space-between", width: "100%", position: "relative", zIndex: 2 }}>
          {stages.map((stage, i) => (
            <div key={stage.id} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8, flex: i === 0 || i === stages.length - 1 ? "0 0 auto" : "1 1 auto" }}>
              {/* Node circle */}
              <div
                role="img"
                aria-label={`${stage.label}: ${stage.status}`}
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  border: `2px solid ${nodeColor(stage.status)}`,
                  background: stage.status === "complete" || stage.status === "active"
                    ? nodeColor(stage.status)
                    : "var(--cs-bg)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 13,
                  fontWeight: 700,
                  color: stage.status === "complete" || stage.status === "active" ? "#000" : "var(--cs-text-dim)",
                  animation: stage.status === "active" ? "pulse-glow 2s infinite" : "none",
                  transition: "all 0.3s ease",
                }}
              >
                {stage.status === "complete" ? "✓" :
                 stage.status === "error" ? "✕" :
                 stage.status === "active" ? i + 1 : i + 1}
              </div>
              {/* Label */}
              <span style={{
                fontSize: 10,
                fontWeight: 600,
                letterSpacing: "0.04em",
                textTransform: "uppercase",
                color: stage.status === "active" ? "var(--cs-accent)" :
                       stage.status === "complete" ? "var(--cs-text)" :
                       stage.status === "error" ? "var(--cs-critical)" : "var(--cs-text-dim)",
                textAlign: "center",
                maxWidth: 80,
                lineHeight: 1.3,
              }}>
                {stage.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
