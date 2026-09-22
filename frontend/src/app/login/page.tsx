"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@rivercdc.local");
  const [password, setPassword] = useState("Password123!");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const res = await api<{ access_token: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setLoading(false);
    if (!res.success) {
      setError(res.error.message);
      return;
    }
    setToken(res.data.access_token);
    router.push("/app");
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center px-6">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 overflow-hidden"
      >
        <div className="absolute -left-24 top-16 h-72 w-72 rounded-full bg-river-400/20 blur-3xl" />
        <div className="absolute -right-16 bottom-10 h-80 w-80 rounded-full bg-river-600/15 blur-3xl" />
      </div>
      <div className="relative w-full max-w-md">
        <div className="mb-8 text-center">
          <p className="font-display text-4xl font-semibold tracking-tight text-slate-ink">
            River<span className="text-river-600">CDC</span>
          </p>
          <p className="mt-2 text-slate-mist">
            Monitor capture pipelines, lag, and dead-letter recovery.
          </p>
        </div>
        <form
          onSubmit={onSubmit}
          className="rounded-2xl border border-slate-line bg-white/80 p-6 shadow-[0_20px_60px_-40px_rgba(15,23,42,0.45)] backdrop-blur"
        >
          <label className="block text-sm font-medium text-slate-ink">
            Email
            <input
              className="mt-1.5 w-full rounded-lg border border-slate-line bg-white px-3 py-2 outline-none ring-river-400 focus:ring-2"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              type="email"
              required
            />
          </label>
          <label className="mt-4 block text-sm font-medium text-slate-ink">
            Password
            <input
              className="mt-1.5 w-full rounded-lg border border-slate-line bg-white px-3 py-2 outline-none ring-river-400 focus:ring-2"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              type="password"
              required
            />
          </label>
          {error ? (
            <p className="mt-3 text-sm text-red-600" role="alert">
              {error}
            </p>
          ) : null}
          <button
            type="submit"
            disabled={loading}
            className="mt-6 w-full rounded-lg bg-river-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-river-700 disabled:opacity-60"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-mist">
          Demo: admin@rivercdc.local / Password123!
        </p>
        <p className="mt-2 text-center text-sm">
          <Link href="/" className="text-river-700 hover:underline">
            Back to home
          </Link>
        </p>
      </div>
    </div>
  );
}
