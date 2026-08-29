"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { fetchFinding, triggerValidation, FindingDetail } from "../../../lib/api";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#ff3b3b", high: "#ff7b00", medium: "#f5c518", low: "#4caf50", info: "#5c9bff",
};

function Section({ title, badge, children, id }: { title: string; badge?: React.ReactNode; children: React.ReactNode; id?: string }) {
  return (
    <div id={id} className="glass-card" style={{ padding: 20, marginBottom: 16 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
        <h3 style={{ margin: 0, fontSize: 13, fontWeight: 700, color: "var(--cs-text)" }}>{title}</h3>
        {badge}
      </div>
      {children}
    </div>
  );
}

export default function FindingDetailPage() {
  const { findingId } = useParams<{ findingId: string }>();
  const [finding, setFinding] = useState<FindingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [validating, setValidating] = useState(false);

  useEffect(() => {
    fetchFinding(findingId).then(setFinding).finally(() => setLoading(false));
  }, [findingId]);

  async function handleValidate() {
    setValidating(true);
    try {
      await triggerValidation(findingId);
      const updated = await fetchFinding(findingId);
      setFinding(updated);
    } finally {
      setValidating(false);
    }
  }

  if (loading) return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--cs-bg)" }}>
      <div className="animate-spin" style={{ width: 32, height: 32, border: "3px solid var(--cs-border)", borderTopColor: "var(--cs-accent)", borderRadius: "50%" }} />
    </div>
  );

  if (!finding) return <div style={{ padding: 40, color: "var(--cs-text-muted)" }}>Finding not found</div>;

  const severity = finding.severity;
  const sevColor = SEVERITY_COLORS[severity] || "#7d8590";

  return (
    <div style={{ minHeight: "100vh", background: "var(--cs-bg)" }}>
      <header style={{ padding: "14px 24px", borderBottom: "1px solid var(--cs-border)", display: "flex", alignItems: "center", gap: 14, background: "var(--cs-bg-card)", position: "sticky", top: 0, zIndex: 50 }}>
        <Link href={`/dashboard/scans/${finding.scan_id}`} style={{ textDecoration: "none", color: "var(--cs-text-muted)", fontSize: 13 }}>← Scan Results</Link>
        <span style={{ color: "var(--cs-border)" }}>|</span>
        <span style={{ fontSize: 22 }}>🛡️</span>
        <span style={{ fontWeight: 700, fontSize: 15, color: "var(--cs-text)" }}>CodeSentinel</span>
      </header>

      <main style={{ maxWidth: 900, margin: "0 auto", padding: "28px 24px" }}>
        {/* Finding header */}
        <div className="glass-card animate-fade-in" style={{ padding: "20px 24px", marginBottom: 20, borderLeft: `3px solid ${sevColor}` }}>
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16 }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
                <span className={`badge badge-${severity}`}>{severity}</span>
                <span style={{ fontSize: 11, color: "var(--cs-text-muted)", textTransform: "uppercase", fontWeight: 600 }}>{finding.tool}</span>
                {finding.history_status && (
                  <span style={{ fontSize: 11, color: finding.history_status === "new" ? "var(--cs-accent)" : "var(--cs-text-muted)", fontWeight: 600 }}>
                    ● {finding.history_status}
                  </span>
                )}
                {finding.is_true_positive === false && (
                  <span style={{ fontSize: 11, color: "var(--cs-text-muted)", background: "var(--cs-bg)", padding: "2px 8px", borderRadius: 4, border: "1px solid var(--cs-border)" }}>
                    Possible false positive
                  </span>
                )}
              </div>
              <h1 style={{ fontSize: 18, fontWeight: 700, marginBottom: 6 }}>
                {finding.finding_type.replace(/_/g, " ")}
              </h1>
              <div style={{ fontSize: 12, color: "var(--cs-text-muted)", fontFamily: "monospace" }}>
                {finding.file_path}{finding.line_start ? `:${finding.line_start}` : ""}
                {finding.line_end && finding.line_end !== finding.line_start ? `–${finding.line_end}` : ""}
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={{ fontSize: 28, fontWeight: 800, color: finding.risk_score !== null ? (finding.risk_score >= 80 ? "#ff3b3b" : finding.risk_score >= 50 ? "#f5c518" : "#4caf50") : "var(--cs-text-dim)" }}>
                {finding.risk_score !== null ? Math.round(finding.risk_score) : "—"}
              </div>
              <div style={{ fontSize: 10, color: "var(--cs-text-muted)", letterSpacing: "0.06em" }}>RISK SCORE</div>
              <span className="deterministic-badge" style={{ marginTop: 6, display: "inline-flex" }}>⚙ Deterministic</span>
            </div>
          </div>
        </div>

        {/* Code snippet */}
        {finding.code_snippet && (
          <Section id="code-section" title="Vulnerable Code">
            <pre className="code-block" style={{ margin: 0 }}>{finding.code_snippet}</pre>
          </Section>
        )}

        {/* AI Analysis */}
        {finding.ai_explanation && (
          <Section id="ai-analysis-section" title="AI Security Analysis" badge={<span className="ai-badge">✦ AI Generated</span>}>
            <p style={{ fontSize: 13, lineHeight: 1.7, color: "var(--cs-text-muted)", margin: 0 }}>{finding.ai_explanation}</p>
            {finding.root_cause && (
              <div style={{ marginTop: 12, padding: "12px 14px", background: "var(--cs-bg)", borderRadius: 8, borderLeft: "3px solid var(--cs-accent)" }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: "var(--cs-accent)", marginBottom: 4, letterSpacing: "0.08em" }}>ROOT CAUSE</div>
                <p style={{ fontSize: 13, color: "var(--cs-text-muted)", margin: 0 }}>{finding.root_cause}</p>
              </div>
            )}
            {finding.attack_scenario && (
              <div style={{ marginTop: 12, padding: "12px 14px", background: "rgba(255,59,59,0.05)", borderRadius: 8, borderLeft: "3px solid var(--cs-critical)" }}>
                <div style={{ fontSize: 10, fontWeight: 700, color: "var(--cs-critical)", marginBottom: 4, letterSpacing: "0.08em" }}>ATTACK SCENARIO</div>
                <p style={{ fontSize: 13, color: "var(--cs-text-muted)", margin: 0 }}>{finding.attack_scenario}</p>
              </div>
            )}
            {/* References */}
            {(finding.owasp_refs.length > 0 || finding.cwe_refs.length > 0) && (
              <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
                {finding.owasp_refs.map((ref) => (
                  <span key={ref} className="badge badge-info" style={{ fontSize: 10 }}>{ref}</span>
                ))}
                {finding.cwe_refs.map((ref) => (
                  <span key={ref} className="badge" style={{ fontSize: 10, background: "rgba(255,123,0,0.1)", color: "#ff7b00", border: "1px solid #ff7b00" }}>{ref}</span>
                ))}
              </div>
            )}
          </Section>
        )}

        {/* Remediation */}
        {finding.suggested_fix && (
          <Section id="remediation-section" title="Suggested Fix" badge={<span className="ai-badge">✦ AI Generated — Pending Validation</span>}>
            <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
              <span className={`badge ${
                finding.validation_status === "pass" ? "badge-low" :
                finding.validation_status === "fail" ? "badge-critical" :
                finding.validation_status === "pending" ? "badge-medium" : "badge-info"
              }`}>
                Validation: {finding.validation_status || "not_run"}
              </span>
              {finding.validation_status === "not_run" && (
                <button id="validate-patch-btn" onClick={handleValidate} disabled={validating} className="btn-secondary" style={{ fontSize: 12, padding: "5px 12px" }}>
                  {validating ? "Validating..." : "▶ Run Validation"}
                </button>
              )}
            </div>
            {finding.validation_status !== "pass" && (
              <div style={{ padding: "10px 14px", background: "rgba(245,197,24,0.08)", border: "1px solid rgba(245,197,24,0.2)", borderRadius: 8, marginBottom: 12, fontSize: 12, color: "#f5c518" }}>
                ⚠️ This suggestion is AI-generated and requires validation before use. Do not apply to production without review.
              </div>
            )}
            <pre className="code-block" style={{ margin: 0 }}>{finding.suggested_fix}</pre>
            {finding.fix_explanation && (
              <p style={{ fontSize: 13, color: "var(--cs-text-muted)", marginTop: 12, lineHeight: 1.6 }}>{finding.fix_explanation}</p>
            )}
          </Section>
        )}

        {/* Secure Coding Guidance */}
        {finding.secure_coding_guidance && (
          <Section id="guidance-section" title="Secure Coding Guidance" badge={<span className="ai-badge">✦ AI Generated</span>}>
            <p style={{ fontSize: 13, color: "var(--cs-text-muted)", lineHeight: 1.7, margin: 0 }}>{finding.secure_coding_guidance}</p>
          </Section>
        )}
      </main>
    </div>
  );
}
