"use client";

import { Bell, CircleDot, MoonStar } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/providers/auth-provider";
import { useWebSocket } from "@/components/providers/websocket-provider";

export function Topbar() {
  const { user } = useAuth();
  const { status, lastEvent } = useWebSocket();

  return (
    <header className="sticky top-0 z-10 flex items-center justify-between border-b border-border/70 bg-background/80 px-6 py-4 backdrop-blur">
      <div>
        <p className="text-sm text-muted-foreground">Welcome back</p>
        <h2 className="font-display text-xl font-semibold">{user?.full_name ?? user?.email ?? "Team member"}</h2>
      </div>
      <div className="flex items-center gap-3">
        <Badge variant={status === "connected" ? "success" : "warning"} className="gap-2">
          <CircleDot className="h-3 w-3" />
          {status}
        </Badge>
        {lastEvent ? (
          <Badge variant="outline" className="hidden max-w-sm truncate lg:inline-flex">
            {lastEvent.message}
          </Badge>
        ) : null}
        <Button variant="outline" size="sm" type="button">
          <Bell className="h-4 w-4" />
          Alerts
        </Button>
        <Button variant="ghost" size="sm" type="button">
          <MoonStar className="h-4 w-4" />
          Theme
        </Button>
      </div>
    </header>
  );
}
