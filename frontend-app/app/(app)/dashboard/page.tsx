"use client";

import Link from "next/link";
import { ArrowRight, Clock3, FileText, Flame, FolderPlus, Layers3, RadioTower, Sparkles } from "lucide-react";

import { useAuth } from "@/components/providers/auth-provider";
import { useWebSocket } from "@/components/providers/websocket-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";

const shortcuts = [
  { href: "/workspaces", label: "Create workspace", icon: FolderPlus },
  { href: "/goals", label: "Create goal", icon: Layers3 },
  { href: "/planning", label: "Planning workspace", icon: Flame },
  { href: "/plans", label: "Finalize plan", icon: FileText },
  { href: "/rag", label: "Ingest document", icon: Sparkles },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const { status, lastEvent, events } = useWebSocket();

  return (
    <div className="space-y-8">
      <PageHeader
        title="Dashboard"
        description="Your orchestration command center for goal capture, planning, execution monitoring, and document ingestion."
      />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="glass-panel">
          <CardHeader>
            <CardTitle>Session</CardTitle>
            <CardDescription>Authenticated user and active session details.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-sm text-muted-foreground">User</p>
              <p className="font-medium">{user?.email ?? "Not available"}</p>
            </div>
            <Badge variant={status === "connected" ? "success" : "warning"}>{status}</Badge>
          </CardContent>
        </Card>

        <Card className="glass-panel">
          <CardHeader>
            <CardTitle>Realtime feed</CardTitle>
            <CardDescription>Latest event received from the backend-api websocket gateway.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {lastEvent ? (
              <>
                <p className="font-medium">{lastEvent.message}</p>
                <p className="text-sm text-muted-foreground">
                  {lastEvent.event_type} • {lastEvent.entity_type} • {lastEvent.timestamp}
                </p>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">No realtime events yet.</p>
            )}
          </CardContent>
        </Card>

        <Card className="glass-panel">
          <CardHeader>
            <CardTitle>Event count</CardTitle>
            <CardDescription>Recent realtime events kept in memory.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="text-4xl font-semibold">{events.length}</div>
            <p className="text-sm text-muted-foreground">Useful for monitoring planning, execution, and RAG flows.</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card className="glass-panel">
          <CardHeader>
            <CardTitle>Quick actions</CardTitle>
            <CardDescription>Common routes for the frontend to exercise the orchestration layer.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-3">
            {shortcuts.map((item) => {
              const Icon = item.icon;
              return (
                <Button asChild key={item.href} variant="outline" className="justify-start h-auto py-4">
                  <Link href={item.href}>
                    <Icon className="h-4 w-4" />
                    {item.label}
                    <ArrowRight className="ml-auto h-4 w-4 opacity-60" />
                  </Link>
                </Button>
              );
            })}
          </CardContent>
        </Card>

        <Card className="glass-panel">
          <CardHeader>
            <CardTitle>What’s connected</CardTitle>
            <CardDescription>These frontend modules are ready to speak to backend-api today.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-muted-foreground">
            <div className="flex items-center gap-3">
              <RadioTower className="h-4 w-4 text-primary" />
              WebSocket updates for long-running operations
            </div>
            <div className="flex items-center gap-3">
              <Flame className="h-4 w-4 text-primary" />
              JWT-authenticated API calls
            </div>
            <div className="flex items-center gap-3">
              <Clock3 className="h-4 w-4 text-primary" />
              React Query for request orchestration
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
