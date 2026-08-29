"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { fetchLatestScan, fetchRepoScans, fetchRepoTrends, createScan, ScanStatus as ScanStatusType, ScanHistoryItem, TrendItem } from "../../../lib/api";
import AIAssistant from "../../../components/assistant/AIAssistant";

export default function RepoOverviewPage() {
  const { repoId } = useParams<{ repoId: string }>();
  const router = useRouter();
  const [latestScan, setLatestScan] = useState<ScanStatusType | null>(null);
  const [scans, setScans] = useState<ScanHistoryItem[]>([]);
  const [trends, setTrends] = useState<TrendItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [showAssistant, setShowAssistant] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [latest, history, trendData] = await Promise.all([
        fetchLatestScan(repoId),
        fetchRepoScans(repoId),
        fetchRepoTrends(repoId),
      ]);
      setLatestScan(latest);
      setScans(history.scans);
      setTrends(trendData);
    } finally {
      setLoading(false);
    }
  }, [repoId]);

  useEffect(() => { loadData(); }, [loadData]);

  async function handleScan() {
    setScanning(true);
    try {
      const result = await createScan(repoId);
      router.push(`/dashboard/scans/${result.scan_id}`);
    } finally {
      setScanning(false);
    }
  }

  const gateMap = { pass: { color: "#4caf50", icon: "✓" }, warning: { color: "#f5c518", icon: "⚠" }, block: { color: "#ff3b3b", icon: "✗" } };

  return (
    <div style={{ minHeight: "100vh", background: "var(--cs-bg)" }}>
      <header style={{ padding: "14px 24px", borderBottom: "1px solid var(--cs-border)", display: "flex", alignItems: "center", justifyContent: "space-between", background: "var(--cs-bg-card)", position: "sticky", top: 0, zIndex: 50 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <Link href="/dashboard" style={{ textDecoration: "none", color: "var(--cs-text-muted)", fontSize: 13 }}>← Dashboard</Link>
          <span style={{ color: "var(--cs-border)" }}>|</span>
          <span style={{ fontSize: 22 }}>🛡️</span>
          <span style={{ fontWeight: 700, fontSize: 15, color: "var(--cs-text)" }}>CodeSentinel</span>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button onClick={() => setShowAssistant(!showAssistant)} className="btn-secondary" style={{ fontSize: 12 }}>
            🤖 {showAssistant ? "Close" : "AI Assistant"}
          </button>
          <button id="run-scan-btn" onClick={handleScan} disabled={scanning} className="btn-primary" style={{ fontSize: 13 }}>
            {scanning ? "Starting scan..." : "▶ Run Security Scan"}
          </button>
        </div>
      </header>

      <div style={{ display: "flex", height: "calc(100vh - 57px)" }}>
        <main style={{ flex: 1, overflowY: "auto", padding: "28px 24px", maxWidth: showAssistant ? 700 : 1100 }}>
          {loading ? (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 200 }}>
              <div className="animate-spin" style={{ width: 32, height: 32, border: "3px solid var(--cs-border)", borderTopColor: "var(--cs-accent)", borderRadius: "50%" }} />
            </div>
          ) : (
            <>
              {/* Latest scan summary */}
              {latestScan ? (
                <div className="glass-card animate-fade-in" style={{ padding: "20px 24px", marginBottom: 24 }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <div>
                      <div style={{ fontSize: 11, color: "var(--cs-text-muted)", letterSpacing: "0.06em", textTransform: "uppercase", marginBottom: 8 }}>Latest Security Score</div>
                      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                        <span style={{ fontSize: 48, fontWeight: 800, color: latestScan.security_score !== null ? (latestScan.security_score >= 80 ? "#4caf50" : latestScan.security_score >= 50 ? "#f5c518" : "#ff3b3b") : "var(--cs-text-dim)" }}>
                          {latestScan.security_score !== null ? Math.round(latestScan.security_score) : "—"}
                        </span>
                        <span style={{ color: "var(--cs-text-muted)", fontSize: 14 }}>/100</span>
                      </div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      {latestScan.gate_result && (
                        <div style={{
                          display: "inline-flex", alignItems: "center", gap: 6, padding: "8px 16px",
                          borderRadius: 8, fontSize: 14, fontWeight: 700,
                          background: `${gateMap[latestScan.gate_result as keyof typeof gateMap]?.color}22`,
                          color: gateMap[latestScan.gate_result as keyof typeof gateMap]?.color,
                          border: `1px solid ${gateMap[latestScan.gate_result as keyof typeof gateMap]?.color}55`,
                        }}>
                          {gateMap[latestScan.gate_result as keyof typeof gateMap]?.icon} {latestScan.gate_result.toUpperCase()}
                        </div>
                      )}
                      <div style={{ fontSize: 11, color: "var(--cs-text-dim)", marginTop: 6 }}>
                        {latestScan.completed_at ? new Date(latestScan.completed_at).toLocaleDateString() : ""}
                      </div>
                      <Link href={`/dashboard/scans/${latestScan.scan_id}`} style={{ fontSize: 12, color: "var(--cs-accent)", textDecoration: "none", marginTop: 4, display: "inline-block" }}>
                        View full report →
                      </Link>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="glass-card animate-fade-in" style={{ padding: "40px 24px", marginBottom: 24, textAlign: "center" }}>
                  <div style={{ fontSize: 40, marginBottom: 16 }}>🔍</div>
                  <h3 style={{ fontWeight: 700, marginBottom: 8 }}>No scans yet</h3>
                  <p style={{ color: "var(--cs-text-muted)", fontSize: 13, marginBottom: 20 }}>Run your first security scan to get started.</p>
                  <button onClick={handleScan} disabled={scanning} className="btn-primary">
                    {scanning ? "Starting..." : "▶ Run First Scan"}
                  </button>
                </div>
              )}

              {/* Trend chart (simple bar visualization) */}
              {trends.length > 1 && (
                <div className="glass-card animate-fade-in" style={{ padding: "20px 24px", marginBottom: 24 }}>
                  <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>Security Score Trend</h3>
                  <div style={{ display: "flex", alignItems: "flex-end", gap: 8, height: 100 }}>
                    {trends.slice(-12).map((t, i) => {
                      const score = t.security_score ?? 0;
                      const color = score >= 80 ? "#4caf50" : score >= 50 ? "#f5c518" : "#ff3b3b";
                      return (
                        <div key={t.scan_id} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                          <div style={{ fontSize: 9, color: "var(--cs-text-dim)", fontWeight: 600 }}>{Math.round(score)}</div>
                          <div style={{ width: "100%", background: `${color}33`, borderRadius: 4, height: `${score}%`, minHeight: 4, border: `1px solid ${color}55`, transition: "height 0.5s ease", cursor: "pointer" }}
                            title={`${new Date(t.date).toLocaleDateString()}: ${Math.round(score)}/100`} />
                          <Link href={`/dashboard/scans/${t.scan_id}`} style={{ fontSize: 8, color: "var(--cs-text-dim)" }}>
                            {i + 1}
                          </Link>
                        </div>
                      );
                    })}
                  </div>
                  <div style={{ display: "flex", gap: 16, marginTop: 12, fontSize: 11, color: "var(--cs-text-muted)" }}>
                    <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      <span style={{ width: 8, height: 8, borderRadius: 2, background: "#4caf50", display: "inline-block" }} /> ≥80 Good
                    </span>
                    <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      <span style={{ width: 8, height: 8, borderRadius: 2, background: "#f5c518", display: "inline-block" }} /> ≥50 Warning
                    </span>
                    <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      <span style={{ width: 8, height: 8, borderRadius: 2, background: "#ff3b3b", display: "inline-block" }} /> &lt;50 Critical
                    </span>
                  </div>
                </div>
              )}

              {/* Scan history */}
              {scans.length > 0 && (
                <div className="glass-card animate-fade-in" style={{ overflow: "hidden" }}>
                  <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--cs-border)" }}>
                    <h3 style={{ fontSize: 14, fontWeight: 700, margin: 0 }}>Scan History</h3>
                  </div>
                  {scans.map((s, i) => (
                    <Link key={s.scan_id} href={`/dashboard/scans/${s.scan_id}`} style={{ textDecoration: "none" }}>
                      <div style={{
                        display: "grid", gridTemplateColumns: "1fr auto auto auto",
                        alignItems: "center", gap: 16, padding: "12px 20px",
                        borderBottom: i < scans.length - 1 ? "1px solid var(--cs-border)" : "none",
                        transition: "background 0.12s", cursor: "pointer",
                      }}
                        onMouseEnter={(e) => ((e.currentTarget as HTMLElement).style.background = "var(--cs-bg-hover)")}
                        onMouseLeave={(e) => ((e.currentTarget as HTMLElement).style.background = "transparent")}
                      >
                        <div>
                          <div style={{ fontSize: 12, fontWeight: 600, color: "var(--cs-text)", marginBottom: 2 }}>
                            {s.scan_type === "pr" ? "PR Scan" : "Repository Scan"}
                          </div>
                          <div style={{ fontSize: 11, color: "var(--cs-text-muted)" }}>
                            {new Date(s.started_at).toLocaleDateString()} at {new Date(s.started_at).toLocaleTimeString()}
                          </div>
                        </div>
                        <span style={{ fontSize: 11, color: "var(--cs-text-muted)", textTransform: "capitalize" }}>{s.status}</span>
                        <span style={{ fontSize: 14, fontWeight: 700, color: s.security_score !== null ? (s.security_score >= 80 ? "#4caf50" : s.security_score >= 50 ? "#f5c518" : "#ff3b3b") : "var(--cs-text-dim)" }}>
                          {s.security_score !== null ? Math.round(s.security_score) : "—"}
                        </span>
                        {s.gate_result && (
                          <span style={{ fontSize: 11, fontWeight: 700, color: gateMap[s.gate_result as keyof typeof gateMap]?.color }}>
                            {gateMap[s.gate_result as keyof typeof gateMap]?.icon} {s.gate_result.toUpperCase()}
                          </span>
                        )}
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </>
          )}
        </main>

        {/* AI Assistant sidebar */}
        {showAssistant && (
          <div style={{ width: 380, borderLeft: "1px solid var(--cs-border)", flexShrink: 0, overflow: "hidden" }}>
            <AIAssistant scanId={latestScan?.scan_id} />
          </div>
        )}
      </div>
    </div>
  );
}
