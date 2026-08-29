"use client";
import { ReactNode } from "react";

/**
 * T-124: SeverityTag — filled pill with signal color.
 * - 16% background opacity of signal color
 * - colored dot
 * - uppercase text label (NEVER color alone — T-164)
 * Matches DesignDoc.md §4.1
 */

type Severity = "critical" | "high" | "medium" | "low" | "info";

interface SeverityTagProps {
  severity: Severity;
  className?: string;
}

const SEVERITY_CONFIG: Record<Severity, { color: string; bg: string; label: string }> = {
  critical: { color: "#ff3b3b", bg: "rgba(255,59,59,0.16)",  label: "CRITICAL" },
  high:     { color: "#ff7b00", bg: "rgba(255,123,0,0.16)",  label: "HIGH"     },
  medium:   { color: "#f5c518", bg: "rgba(245,197,24,0.16)", label: "MEDIUM"   },
  low:      { color: "#4caf50", bg: "rgba(76,175,80,0.16)",  label: "LOW"      },
  info:     { color: "#5c9bff", bg: "rgba(92,155,255,0.16)", label: "INFO"     },
};

export default function SeverityTag({ severity, className }: SeverityTagProps) {
  const config = SEVERITY_CONFIG[severity] ?? SEVERITY_CONFIG.info;

  return (
    <span
      className={className}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 5,
        padding: "3px 9px",
        borderRadius: 6,
        background: config.bg,
        border: `1px solid ${config.color}44`,
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: "0.06em",
        color: config.color,
        whiteSpace: "nowrap",
      }}
    >
      {/* T-164: Colored dot + text — never color alone */}
      <span
        aria-hidden="true"
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: config.color,
          flexShrink: 0,
        }}
      />
      {/* T-164: Text label MUST be present */}
      {config.label}
    </span>
  );
}


/**
 * T-125: GateBadge — flat filled badge.
 * - correct signal color, icon, and text
 * - sharp radius-sm edges, no glow, no hover state (T-125)
 * - NEVER icon alone — always icon + text (T-165)
 * Matches DesignDoc.md §4.2
 */

type GateResult = "pass" | "warning" | "block" | "loading";

interface GateBadgeProps {
  result: GateResult;
}

const GATE_CONFIG: Record<GateResult, { color: string; bg: string; border: string; icon: string; label: string }> = {
  pass:    { color: "#4caf50", bg: "rgba(76,175,80,0.12)",   border: "rgba(76,175,80,0.3)",   icon: "✓", label: "PASS"    },
  warning: { color: "#f5c518", bg: "rgba(245,197,24,0.12)",  border: "rgba(245,197,24,0.3)",  icon: "△", label: "WARNING" },
  block:   { color: "#ff3b3b", bg: "rgba(255,59,59,0.12)",   border: "rgba(255,59,59,0.3)",   icon: "⛔", label: "BLOCK"  },
  loading: { color: "#7d8590", bg: "rgba(125,133,144,0.12)", border: "rgba(125,133,144,0.3)", icon: "…", label: "SCANNING"},
};

