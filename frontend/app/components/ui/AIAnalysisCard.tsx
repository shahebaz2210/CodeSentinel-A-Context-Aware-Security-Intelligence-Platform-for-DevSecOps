"use client";
import { ReactNode } from "react";

/**
 * T-128: AIAnalysisCard — container for all AI-generated content.
 * - accent-ai border at 24% opacity
 * - soft glow when loaded
 * - breathing border animation when loading
 * - error state drops glow
 * Matches DesignDoc.md §4.5
 * T-163: h3 aria-label="AI-generated analysis"
 */

interface AIAnalysisCardProps {
  title?: string;
  loading?: boolean;
  error?: boolean;
  onRetry?: () => void;
  children: ReactNode;
  id?: string;
}

export default function AIAnalysisCard({
  title,
  loading = false,
  error = false,
  onRetry,
  children,
  id,
}: AIAnalysisCardProps) {
  return (
    <div
      id={id}
      style={{
        padding: "16px 20px",
        borderRadius: 10,
        border: `1px solid ${error ? "rgba(255,59,59,0.3)" : "rgba(92,155,255,0.24)"}`,
        background: error
          ? "rgba(255,59,59,0.04)"
          : loading
          ? "rgba(92,155,255,0.03)"
          : "rgba(92,155,255,0.06)",
        boxShadow: error
          ? "none"
          : loading
          ? "none"
          : "0 0 16px rgba(92,155,255,0.08)",
        animation: loading ? "border-breathe 2s ease-in-out infinite" : "none",
        transition: "box-shadow 0.3s ease, border-color 0.3s ease",
      }}
    >
      {/* T-163: Real h3 with aria-label — never a decorative div */}
      {title && (
        <h3
          aria-label="AI-generated analysis"
          style={{
            margin: "0 0 12px 0",
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            color: error ? "var(--cs-critical)" : "#5c9bff",
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <span style={{ fontSize: 10 }}>✦</span>
          {title}
          <span
            style={{
              marginLeft: 4,
              padding: "1px 6px",
              background: "rgba(92,155,255,0.1)",
              border: "1px solid rgba(92,155,255,0.2)",
              borderRadius: 20,
              fontSize: 9,
              letterSpacing: "0.06em",
            }}
          >
            AI
          </span>
        </h3>
      )}

      {loading && (
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          {[0.2, 0.4, 0.6, 0.8, 1.0].map((opacity, i) => (
            <div
              key={i}
              style={{
                height: 8,
                flex: 1,
                borderRadius: 4,
                background: `rgba(92,155,255,${opacity})`,
                animation: `pulse-glow ${1 + i * 0.2}s ease-in-out infinite`,
              }}
            />
          ))}
        </div>
      )}

      {error ? (
        <div style={{ color: "var(--cs-critical)", fontSize: 13 }}>
          <span>Failed to load AI analysis.</span>
          {onRetry && (
            <button
              onClick={onRetry}
              style={{
                marginLeft: 8,
                background: "none",
                border: "none",
                color: "var(--cs-accent)",
                cursor: "pointer",
                fontSize: 12,
                fontWeight: 600,
                padding: 0,
                textDecoration: "underline",
              }}
            >
              Retry
            </button>
          )}
        </div>
      ) : (
        !loading && children
      )}
    </div>
  );
}
