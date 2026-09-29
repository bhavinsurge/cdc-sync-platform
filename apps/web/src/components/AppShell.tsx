"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { api, setToken } from "@/lib/api";

const links = [
  { href: "/app", label: "Overview" },
  { href: "/app/pipelines", label: "Pipelines" },
  { href: "/app/events", label: "Events" },
  { href: "/app/dlq", label: "DLQ" },
];

export function AppShell({
  children,
  userEmail,
}: {
  children: React.ReactNode;
  userEmail?: string;
}) {
  const pathname = usePathname();
  const router = useRouter();

  async function logout() {
    await api("/api/auth/logout", { method: "POST" });
    setToken(null);
    router.push("/login");
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-line/80 bg-white/70 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-4">
          <Link href="/app" className="group flex items-baseline gap-2">
            <span className="font-display text-2xl font-semibold tracking-tight text-slate-ink">
              River<span className="text-river-600">CDC</span>
            </span>
            <span className="hidden text-xs font-medium uppercase tracking-[0.18em] text-slate-mist sm:inline">
              sync platform
            </span>
          </Link>
          <nav className="flex flex-wrap items-center gap-1">
            {links.map((l) => {
              const active = pathname === l.href;
              return (
                <Link
                  key={l.href}
                  href={l.href}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
                    active
                      ? "bg-river-50 text-river-700"
                      : "text-slate-mist hover:bg-slate-soft hover:text-slate-ink"
                  }`}
                >
                  {l.label}
                </Link>
              );
            })}
          </nav>
          <div className="flex items-center gap-3 text-sm">
            {userEmail ? (
              <span className="hidden text-slate-mist md:inline">{userEmail}</span>
            ) : null}
            <button
              type="button"
              onClick={logout}
              className="rounded-md border border-slate-line px-3 py-1.5 text-slate-ink transition hover:border-river-400 hover:text-river-700"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
    </div>
  );
}