export function GateBadge({ result }: GateBadgeProps) {
  const config = GATE_CONFIG[result] ?? GATE_CONFIG.loading;

  return (
    <span
      role="status"
      aria-label={`Gate result: ${config.label}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "5px 12px",
        borderRadius: 6,         // radius-sm: 6px
        background: config.bg,
        border: `1px solid ${config.border}`,
        color: config.color,
        fontSize: 12,
        fontWeight: 700,
        letterSpacing: "0.06em",
        whiteSpace: "nowrap",
      }}
    >
      {/* T-165: NEVER icon alone — always icon + text */}
      <span aria-hidden="true">{config.icon}</span>
      {config.label}
    </span>
  );
}


/**
 * T-130: SecurityScoreRing — circular SVG ring.
 * - colored by score band (≥80 green, ≥50 yellow, <50 red)
 * - mono numeral center
 * - no glow, static when loaded
 * Matches DesignDoc.md §4.7
 */

interface SecurityScoreRingProps {
  score: number | null;
  loading?: boolean;
  size?: number;
}

export function SecurityScoreRing({ score, loading = false, size = 110 }: SecurityScoreRingProps) {
  const r = (size / 2) - 8;
  const circumference = 2 * Math.PI * r;
  const s = score ?? 0;
  const offset = loading ? 0 : circumference * (1 - s / 100);
  const color = s >= 80 ? "#4caf50" : s >= 50 ? "#f5c518" : "#ff3b3b";

  return (
    <div
      role="img"
      aria-label={`Security score: ${score !== null ? Math.round(score) : "loading"} out of 100`}
      style={{ position: "relative", display: "inline-flex", alignItems: "center", justifyContent: "center" }}
    >
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none" stroke="var(--cs-border)" strokeWidth={7}
        />
        <circle
          cx={size / 2} cy={size / 2} r={r}
          fill="none"
          stroke={loading ? "var(--cs-border)" : color}
          strokeWidth={7}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.8s ease, stroke 0.3s ease" }}
        />
      </svg>
      <div
        aria-hidden="true"
        style={{
          position: "absolute",
          textAlign: "center",
          fontFamily: "'IBM Plex Mono', monospace",
        }}
      >
        <div style={{ fontSize: size * 0.2, fontWeight: 800, color: loading ? "var(--cs-text-dim)" : color }}>
          {loading ? "…" : score !== null ? Math.round(score) : "—"}
        </div>
        <div style={{ fontSize: size * 0.09, color: "var(--cs-text-muted)", letterSpacing: "0.05em" }}>
          SCORE
        </div>
      </div>
    </div>
  );
}


/**
 * T-131: Button — primary, secondary, destructive variants.
 * Matches DesignDoc.md §4.9
 */

interface ButtonProps {
  variant?: "primary" | "secondary" | "destructive";
  loading?: boolean;
  disabled?: boolean;
  onClick?: () => void;
  children: ReactNode;
  id?: string;
  type?: "button" | "submit" | "reset";
}

export function Button({
  variant = "primary",
  loading = false,
  disabled = false,
  onClick,
  children,
  id,
  type = "button",
}: ButtonProps) {
  const isDisabled = disabled || loading;

  const styles: Record<string, React.CSSProperties> = {
    primary: {
      background: "linear-gradient(135deg, #00d4aa, #009f80)",
      color: "#000",
      border: "none",
    },
    secondary: {
      background: "var(--cs-bg-card)",
      color: "var(--cs-text)",
      border: "1px solid var(--cs-border)",
    },
    destructive: {
      background: "rgba(255,59,59,0.12)",
      color: "var(--cs-critical)",
      border: "1px solid rgba(255,59,59,0.3)",
    },
  };

  return (
    <button
      id={id}
      type={type}
      onClick={onClick}
      disabled={isDisabled}
      style={{
        ...styles[variant],
        display: "inline-flex",
        alignItems: "center",
        gap: 8,
        padding: "9px 18px",
        borderRadius: 8,
        fontSize: 13,
        fontWeight: 600,
        fontFamily: "inherit",
        cursor: isDisabled ? "not-allowed" : "pointer",
        opacity: isDisabled ? 0.5 : 1,
        transition: "transform 0.15s ease, opacity 0.15s ease",
        outline: "none",
        // T-161: visible focus ring
      }}
      onFocus={(e) => {
        (e.currentTarget as HTMLElement).style.boxShadow = "0 0 0 2px var(--cs-border-focus, var(--cs-accent))";
      }}
      onBlur={(e) => {
        (e.currentTarget as HTMLElement).style.boxShadow = "none";
      }}
    >
      {loading && (
        <span
          className="animate-spin"
          aria-hidden="true"
          style={{ width: 13, height: 13, border: "2px solid rgba(0,0,0,0.3)", borderTopColor: "currentColor", borderRadius: "50%", display: "inline-block" }}
        />
      )}
      {children}
    </button>
  );
}


/**
 * T-132: Toast — slide-up + fade animation.
 * 200ms in / 160ms out
 */

interface ToastProps {
  message: string;
  type?: "success" | "error" | "info";
  visible: boolean;
}

export function Toast({ message, type = "info", visible }: ToastProps) {
  const colors = {
    success: { bg: "rgba(76,175,80,0.15)", border: "rgba(76,175,80,0.3)", icon: "✓" },
    error:   { bg: "rgba(255,59,59,0.15)", border: "rgba(255,59,59,0.3)", icon: "✕" },
    info:    { bg: "rgba(92,155,255,0.12)", border: "rgba(92,155,255,0.25)", icon: "ℹ" },
  };
  const c = colors[type];

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        position: "fixed",
        bottom: 24,
        right: 24,
        padding: "12px 18px",
        background: "var(--cs-bg-card)",
        border: `1px solid ${c.border}`,
        borderLeft: `3px solid ${c.border}`,
        borderRadius: 10,
        display: "flex",
        alignItems: "center",
        gap: 10,
        fontSize: 13,
        color: "var(--cs-text)",
        boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
        zIndex: 9999,
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(12px)",
        transition: visible
          ? "opacity 200ms ease, transform 200ms ease"
          : "opacity 160ms ease, transform 160ms ease",
        pointerEvents: visible ? "auto" : "none",
      }}
    >
      <span style={{ fontSize: 16 }}>{c.icon}</span>
      {message}
    </div>
  );
}
