"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

type DlqRow = {
  id: string;
  event_id: string;
  error: string;
  attempts: number;
  status: string;
  created_at: string;
};

export default function DlqPage() {
  const router = useRouter();
  const [email, setEmail] = useState<string>();
  const [rows, setRows] = useState<DlqRow[]>([]);
  const [msg, setMsg] = useState<string | null>(null);

  async function load() {
    const res = await api<DlqRow[]>("/api/dlq");
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

  async function replay(id: string) {
    const res = await api(`/api/dlq/${id}/replay`, { method: "POST" });
    setMsg(res.success ? `DLQ ${id} replayed` : res.error.message);
    await load();
  }

  async function discard(id: string) {
    const res = await api(`/api/dlq/${id}/discard`, { method: "POST" });
    setMsg(res.success ? `DLQ ${id} discarded` : res.error.message);
    await load();
  }

  return (
    <AppShell userEmail={email}>
      <h1 className="font-display text-3xl font-semibold text-slate-ink">Dead letter queue</h1>
      <p className="mt-1 text-slate-mist">Failed applies after exhausted retries.</p>
      {msg ? <p className="mt-3 text-sm text-river-700">{msg}</p> : null}
      <div className="mt-6 overflow-x-auto rounded-xl border border-slate-line bg-white/80">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead className="bg-slate-soft/80 text-slate-mist">
            <tr>
              <th className="px-4 py-3 font-medium">Time</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Attempts</th>
              <th className="px-4 py-3 font-medium">Error</th>
              <th className="px-4 py-3 font-medium" />
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-slate-mist">
                  No DLQ entries — good news.
                </td>
              </tr>
            ) : (
              rows.map((d) => (
                <tr key={d.id} className="border-t border-slate-line/70">
                  <td className="px-4 py-3 text-xs text-slate-mist">
                    {new Date(d.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">{d.status}</td>
                  <td className="px-4 py-3">{d.attempts}</td>
                  <td className="max-w-sm truncate px-4 py-3 text-xs" title={d.error}>
                    {d.error}
                  </td>
                  <td className="space-x-3 px-4 py-3 text-right">
                    {d.status === "open" ? (
                      <>
                        <button
                          type="button"
                          onClick={() => replay(d.id)}
                          className="text-sm font-medium text-river-700 hover:underline"
                        >
                          Replay
                        </button>
                        <button
                          type="button"
                          onClick={() => discard(d.id)}
                          className="text-sm font-medium text-slate-mist hover:underline"
                        >
                          Discard
                        </button>
                      </>
                    ) : null}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
