"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

type LagRow = {
  pipeline_id: string;
  pipeline_name: string;
  lag_ms: number;
  last_lsn: string | null;
  producer_status: string;
  consumer_status: string;
  last_event_at: string | null;
};

type User = { email: string; full_name: string; role: string };

export default function OverviewPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [lag, setLag] = useState<LagRow[]>([]);
  const [eventCount, setEventCount] = useState(0);
  const [dlqOpen, setDlqOpen] = useState(0);

  useEffect(() => {
    (async () => {
      const me = await api<User>("/api/auth/me");
      if (!me.success) {
        router.replace("/login");
        return;
      }
      setUser(me.data);
      const [lagRes, eventsRes, dlqRes] = await Promise.all([
        api<LagRow[]>("/api/sync/lag"),
        api<unknown[]>("/api/events?limit=50"),
        api<{ status: string }[]>("/api/dlq?status=open"),
      ]);
      if (lagRes.success) setLag(lagRes.data);
      if (eventsRes.success) setEventCount(eventsRes.data.length);
      if (dlqRes.success) setDlqOpen(dlqRes.data.length);
    })();
  }, [router]);

  return (
    <AppShell userEmail={user?.email}>
      <div className="mb-8">
        <h1 className="font-display text-3xl font-semibold text-slate-ink">Overview</h1>
        <p className="mt-1 text-slate-mist">Pipeline health, lag, and recent capture activity.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Recent events" value={String(eventCount)} />
        <Stat label="Open DLQ" value={String(dlqOpen)} accent={dlqOpen > 0} />
        <Stat label="Pipelines tracked" value={String(lag.length)} />
      </div>

      <section className="mt-10">
        <h2 className="text-lg font-semibold text-slate-ink">Sync lag</h2>
        <div className="mt-3 overflow-hidden rounded-xl border border-slate-line bg-white/80">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-soft/80 text-slate-mist">
              <tr>
                <th className="px-4 py-3 font-medium">Pipeline</th>
                <th className="px-4 py-3 font-medium">Lag</th>
                <th className="px-4 py-3 font-medium">Producer</th>
                <th className="px-4 py-3 font-medium">Consumer</th>
                <th className="px-4 py-3 font-medium">Last LSN</th>
              </tr>
            </thead>
            <tbody>
              {lag.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-slate-mist">
                    No sync state yet — start the CDC producer/consumer.
                  </td>
                </tr>
              ) : (
                lag.map((row) => (
                  <tr key={row.pipeline_id} className="border-t border-slate-line/70">
                    <td className="px-4 py-3 font-medium text-slate-ink">{row.pipeline_name}</td>
                    <td className="px-4 py-3">{row.lag_ms} ms</td>
                    <td className="px-4 py-3">
                      <Pill ok={row.producer_status === "running"}>{row.producer_status}</Pill>
                    </td>
                    <td className="px-4 py-3">
                      <Pill ok={row.consumer_status === "running"}>{row.consumer_status}</Pill>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-mist">
                      {row.last_lsn || "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </AppShell>
  );
}

function Stat({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-line bg-white/80 px-5 py-4">
      <p className="text-xs font-medium uppercase tracking-wider text-slate-mist">{label}</p>
      <p
        className={`mt-2 font-display text-3xl font-semibold ${
          accent ? "text-amber-600" : "text-slate-ink"
        }`}
      >
        {value}
      </p>
    </div>
  );
}

function Pill({ children, ok }: { children: React.ReactNode; ok: boolean }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
        ok ? "bg-emerald-50 text-emerald-700" : "bg-slate-soft text-slate-mist"
      }`}
    >
      {children}
    </span>
  );
}
