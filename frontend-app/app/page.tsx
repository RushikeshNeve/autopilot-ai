import Link from "next/link";
import { ArrowRight, Layers3, Rocket, Sparkles, ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const highlights = [
  {
    title: "Goal to Plan",
    description: "Turn a raw goal into structured milestones and tasks with a clean orchestration layer.",
    icon: Layers3,
  },
  {
    title: "Realtime Visibility",
    description: "Stream progress events over WebSocket for long-running planning and ingestion workflows.",
    icon: Rocket,
  },
  {
    title: "Grounded Retrieval",
    description: "Upload documents and prepare them for the reusable RAG layer behind the scenes.",
    icon: Sparkles,
  },
  {
    title: "JWT Protected",
    description: "Everything runs through backend-api with a simple, authentication-first flow.",
    icon: ShieldCheck,
  },
];

export default function HomePage() {
  return (
    <main className="app-grid min-h-screen">
      <section className="mx-auto flex min-h-screen w-full max-w-7xl flex-col justify-center px-6 py-16">
        <div className="grid gap-10 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
          <div className="space-y-8">
            <span className="inline-flex rounded-full border border-border/70 bg-white/5 px-4 py-2 text-xs uppercase tracking-[0.28em] text-muted-foreground">
              AI Planning Platform
            </span>
            <div className="space-y-5">
              <h1 className="font-display max-w-3xl text-5xl font-semibold tracking-tight md:text-6xl">
                An orchestration console for planning, execution, and grounded AI workflows.
              </h1>
              <p className="max-w-2xl text-lg text-muted-foreground">
                backend-api sits between the frontend and ai-service, keeping user experience, auth, and data
                orchestration clean and predictable.
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <Button asChild>
                <Link href="/login">
                  Get started
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/register">Create account</Link>
              </Button>
            </div>
          </div>

          <Card className="glass-panel border-border/60 shadow-glow">
            <CardHeader>
              <CardTitle>What this frontend will handle</CardTitle>
              <CardDescription>
                Auth, workspace management, goal capture, plan review, execution monitoring, and RAG ingestion.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
              {highlights.map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.title} className="flex items-start gap-4 rounded-2xl border border-border/60 bg-white/5 p-4">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/15 text-primary">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <h2 className="font-medium">{item.title}</h2>
                      <p className="mt-1 text-sm text-muted-foreground">{item.description}</p>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  );
}
