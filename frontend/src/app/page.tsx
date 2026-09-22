import Link from "next/link";

export default function HomePage() {
  return (
    <div className="relative min-h-screen overflow-hidden">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0"
      >
        <div className="absolute inset-x-0 top-0 h-[70vh] bg-[linear-gradient(160deg,#dbeafe_0%,transparent_55%),linear-gradient(20deg,#e0f2fe_0%,transparent_40%)]" />
        <svg
          className="absolute bottom-0 left-0 right-0 h-48 w-full text-river-100 opacity-80"
          viewBox="0 0 1440 200"
          preserveAspectRatio="none"
        >
          <path
            fill="currentColor"
            d="M0,120 C240,180 480,40 720,90 C960,140 1200,180 1440,100 L1440,200 L0,200 Z"
          />
        </svg>
      </div>

      <div className="relative mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-16">
        <p className="font-display text-5xl font-semibold tracking-tight text-slate-ink sm:text-6xl">
          River<span className="text-river-600">CDC</span>
        </p>
        <h1 className="mt-4 max-w-xl text-2xl font-medium text-slate-ink sm:text-3xl">
          Change streams that stay consistent.
        </h1>
        <p className="mt-4 max-w-lg text-lg text-slate-mist">
          Capture PostgreSQL mutations, publish through Kafka, and sync destinations
          with idempotent apply, retries, and dead-letter recovery.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/login"
            className="rounded-lg bg-river-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-river-700"
          >
            Open console
          </Link>
          <a
            href="http://localhost:8007/docs"
            className="rounded-lg border border-slate-line bg-white/70 px-5 py-2.5 text-sm font-semibold text-slate-ink transition hover:border-river-400"
          >
            API docs
          </a>
        </div>
      </div>
    </div>
  );
}
