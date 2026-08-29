"use client";

/**
 * T-129: ValidateFixStepper — 4-step patch validation flow.
 * Statuses: idle | applying | testing | rescanning | pass | fail
 * Matches DesignDoc.md §4.6
 */

export type ValidateStatus = "idle" | "applying" | "testing" | "rescanning" | "pass" | "fail";

interface ValidateFixStepperProps {
  status: ValidateStatus;
  reason?: string;
}

const STEPS = [
  { id: "applying",   label: "Apply Patch",    icon: "📝" },
  { id: "testing",    label: "Run Tests",       icon: "🧪" },
  { id: "rescanning", label: "Re-scan",         icon: "🔬" },
  { id: "result",     label: "Result",          icon: "📋" },
];

function stepState(stepId: string, status: ValidateStatus): "pending" | "active" | "done" | "failed" {
  const order = ["applying", "testing", "rescanning", "result"];
  const currentIdx = order.indexOf(
    status === "pass" || status === "fail" ? "result" : status === "idle" ? "" : status
  );
  const stepIdx = order.indexOf(stepId);

  if (status === "idle") return "pending";
  if (status === "fail" && stepId === "result") return "failed";
  if (status === "pass" && stepId === "result") return "done";
  if (stepIdx < currentIdx) return "done";
  if (stepIdx === currentIdx) return "active";
  return "pending";
}

export default function ValidateFixStepper({ status, reason }: ValidateFixStepperProps) {
  if (status === "idle") return null;

  return (
    <div
      style={{
        padding: "16px",
        background: "var(--cs-bg)",
        border: "1px solid var(--cs-border)",
        borderRadius: 10,
        marginTop: 12,
      }}
      className="animate-fade-in"
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        {STEPS.map((step, i) => {
          const state = stepState(step.id, status);
          const color = state === "done" ? "var(--cs-accent)" :
                        state === "failed" ? "var(--cs-critical)" :
                        state === "active" ? "#5c9bff" : "var(--cs-text-dim)";
          return (
            <div key={step.id} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 6, position: "relative" }}>
              {/* Connector line */}
              {i < STEPS.length - 1 && (
                <div style={{
                  position: "absolute",
                  top: 14,
                  left: "50%",
                  right: "-50%",
                  height: 2,
                  background: state === "done" ? "var(--cs-accent)" : "var(--cs-border)",
                  transition: "background 0.3s ease",
                  zIndex: 0,
                }} />
              )}
              {/* Step node */}
              <div style={{
                width: 28,
                height: 28,
                borderRadius: "50%",
                border: `2px solid ${color}`,
                background: state === "done" ? "var(--cs-accent)" :
                            state === "failed" ? "var(--cs-critical)" :
                            state === "active" ? "rgba(92,155,255,0.15)" : "var(--cs-bg)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 12,
                position: "relative",
                zIndex: 1,
                animation: state === "active" ? "pulse-glow 1.5s infinite" : "none",
                transition: "all 0.25s ease",
              }}>
                {state === "done" ? "✓" :
                 state === "failed" ? "✕" :
                 state === "active" ? (
                   <span className="animate-spin" style={{ width: 12, height: 12, border: "2px solid rgba(92,155,255,0.3)", borderTopColor: "#5c9bff", borderRadius: "50%", display: "inline-block" }} />
                 ) : "·"}
              </div>
              <span style={{ fontSize: 9, fontWeight: 700, letterSpacing: "0.04em", color, textTransform: "uppercase", textAlign: "center" }}>
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      {/* Status message */}
      <div style={{ textAlign: "center", fontSize: 12 }}>
        {status === "applying" && <span style={{ color: "#5c9bff" }}>Applying patch to sandbox...</span>}
        {status === "testing" && <span style={{ color: "#5c9bff" }}>Running test suite in sandbox...</span>}
        {status === "rescanning" && <span style={{ color: "#5c9bff" }}>Re-scanning for vulnerability...</span>}
        {status === "pass" && (
          <span style={{ color: "var(--cs-accent)", fontWeight: 600 }}>
            ✓ Validated — patch passes tests and eliminates the vulnerability
          </span>
        )}
        {status === "fail" && (
          <span style={{ color: "var(--cs-critical)", fontWeight: 600 }}>
            ✕ Validation failed {reason ? `— ${reason}` : ""}
          </span>
        )}
      </div>
    </div>
  );
}
