"use client";

import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Check, Copy, FolderPlus, Loader2, Sparkles } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { backendApi } from "@/lib/api/backend-api";
import type { Workspace } from "@/lib/types";

export default function WorkspacesPage() {
  const { user } = useAuth();
  const [name, setName] = useState("Node.js Study Plan");
  const [description, setDescription] = useState("Workspace for planning, execution, and RAG ingestion.");
  const [createdWorkspace, setCreatedWorkspace] = useState<Workspace | null>(null);
  const [copied, setCopied] = useState(false);

  const mutation = useMutation({
    mutationFn: async () => {
      if (!user?.id) {
        throw new Error("You must be signed in to create a workspace.");
      }

      return backendApi.createWorkspace({
        user_id: user.id,
        name: name.trim(),
        description: description.trim() || null,
      });
    },
    onSuccess: (workspace) => {
      setCreatedWorkspace(workspace);
      setCopied(false);
    },
  });

  const workspaceId = createdWorkspace?.id ?? null;
  const errorMessage =
    mutation.error instanceof Error
      ? mutation.error.message
      : mutation.error
        ? String(mutation.error)
        : null;

  async function handleCopy() {
    if (!workspaceId || typeof navigator === "undefined") {
      return;
    }

    await navigator.clipboard.writeText(workspaceId);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  const statusTone = useMemo(() => {
    if (mutation.isPending) {
      return "Creating workspace...";
    }
    if (createdWorkspace) {
      return "Workspace created successfully";
    }
    return "Ready to create";
  }, [createdWorkspace, mutation.isPending]);

  return (
    <div className="space-y-8">
      <PageHeader
        title="Workspaces"
        description="Create the top-level container for a project, study path, or execution workflow. Goals and plans should live under a workspace."
      />

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <Card className="glass-panel">
          <CardHeader>
            <CardTitle>Create a workspace</CardTitle>
            <CardDescription>
              Start with a clean scope so the planning, execution, and RAG flows stay organized.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="rounded-2xl border border-border/70 bg-background/70 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Signed in user</p>
              <p className="mt-2 text-sm font-medium">{user?.email ?? "No authenticated user found"}</p>
              <p className="mt-1 text-xs text-muted-foreground">The workspace will be created under this account.</p>
            </div>

            <form
              className="space-y-5"
              onSubmit={(event) => {
                event.preventDefault();
                mutation.mutate();
              }}
            >
              <div className="space-y-2">
                <Label htmlFor="workspace-name">Workspace name</Label>
                <Input
                  id="workspace-name"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Node.js Study Plan"
                  required
                  minLength={1}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="workspace-description">Description</Label>
                <Textarea
                  id="workspace-description"
                  value={description}
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder="Workspace for planning, execution, and RAG ingestion."
                  rows={5}
                />
              </div>

              {errorMessage ? (
                <div className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  {errorMessage}
                </div>
              ) : null}

              <Button type="submit" className="w-full" disabled={mutation.isPending || !user?.id}>
                {mutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creating workspace
                  </>
                ) : (
                  <>
                    <FolderPlus className="h-4 w-4" />
                    Create workspace
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="glass-panel">
            <CardHeader>
              <CardTitle>Workspace status</CardTitle>
              <CardDescription>Track the current creation state and copy the ID once generated.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-3 rounded-2xl border border-border/70 bg-background/70 px-4 py-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  {createdWorkspace ? <Check className="h-5 w-5" /> : <Sparkles className="h-5 w-5" />}
                </div>
                <div>
                  <p className="text-sm font-medium">{statusTone}</p>
                  <p className="text-xs text-muted-foreground">
                    {createdWorkspace ? "Use this workspace ID when creating goals." : "Create one to continue into goals and planning."}
                  </p>
                </div>
              </div>

              <div className="rounded-2xl border border-border/70 bg-background/70 p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-muted-foreground">Workspace ID</p>
                <div className="mt-2 flex items-center gap-3">
                  <p className="break-all font-mono text-sm text-foreground">
                    {workspaceId ?? "No workspace created yet"}
                  </p>
                  <Button type="button" variant="outline" className="h-10 w-10 p-0" onClick={handleCopy} disabled={!workspaceId}>
                    {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  </Button>
                </div>
              </div>

              <div className="rounded-2xl border border-border/70 bg-accent/40 p-4 text-sm text-muted-foreground">
                The workspace is the parent container for your goal, generated plan, execution jobs, and any uploaded
                documents. Keep one workspace per project or learning track.
              </div>
            </CardContent>
          </Card>

          <Card className="glass-panel">
            <CardHeader>
              <CardTitle>Suggested flow</CardTitle>
              <CardDescription>Once the workspace exists, continue through the orchestration pipeline.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              <div className="rounded-xl border border-border/70 bg-background/70 px-4 py-3">1. Create a goal</div>
              <div className="rounded-xl border border-border/70 bg-background/70 px-4 py-3">2. Finalize the plan</div>
              <div className="rounded-xl border border-border/70 bg-background/70 px-4 py-3">3. Review execution decisions</div>
              <div className="rounded-xl border border-border/70 bg-background/70 px-4 py-3">4. Ingest supporting documents into RAG</div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
