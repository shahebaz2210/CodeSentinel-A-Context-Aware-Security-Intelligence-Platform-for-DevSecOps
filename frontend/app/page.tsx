"use client";
import Link from "next/link";
import { useState } from "react";

export default function LandingPage() {
  const [hovered, setHovered] = useState(false);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px 20px",
        background:
          "radial-gradient(ellipse 80% 60% at 50% 0%, rgba(0,212,170,0.06) 0%, transparent 70%), var(--cs-bg)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background grid */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
          pointerEvents: "none",
        }}
      />

      {/* Hero content */}
      <div
        style={{
          maxWidth: 680,
          width: "100%",
          textAlign: "center",
          position: "relative",
          zIndex: 1,
        }}
        className="animate-fade-in"
      >
        {/* Logo mark */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: 72,
            height: 72,
            borderRadius: 18,
            background: "linear-gradient(135deg, rgba(0,212,170,0.2), rgba(0,212,170,0.05))",
            border: "1px solid rgba(0,212,170,0.3)",
            marginBottom: 28,
            fontSize: 32,
          }}
        >
          🛡️
        </div>

        {/* Wordmark */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            background: "rgba(0,212,170,0.08)",
            border: "1px solid rgba(0,212,170,0.2)",
            borderRadius: 20,
            padding: "4px 14px",
            marginBottom: 24,
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: "0.08em",
            color: "var(--cs-accent)",
            textTransform: "uppercase",
          }}
        >
          ✦ AI-Powered DevSecOps
        </div>

        <h1
          style={{
            fontSize: "clamp(2.4rem, 5vw, 3.5rem)",
            fontWeight: 800,
            lineHeight: 1.1,
            marginBottom: 20,
            letterSpacing: "-0.03em",
          }}
        >
          <span className="gradient-text">CodeSentinel</span>
          <br />
          <span style={{ color: "var(--cs-text)" }}>Security Intelligence</span>
        </h1>

        <p
          style={{
            fontSize: 17,
            color: "var(--cs-text-muted)",
            lineHeight: 1.7,
            marginBottom: 40,
            maxWidth: 520,
            margin: "0 auto 40px",
          }}
        >
          Context-aware vulnerability detection, AI-grounded risk analysis, and
          deterministic security gates for your GitHub repositories.
        </p>

        {/* Feature pills */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 10,
            justifyContent: "center",
            marginBottom: 40,
          }}
        >
          {[
            "🔬 Semgrep · Gitleaks · Trivy",
            "🤖 RAG-Grounded AI Analysis",
            "⚖️ Deterministic Risk Engine",
            "🔒 PASS / WARNING / BLOCK Gate",
            "💊 Validated Patch Suggestions",
            "📊 Security Memory & Trends",
          ].map((f) => (
            <span
              key={f}
              style={{
                padding: "6px 14px",
                background: "var(--cs-bg-card)",
                border: "1px solid var(--cs-border)",
                borderRadius: 20,
                fontSize: 12,
                color: "var(--cs-text-muted)",
                fontWeight: 500,
              }}
            >
              {f}
            </span>
          ))}
        </div>

        {/* CTA */}
        <a
          id="github-connect-btn"
          href={`${apiUrl}/auth/github`}
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => setHovered(false)}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 12,
            padding: "14px 28px",
            background: "linear-gradient(135deg, #00d4aa, #009f80)",
            color: "#000",
            fontWeight: 700,
            fontSize: 15,
            borderRadius: 10,
            textDecoration: "none",
            transform: hovered ? "translateY(-2px)" : "translateY(0)",
            boxShadow: hovered
              ? "0 8px 30px rgba(0,212,170,0.35)"
              : "0 2px 10px rgba(0,212,170,0.2)",
            transition: "transform 0.2s ease, box-shadow 0.2s ease",
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
          </svg>
          Connect with GitHub
        </a>

        <p
          style={{
            marginTop: 16,
            fontSize: 12,
            color: "var(--cs-text-dim)",
          }}
        >
          Requires GitHub OAuth · Your code stays private · No data stored without consent
        </p>
      </div>

      {/* Architecture badge */}
      <div
        style={{
          position: "absolute",
          bottom: 32,
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          gap: 24,
          alignItems: "center",
          fontSize: 12,
          color: "var(--cs-text-dim)",
        }}
      >
        {["Agent 1: Context", "Agent 2: Detect", "Agent 3: Intel", "Agent 4: Risk", "Agent 5: Fix"].map(
          (a, i) => (
            <span key={a} style={{ display: "flex", alignItems: "center", gap: 6 }}>
              {a}
              {i < 4 && (
                <span style={{ color: "var(--cs-accent)", fontSize: 10 }}>→</span>
              )}
            </span>
          )
        )}
      </div>
    </main>
  );
}
