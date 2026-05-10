"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Compass, Database, FolderPlus, Gauge, Layers3, LogOut, Network, Rocket, ShieldCheck, Sparkles, Workflow } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/providers/auth-provider";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: Gauge },
  { href: "/workspaces", label: "Workspaces", icon: FolderPlus },
  { href: "/goals", label: "Goals", icon: Compass },
  { href: "/planning", label: "Planning", icon: Workflow },
  { href: "/plans", label: "Plans", icon: Layers3 },
  { href: "/executions", label: "Executions", icon: Rocket },
  { href: "/approvals", label: "Approvals", icon: ShieldCheck },
  { href: "/integrations", label: "Integrations", icon: Database },
  { href: "/rag", label: "RAG Ingestion", icon: Sparkles },
];

export function Sidebar() {
  const pathname = usePathname();
  const { logout, user } = useAuth();

  return (
    <aside className="flex h-full w-72 flex-col border-r border-border/70 bg-card/50 backdrop-blur">
      <div className="border-b border-border/70 px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-glow">
            <Network className="h-5 w-5" />
          </div>
          <div>
            <div className="font-display text-lg font-semibold">backend-api</div>
            <p className="text-xs text-muted-foreground">AI orchestration layer</p>
          </div>
        </div>
      </div>

      <div className="flex-1 px-4 py-6">
        <nav className="space-y-1">
          {navItems.map((item) => {
            const active = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-colors",
                  active
                    ? "bg-primary text-primary-foreground shadow-glow"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                )}
              >
                <Icon className="h-4 w-4" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      <div className="border-t border-border/70 p-4">
        <div className="rounded-2xl border border-border/70 bg-background/80 p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Signed in as</p>
              <p className="mt-1 text-sm font-medium">{user?.email ?? "Unknown user"}</p>
            </div>
            <Badge variant="outline">JWT</Badge>
          </div>
          <Button
            variant="ghost"
            className="mt-4 w-full justify-start text-muted-foreground"
            onClick={logout}
            type="button"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </Button>
        </div>
      </div>
    </aside>
  );
}
