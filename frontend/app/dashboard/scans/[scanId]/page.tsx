"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { fetchScan, fetchScanFindings, createScan, ScanStatus as ScanStatusType, FindingSummary } from "../../../lib/api";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#ff3b3b", high: "#ff7b00", medium: "#f5c518", low: "#4caf50", info: "#5c9bff",
};
const SEVERITY_ORDER: Record<string, number> = {
  critical: 0, high: 1, medium: 2, low: 3, info: 4,
};

function ScoreRing({ score }: { score: number | null }) {
  const s = score ?? 0;
  const color = s >= 80 ? "#4caf50" : s >= 50 ? "#f5c518" : "#ff3b3b";
  const r = 44;
  const circumference = 2 * Math.PI * r;
  const offset = circumference * (1 - s / 100);

  return (
    <div style={{ position: "relative", display: "inline-flex", alignItems: "center", justifyContent: "center" }}>
      <svg width={110} height={110} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={55} cy={55} r={r} fill="none" stroke="var(--cs-border)" strokeWidth={7} />
        <circle
          cx={55} cy={55} r={r} fill="none"
          stroke={color} strokeWidth={7}
          strokeDasharray={`${circumference}`}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
      </svg>
      <div style={{ position: "absolute", textAlign: "center" }}>
        <div style={{ fontSize: 22, fontWeight: 800, color: color }}>{score !== null ? Math.round(score) : "—"}</div>
        <div style={{ fontSize: 10, color: "var(--cs-text-muted)", letterSpacing: "0.05em" }}>SCORE</div>
      </div>
    </div>
  );
}

function GatePill({ gate }: { gate: string | null }) {
  if (!gate) return null;
  const map: Record<string, { label: string; icon: string; cls: string }> = {
    pass: { label: "PASS", icon: "✓", cls: "gate-pass" },
    warning: { label: "WARNING", icon: "⚠", cls: "gate-warning" },
    block: { label: "BLOCK", icon: "✗", cls: "gate-block" },
  };
  const info = map[gate] || map.pass;
  return (
    <span className={`badge ${info.cls}`} style={{ fontSize: 13, padding: "6px 16px", borderRadius: 8 }}>
      {info.icon} {info.label}
    </span>
  );
}

