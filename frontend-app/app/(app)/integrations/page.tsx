"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Bell, BrainCircuit, CalendarClock, Database, Globe, ShieldAlert, Sparkles } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { backendApi } from "@/lib/api/backend-api";
import type { IntegrationStatus } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

function statusVariant(status: IntegrationStatus["status"]): "default" | "success" | "warning" | "destructive" | "outline" {
  switch (status) {
    case "configured":
    case "available":
      return "success";
    case "local_fallback":
      return "warning";
    case "missing_config":
      return "outline";
    case "unavailable":
      return "destructive";
    default:
      return "default";
  }
}

function statusLabel(status: IntegrationStatus["status"]): string {
  switch (status) {
    case "configured":
      return "Configured";
    case "available":
      return "Available";
    case "local_fallback":
      return "Local fallback";
    case "missing_config":
      return "Missing config";
    case "unavailable":
      return "Unavailable";
    default:
      return status;
  }
}

function iconForCapability(capability: IntegrationStatus["capability"]) {
  switch (capability) {
    case "retrieve_knowledge":
      return Globe;
    case "generate_content":
      return BrainCircuit;
    case "store_data":
      return Database;
    case "schedule":
      return CalendarClock;
    case "notify":
      return Bell;
    default:
      return Sparkles;
  }
}

export default function IntegrationsPage() {
  const integrationsQuery = useQuery({
    queryKey: ["integrations"],
    queryFn: async () => backendApi.listIntegrations(),
  });

  const integrations = integrationsQuery.data ?? [];
  const configuredCount = integrations.filter((item) => item.status === "configured" || item.status === "available").length;
  const fallbackCount = integrations.filter((item) => item.status === "local_fallback").length;
  const approvalCount = integrations.filter((item) => item.requires_approval).length;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Integrations"
        description="See which capabilities are wired to real adapters, which ones use local fallbacks, and where human approval is required."
        actions={
          <>
            <Button asChild variant="outline" size="sm">
              <Link href="/rag">
                Open RAG
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild size="sm">
              <Link href="/approvals">
                Review approvals
                <ShieldAlert className="h-4 w-4" />
              </Link>
            </Button>
          </>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="glass-panel">
          <CardContent className="p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Configured</p>
            <p className="mt-2 text-3xl font-semibold">{configuredCount}</p>
            <p className="mt-2 text-sm text-muted-foreground">Adapters connected or available with settings in place.</p>
          </CardContent>
        </Card>
        <Card className="glass-panel">
          <CardContent className="p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Local fallback</p>
            <p className="mt-2 text-3xl font-semibold">{fallbackCount}</p>
            <p className="mt-2 text-sm text-muted-foreground">Capabilities that work locally until external connectors are added.</p>
          </CardContent>
        </Card>
        <Card className="glass-panel">
          <CardContent className="p-5">
            <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Approval-gated</p>
            <p className="mt-2 text-3xl font-semibold">{approvalCount}</p>
            <p className="mt-2 text-sm text-muted-foreground">Integrations that require a human before running.</p>
          </CardContent>
        </Card>
      </div>

      {integrationsQuery.isLoading ? (
        <Card className="glass-panel">
          <CardContent className="p-6 text-sm text-muted-foreground">Loading integrations...</CardContent>
        </Card>
      ) : null}

      {integrationsQuery.error ? (
        <Card className="glass-panel border-destructive/30">
          <CardContent className="p-6 text-sm text-destructive">
            {integrationsQuery.error instanceof Error ? integrationsQuery.error.message : "Unable to load integrations"}
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-6 xl:grid-cols-2">
        {integrations.map((integration) => {
          const Icon = iconForCapability(integration.capability);
          return (
            <Card key={integration.tool_name} className="glass-panel">
              <CardHeader>
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <CardTitle>{integration.name}</CardTitle>
                      <CardDescription>{integration.description}</CardDescription>
                    </div>
                  </div>
                  <Badge variant={statusVariant(integration.status)}>{statusLabel(integration.status)}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">{integration.capability}</Badge>
                  <Badge variant="secondary">{integration.tool_name}</Badge>
                  {integration.requires_approval ? <Badge variant="warning">Requires approval</Badge> : <Badge variant="success">Safe path</Badge>}
                </div>

                <div className="grid gap-3 md:grid-cols-2">
                  <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Configured</p>
                    <p className="mt-2 text-sm font-medium">{integration.configured ? "Yes" : "No"}</p>
                  </div>
                  <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Approval</p>
                    <p className="mt-2 text-sm font-medium">{integration.requires_approval ? "Human-in-the-loop" : "Automatic"}</p>
                  </div>
                </div>

                {integration.notes.length > 0 ? (
                  <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Notes</p>
                    <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                      {integration.notes.map((note) => (
                        <li key={note}>- {note}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                <details className="rounded-2xl border border-border/70 bg-white/5 p-4">
                  <summary className="cursor-pointer text-sm font-medium">Details</summary>
                  <pre className="mt-4 max-h-56 overflow-auto text-xs leading-6 text-muted-foreground">
                    {JSON.stringify(integration.details, null, 2)}
                  </pre>
                </details>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
