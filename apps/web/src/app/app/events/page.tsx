"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

type EventRow = {
  id: string;
  event_id: string;
  op: string;
  status: string;
  lsn: string | null;
  idempotency_key: string;
  created_at: string;
};

export default function EventsPage() {
  const router = useRouter();
  const [email, setEmail] = useState<string>();
  const [rows, setRows] = useState<EventRow[]>([]);
  const [msg, setMsg] = useState<string | null>(null);

  async function load() {
    const res = await api<EventRow[]>("/api/events?limit=100");
    if (res.success) setRows(res.data);
  }

  useEffect(() => {
    (async () => {
      const me = await api<{ email: string }>("/api/auth/me");
      if (!me.success) {
        router.replace("/login");
        return;
      }
      setEmail(me.data.email);
      await load();
    })();
  }, [router]);

  async function replay(eventId: string) {
    const res = await api(`/api/events/${eventId}/replay`, { method: "POST" });
    setMsg(res.success ? `Replayed ${eventId}` : res.error.message);
    await load();
  }

  return (
    <AppShell userEmail={email}>
      <h1 className="font-display text-3xl font-semibold text-slate-ink">Events</h1>
      <p className="mt-1 text-slate-mist">Captured and applied change events.</p>
      {msg ? <p className="mt-3 text-sm text-river-700">{msg}</p> : null}
      <div className="mt-6 overflow-x-auto rounded-xl border border-slate-line bg-white/80">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="bg-slate-soft/80 text-slate-mist">
            <tr>
              <th className="px-4 py-3 font-medium">Time</th>
              <th className="px-4 py-3 font-medium">Op</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">LSN</th>
              <th className="px-4 py-3 font-medium">Idempotency</th>
              <th className="px-4 py-3 font-medium" />
            </tr>
          </thead>
          <tbody>
            {rows.map((e) => (
              <tr key={e.id} className="border-t border-slate-line/70">
                <td className="px-4 py-3 text-xs text-slate-mist">
                  {new Date(e.created_at).toLocaleString()}
                </td>
                <td className="px-4 py-3 font-mono uppercase">{e.op}</td>
                <td className="px-4 py-3">{e.status}</td>
                <td className="px-4 py-3 font-mono text-xs">{e.lsn || "—"}</td>
                <td className="max-w-[220px] truncate px-4 py-3 font-mono text-xs" title={e.idempotency_key}>
                  {e.idempotency_key}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    type="button"
                    onClick={() => replay(e.event_id)}
                    className="text-sm font-medium text-river-700 hover:underline"
                  >
                    Replay
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