export default function ScanDetailPage() {
  const { scanId } = useParams<{ scanId: string }>();
  const router = useRouter();
  const [scan, setScan] = useState<ScanStatusType | null>(null);
  const [findings, setFindings] = useState<FindingSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [polling, setPolling] = useState(false);
  const [filterSeverity, setFilterSeverity] = useState<string | null>(null);
  const [filterTool, setFilterTool] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"severity" | "risk_score">("severity");

  const load = useCallback(async () => {
    try {
      const s = await fetchScan(scanId);
      setScan(s);
      if (s.status === "completed" || s.status === "failed") {
        if (s.status === "completed") {
          const f = await fetchScanFindings(scanId);
          setFindings(f);
        }
        setPolling(false);
        setLoading(false);
      } else {
        setPolling(true);
      }
    } catch {
      setLoading(false);
    }
  }, [scanId]);

  useEffect(() => {
    load();
  }, [load]);

  // Polling while running/pending
  useEffect(() => {
    if (!polling) return;
    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
  }, [polling, load]);

  const displayedFindings = [...findings]
    .filter((f) => !filterSeverity || f.severity === filterSeverity)
    .filter((f) => !filterTool || f.tool === filterTool)
    .sort((a, b) => {
      if (sortBy === "risk_score") return (b.risk_score ?? 0) - (a.risk_score ?? 0);
      return (SEVERITY_ORDER[a.severity] ?? 99) - (SEVERITY_ORDER[b.severity] ?? 99);
    });

  const severityCounts = findings.reduce<Record<string, number>>((acc, f) => {
    acc[f.severity] = (acc[f.severity] || 0) + 1;
    return acc;
  }, {});

  const isRunning = scan?.status === "pending" || scan?.status === "running";

  return (
    <div style={{ minHeight: "100vh", background: "var(--cs-bg)" }}>
      {/* Header */}
      <header style={{ padding: "14px 24px", borderBottom: "1px solid var(--cs-border)", display: "flex", alignItems: "center", justifyContent: "space-between", background: "var(--cs-bg-card)", position: "sticky", top: 0, zIndex: 50 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <Link href="/dashboard" style={{ textDecoration: "none", color: "var(--cs-text-muted)", fontSize: 13 }}>← Dashboard</Link>
          <span style={{ color: "var(--cs-border)" }}>|</span>
          <span style={{ fontSize: 22 }}>🛡️</span>
          <span style={{ fontWeight: 700, fontSize: 15, color: "var(--cs-text)" }}>CodeSentinel</span>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          {scan?.status === "completed" && (
            <button id="re-scan-btn" onClick={() => {
              if (scan?.repository_id) createScan(scan.repository_id).then((r) => router.push(`/dashboard/scans/${r.scan_id}`));
            }} className="btn-secondary" style={{ fontSize: 12 }}>
              ↻ Re-scan
            </button>
          )}
        </div>
      </header>

      <main style={{ maxWidth: 1100, margin: "0 auto", padding: "28px 24px" }}>
        {/* Scan status bar */}
        {isRunning && (
          <div className="glass-card animate-fade-in" style={{ padding: "20px 24px", marginBottom: 24, display: "flex", alignItems: "center", gap: 14, borderColor: "rgba(0,212,170,0.3)" }}>
            <div className="animate-spin" style={{ width: 20, height: 20, border: "3px solid var(--cs-border)", borderTopColor: "var(--cs-accent)", borderRadius: "50%" }} />
            <div>
              <div style={{ fontWeight: 600, marginBottom: 2 }}>
                {scan?.status === "pending" ? "Scan queued..." : "Security analysis running..."}
              </div>
              <div style={{ fontSize: 12, color: "var(--cs-text-muted)" }}>
                Running all 5 agents: Repository Analysis → Detection → Intelligence → Risk → Remediation
              </div>
            </div>
          </div>
        )}

        {/* Score + gate row */}
        {scan?.status === "completed" && (
          <div className="animate-fade-in" style={{ display: "grid", gridTemplateColumns: "auto 1fr auto", gap: 24, alignItems: "center", marginBottom: 28, padding: "24px", background: "var(--cs-bg-card)", border: "1px solid var(--cs-border)", borderRadius: 14 }}>
            <ScoreRing score={scan.security_score} />
            <div>
              <div style={{ fontSize: 13, color: "var(--cs-text-muted)", marginBottom: 8 }}>
                Security score — computed deterministically from weighted risk factors
              </div>
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                {Object.entries(severityCounts).sort(([a], [b]) => SEVERITY_ORDER[a] - SEVERITY_ORDER[b]).map(([sev, count]) => (
                  <button key={sev} id={`filter-${sev}`} onClick={() => setFilterSeverity(filterSeverity === sev ? null : sev)}
                    style={{ display: "flex", alignItems: "center", gap: 5, padding: "4px 10px", borderRadius: 6, border: "1px solid", borderColor: filterSeverity === sev ? SEVERITY_COLORS[sev] : "var(--cs-border)", background: filterSeverity === sev ? `${SEVERITY_COLORS[sev]}22` : "transparent", cursor: "pointer", transition: "all 0.15s", color: SEVERITY_COLORS[sev], fontSize: 12, fontWeight: 600 }}>
                    <span>{count}</span>
                    <span style={{ textTransform: "uppercase", fontSize: 10 }}>{sev}</span>
                  </button>
                ))}
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8 }}>
              <GatePill gate={scan.gate_result} />
              <span className="deterministic-badge">⚙ Deterministic</span>
            </div>
          </div>
        )}

        {scan?.status === "failed" && (
          <div className="glass-card" style={{ padding: 24, marginBottom: 24, borderColor: "rgba(255,59,59,0.3)" }}>
            <div style={{ fontWeight: 600, color: "var(--cs-critical)", marginBottom: 6 }}>❌ Scan failed</div>
            <div style={{ fontSize: 13, color: "var(--cs-text-muted)", fontFamily: "monospace" }}>{scan.error_message}</div>
          </div>
        )}

        {/* Findings table */}
        {findings.length > 0 && (
          <div className="animate-fade-in">
            {/* Controls */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14, gap: 12, flexWrap: "wrap" }}>
              <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>
                Findings <span style={{ color: "var(--cs-text-muted)", fontWeight: 400, fontSize: 13 }}>({displayedFindings.length} shown)</span>
              </h2>
              <div style={{ display: "flex", gap: 8 }}>
                {["semgrep", "gitleaks", "trivy"].map((tool) => (
                  <button key={tool} onClick={() => setFilterTool(filterTool === tool ? null : tool)}
                    style={{ padding: "5px 12px", borderRadius: 6, border: "1px solid var(--cs-border)", background: filterTool === tool ? "var(--cs-accent-dim)" : "transparent", color: filterTool === tool ? "var(--cs-accent)" : "var(--cs-text-muted)", cursor: "pointer", fontSize: 11, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.04em" }}>
                    {tool}
                  </button>
                ))}
                <select value={sortBy} onChange={(e) => setSortBy(e.target.value as any)}
                  style={{ padding: "5px 10px", borderRadius: 6, border: "1px solid var(--cs-border)", background: "var(--cs-bg-card)", color: "var(--cs-text-muted)", fontSize: 11, cursor: "pointer" }}>
                  <option value="severity">Sort: Severity</option>
                  <option value="risk_score">Sort: Risk Score</option>
                </select>
              </div>
            </div>

            {/* Table header */}
            <div style={{ display: "grid", gridTemplateColumns: "80px 1fr 100px 70px 80px", gap: 12, padding: "8px 16px", borderBottom: "1px solid var(--cs-border)", fontSize: 10, fontWeight: 700, letterSpacing: "0.08em", color: "var(--cs-text-dim)", textTransform: "uppercase" }}>
              <span>Severity</span><span>Finding</span><span>Tool</span><span>Risk</span><span>History</span>
            </div>

            {/* Finding rows */}
            {displayedFindings.map((f, i) => (
              <Link key={f.id} href={`/dashboard/findings/${f.id}`} style={{ textDecoration: "none" }}>
                <div id={`finding-row-${f.id}`}
                  className="findings-row"
                  style={{ gridTemplateColumns: "80px 1fr 100px 70px 80px", animationDelay: `${i * 0.03}s` }}>
                  <span className={`badge badge-${f.severity}`}>{f.severity}</span>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: 13, color: "var(--cs-text)", marginBottom: 2, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {f.finding_type.replace(/_/g, " ")}
                    </div>
                    <div style={{ fontSize: 11, color: "var(--cs-text-muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {f.file_path}{f.line_start ? `:${f.line_start}` : ""}
                    </div>
                  </div>
                  <span style={{ fontSize: 11, color: "var(--cs-text-muted)", textTransform: "uppercase", fontWeight: 600 }}>{f.tool}</span>
                  <span style={{ fontSize: 13, fontWeight: 700, color: f.risk_score !== null ? (f.risk_score >= 80 ? "#ff3b3b" : f.risk_score >= 50 ? "#f5c518" : "#4caf50") : "var(--cs-text-dim)" }}>
                    {f.risk_score !== null ? Math.round(f.risk_score) : "—"}
                  </span>
                  <span style={{ fontSize: 11, textTransform: "capitalize", color: f.history_status === "new" ? "var(--cs-accent)" : f.history_status === "recurring" ? "var(--cs-high)" : "var(--cs-text-muted)" }}>
                    {f.history_status ?? "—"}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}

        {scan?.status === "completed" && findings.length === 0 && (
          <div style={{ textAlign: "center", padding: "60px 20px" }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🎉</div>
            <h3 style={{ fontWeight: 700, marginBottom: 8 }}>No security issues found</h3>
            <p style={{ color: "var(--cs-text-muted)", fontSize: 13 }}>All configured security checks passed.</p>
          </div>
        )}
      </main>
    </div>
  );
}
