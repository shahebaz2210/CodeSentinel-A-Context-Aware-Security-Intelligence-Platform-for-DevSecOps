"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { fetchGitHubRepos, connectRepo, fetchLatestScan, GitHubRepo } from "../lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [repos, setRepos] = useState<GitHubRepo[]>([]);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState<{ login: string; avatar_url?: string } | null>(null);
  const [connecting, setConnecting] = useState<number | null>(null);
  const [connectedRepos, setConnectedRepos] = useState<Set<number>>(new Set());
  const [search, setSearch] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("github_token");
    if (!token) { router.push("/"); return; }
    const userStr = localStorage.getItem("github_user");
    if (userStr) setUser(JSON.parse(userStr));

    fetchGitHubRepos()
      .then(setRepos)
      .catch(() => router.push("/"))
      .finally(() => setLoading(false));
  }, [router]);

  async function handleConnect(repo: GitHubRepo) {
    setConnecting(repo.github_id);
    try {
      const result = await connectRepo({
        github_id: repo.github_id,
        name: repo.name,
        full_name: repo.full_name,
        clone_url: repo.clone_url,
        default_branch: repo.default_branch,
        owner_login: repo.owner,
        is_private: repo.private,
      });
      setConnectedRepos((prev) => new Set([...prev, repo.github_id]));
      router.push(`/dashboard/repos/${result.id}`);
    } catch (e) {
      alert("Failed to connect repository");
    } finally {
      setConnecting(null);
    }
  }

  const filtered = repos.filter(
    (r) =>
      !search ||
      r.full_name.toLowerCase().includes(search.toLowerCase()) ||
      r.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", background: "var(--cs-bg)" }}>
      {/* Header */}
      <header
        style={{
          padding: "14px 24px",
          borderBottom: "1px solid var(--cs-border)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "var(--cs-bg-card)",
          position: "sticky",
          top: 0,
          zIndex: 50,
        }}
      >
        <Link href="/dashboard" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none" }}>
          <span style={{ fontSize: 22 }}>🛡️</span>
          <span style={{ fontWeight: 700, fontSize: 15, color: "var(--cs-text)" }}>CodeSentinel</span>
        </Link>
        {user && (
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            {user.avatar_url && (
              <img src={user.avatar_url} alt={user.login} style={{ width: 28, height: 28, borderRadius: "50%", border: "1px solid var(--cs-border)" }} />
            )}
            <span style={{ fontSize: 13, color: "var(--cs-text-muted)" }}>{user.login}</span>
          </div>
        )}
      </header>

      <main style={{ flex: 1, padding: "32px 24px", maxWidth: 900, margin: "0 auto", width: "100%" }}>
        <div style={{ marginBottom: 28 }}>
          <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 6 }}>Your Repositories</h1>
          <p style={{ color: "var(--cs-text-muted)", fontSize: 13 }}>
            Select a repository to connect and run a security scan.
          </p>
        </div>

        {/* Search */}
        <input
          id="repo-search"
          type="text"
          placeholder="Search repositories..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="cs-input"
          style={{ marginBottom: 20, maxWidth: 400 }}
        />

        {loading ? (
          <div style={{ display: "grid", gap: 12 }}>
            {[...Array(5)].map((_, i) => (
              <div key={i} className="glass-card" style={{ height: 70, opacity: 0.4 + i * 0.1 }} />
            ))}
          </div>
        ) : (
          <div style={{ display: "grid", gap: 10 }}>
            {filtered.map((repo) => (
              <div
                key={repo.github_id}
                className="glass-card glass-card-hover animate-fade-in"
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "16px 20px",
                  gap: 16,
                }}
              >
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, fontSize: 14, color: "var(--cs-text)" }}>
                      {repo.full_name}
                    </span>
                    {repo.private && (
                      <span className="badge badge-info" style={{ fontSize: 10, padding: "1px 6px" }}>Private</span>
                    )}
                    {repo.language && (
                      <span style={{ fontSize: 11, color: "var(--cs-text-muted)", background: "var(--cs-bg)", padding: "2px 8px", borderRadius: 4, border: "1px solid var(--cs-border)" }}>
                        {repo.language}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 11, color: "var(--cs-text-dim)" }}>
                    {repo.default_branch} · Updated {repo.updated_at ? new Date(repo.updated_at).toLocaleDateString() : "recently"}
                  </div>
                </div>
                <button
                  id={`connect-repo-${repo.github_id}`}
                  onClick={() => handleConnect(repo)}
                  disabled={connecting === repo.github_id || connectedRepos.has(repo.github_id)}
                  className="btn-primary"
                  style={{
                    fontSize: 13,
                    padding: "8px 16px",
                    opacity: connecting !== null && connecting !== repo.github_id ? 0.5 : 1,
                    pointerEvents: connecting !== null ? "none" : "auto",
                  }}
                >
                  {connecting === repo.github_id ? (
                    <span className="animate-spin" style={{ display: "inline-block", width: 14, height: 14, border: "2px solid rgba(0,0,0,0.3)", borderTopColor: "#000", borderRadius: "50%" }} />
                  ) : connectedRepos.has(repo.github_id) ? "✓ Connected" : "Connect"}
                </button>
              </div>
            ))}
            {filtered.length === 0 && (
              <div style={{ textAlign: "center", padding: 60, color: "var(--cs-text-muted)" }}>
                No repositories match your search.
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
