import Link from "next/link";
import { Sparkles } from "lucide-react";
import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <main className="min-h-screen app-grid">
      <div className="mx-auto grid min-h-screen w-full max-w-7xl lg:grid-cols-[0.95fr_1.05fr]">
        <section className="flex flex-col justify-between border-r border-border/70 px-8 py-10">
          <Link href="/" className="inline-flex items-center gap-3 text-sm font-medium text-muted-foreground">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
              <Sparkles className="h-5 w-5" />
            </span>
            backend-api frontend
          </Link>

          <div className="max-w-xl space-y-6">
            <span className="inline-flex rounded-full border border-border/70 bg-white/5 px-4 py-2 text-xs uppercase tracking-[0.28em] text-muted-foreground">
              Auth Portal
            </span>
            <h1 className="font-display text-5xl font-semibold tracking-tight">
              Sign in once and move through planning, execution, and ingestion without switching tools.
            </h1>
            <p className="text-lg text-muted-foreground">
              This interface is intentionally lean so the backend workflows stay the focus.
            </p>
          </div>

          <p className="text-sm text-muted-foreground">
            Built for the backend-api orchestration layer and the separate ai-service.
          </p>
        </section>

        <section className="flex items-center justify-center px-6 py-12 lg:px-12">
          <div className="w-full max-w-md">{children}</div>
        </section>
      </div>
    </main>
  );
}
