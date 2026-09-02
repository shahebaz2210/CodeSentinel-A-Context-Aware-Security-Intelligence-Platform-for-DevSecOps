"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

export default function AuthCallback() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [status, setStatus] = useState<"loading" | "success" | "error">(
    "loading"
  );

  const handleCallback = useCallback(async () => {
    const token =
      searchParams.get("token") || searchParams.get("access_token");
    const error = searchParams.get("error");

    if (error) {
      setStatus("error");
      return;
    }

    // The backend /auth/github/callback returns token in JSON response
    // For OAuth redirect flow, the backend redirects with token as query param
    if (token) {
      localStorage.setItem("github_token", token);
      setStatus("success");

      setTimeout(() => router.push("/dashboard"), 1000);
      return;
    }

    // Try reading from API response if code is in URL
    const code = searchParams.get("code");

    if (code) {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/auth/github/callback?code=${code}&state=${searchParams.get("state") || ""}`
        );

        const data = await res.json();

        if (data.access_token) {
          localStorage.setItem("github_token", data.access_token);

          if (data.github_user) {
            localStorage.setItem(
              "github_user",
              JSON.stringify(data.github_user)
            );
          }

          setStatus("success");

          setTimeout(() => router.push("/dashboard"), 800);
        } else {
          setStatus("error");
        }
      } catch {
        setStatus("error");
      }

      return;
    }

    setStatus("error");
  }, [searchParams, router]);

  useEffect(() => {
    const timer = setTimeout(() => {
      handleCallback();
    }, 0);

    return () => clearTimeout(timer);
  }, [handleCallback]);

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--cs-bg)",
      }}
    >
      <div
        className="glass-card animate-fade-in"
        style={{
          padding: 48,
          textAlign: "center",
          maxWidth: 400,
        }}
      >
        {status === "loading" && (
          <>
            <div
              style={{
                width: 40,
                height: 40,
                border: "3px solid var(--cs-border)",
                borderTopColor: "var(--cs-accent)",
                borderRadius: "50%",
                margin: "0 auto 20px",
              }}
              className="animate-spin"
            />

            <h2
              style={{
                color: "var(--cs-text)",
                marginBottom: 8,
              }}
            >
              Connecting to GitHub...
            </h2>

            <p
              style={{
                color: "var(--cs-text-muted)",
                fontSize: 13,
              }}
            >
              Exchanging OAuth credentials
            </p>
          </>
        )}

        {status === "success" && (
          <>
            <div
              style={{
                fontSize: 40,
                marginBottom: 16,
              }}
            >
              ✅
            </div>

            <h2
              style={{
                color: "var(--cs-text)",
                marginBottom: 8,
              }}
            >
              Connected!
            </h2>

            <p
              style={{
                color: "var(--cs-text-muted)",
                fontSize: 13,
              }}
            >
              Redirecting to dashboard...
            </p>
          </>
        )}

        {status === "error" && (
          <>
            <div
              style={{
                fontSize: 40,
                marginBottom: 16,
              }}
            >
              ❌
            </div>

            <h2
              style={{
                color: "var(--cs-critical)",
                marginBottom: 8,
              }}
            >
              Connection failed
            </h2>

            <p
              style={{
                color: "var(--cs-text-muted)",
                fontSize: 13,
                marginBottom: 20,
              }}
            >
              Failed to authenticate with GitHub. Please try again.
            </p>

            <Link
              href="/"
              className="btn-primary"
              style={{
                display: "inline-flex",
              }}
            >
              Try Again
            </Link>
          </>
        )}
      </div>
    </main>
  );
}