"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

type Pipeline = {
  id: string;
  name: string;
  source_schema: string;
  source_table: string;
  topic: string;
  dest_schema: string;
  dest_table: string;
  status: string;
  max_retries: number;
};

export default function PipelinesPage() {
  const router = useRouter();
  const [email, setEmail] = useState<string>();
  const [rows, setRows] = useState<Pipeline[]>([]);

  useEffect(() => {
    (async () => {
      const me = await api<{ email: string }>("/api/auth/me");
      if (!me.success) {
        router.replace("/login");
        return;
      }
      setEmail(me.data.email);
      const res = await api<Pipeline[]>("/api/pipelines");
      if (res.success) setRows(res.data);
    })();
  }, [router]);

  return (
    <AppShell userEmail={email}>
      <h1 className="font-display text-3xl font-semibold text-slate-ink">Pipelines</h1>
      <p className="mt-1 text-slate-mist">Source → Kafka topic → destination mappings.</p>
      <div className="mt-6 overflow-hidden rounded-xl border border-slate-line bg-white/80">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-soft/80 text-slate-mist">
            <tr>
              <th className="px-4 py-3 font-medium">Name</th>
              <th className="px-4 py-3 font-medium">Source</th>
              <th className="px-4 py-3 font-medium">Topic</th>
              <th className="px-4 py-3 font-medium">Destination</th>
              <th className="px-4 py-3 font-medium">Status</th>
              <th className="px-4 py-3 font-medium">Retries</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id} className="border-t border-slate-line/70">
                <td className="px-4 py-3 font-medium">{p.name}</td>
                <td className="px-4 py-3 font-mono text-xs">
                  {p.source_schema}.{p.source_table}
                </td>
                <td className="px-4 py-3 font-mono text-xs">{p.topic}</td>
                <td className="px-4 py-3 font-mono text-xs">
                  {p.dest_schema}.{p.dest_table}
                </td>
                <td className="px-4 py-3">{p.status}</td>
                <td className="px-4 py-3">{p.max_retries}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
