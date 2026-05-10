"use client";

import type { FormEvent } from "react";
import { useMemo, useState } from "react";
import { CloudUpload, Search, Sparkles, RadioTower, FileText } from "lucide-react";
import { useMutation } from "@tanstack/react-query";

import { PageHeader } from "@/components/layout/page-header";
import { useAuth } from "@/components/providers/auth-provider";
import { useRealtimeEvents } from "@/lib/hooks/use-realtime-events";
import { backendApi } from "@/lib/api/backend-api";
import type { RagIngestResponse, RagQueryResponse, RetrievedChunk } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

function chunkSummary(chunk: RetrievedChunk): string {
  return chunk.text.length > 220 ? `${chunk.text.slice(0, 220)}…` : chunk.text;
}

export default function RagPage() {
  const { user } = useAuth();
  const { status: wsStatus, ragEvents } = useRealtimeEvents();

  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [source, setSource] = useState("frontend_upload");
  const [filename, setFilename] = useState("");
  const [ingestResult, setIngestResult] = useState<RagIngestResponse | null>(null);
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [queryResult, setQueryResult] = useState<RagQueryResponse | null>(null);

  const ingestMutation = useMutation({
    onMutate: () => {
      setIngestResult(null);
    },
    mutationFn: async () =>
      backendApi.ingestDocument({
        file,
        text: file ? null : text,
        userId: user?.id ?? null,
        documentId: documentId || null,
        source,
        filename: filename || undefined,
      }),
    onSuccess: (data) => {
      setIngestResult(data);
    },
  });

  const queryMutation = useMutation({
    onMutate: () => {
      setQueryResult(null);
    },
    mutationFn: async () =>
      backendApi.queryKnowledge({
        query,
        user_id: user?.id ?? null,
        top_k: topK,
      }),
    onSuccess: (data) => {
      setQueryResult(data);
    },
  });

  async function handleIngest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await ingestMutation.mutateAsync();
    } catch {
      // Error state is surfaced in the UI below.
    }
  }

  async function handleQuery(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await queryMutation.mutateAsync();
    } catch {
      // Error state is surfaced in the UI below.
    }
  }

  const latestRagEvent = ragEvents[0] ?? null;

  const sourceChunks = useMemo(() => queryResult?.sources ?? [], [queryResult]);

  return (
    <div className="space-y-8">
      <PageHeader
        title="RAG Ingestion"
        description="Upload documents into the reusable RAG layer, then query grounded answers from backend-api."
      />

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <Card className="glass-panel">
          <CardHeader>
            <CardTitle>Ingest knowledge</CardTitle>
            <CardDescription>
              Upload PDF, markdown, or text files, or paste raw text for ingestion into Qdrant-backed retrieval.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={handleIngest}>
              <div className="space-y-2">
                <Label htmlFor="file">File upload</Label>
                <Input
                  id="file"
                  type="file"
                  accept=".pdf,.md,.markdown,.txt,.text"
                  onChange={(event) => {
                    const selected = event.target.files?.[0] ?? null;
                    setFile(selected);
                    if (selected) {
                      setFilename(selected.name);
                    }
                  }}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="text">Raw text</Label>
                <Textarea
                  id="text"
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                  placeholder="Paste raw text here if you're not uploading a file."
                  rows={7}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="documentId">Document ID</Label>
                <Input
                  id="documentId"
                  value={documentId}
                  onChange={(event) => setDocumentId(event.target.value)}
                  placeholder="Optional stable document identifier"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="source">Source label</Label>
                <Input id="source" value={source} onChange={(event) => setSource(event.target.value)} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="filename">Filename</Label>
                <Input
                  id="filename"
                  value={filename}
                  onChange={(event) => setFilename(event.target.value)}
                  placeholder="Optional display filename"
                />
              </div>
              {ingestMutation.error ? (
                <div className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                  {ingestMutation.error instanceof Error ? ingestMutation.error.message : "Unable to ingest document"}
                </div>
              ) : null}
              <Button type="submit" className="w-full" disabled={ingestMutation.isPending}>
                <CloudUpload className="h-4 w-4" />
                {ingestMutation.isPending ? "Ingesting..." : "Ingest document"}
              </Button>
            </form>

            <div className="mt-6 space-y-3">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                <h3 className="text-sm font-medium">Ingestion result</h3>
              </div>
              {ingestResult ? (
                <div className="space-y-3 rounded-2xl border border-border/70 bg-white/5 p-4">
                  <div className="grid gap-3 md:grid-cols-2">
                    <div>
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Document</p>
                      <p className="mt-2 break-all text-sm font-medium">{ingestResult.document_id}</p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Chunks indexed</p>
                      <p className="mt-2 text-sm font-medium">{ingestResult.chunk_count}</p>
                    </div>
                  </div>
                  <pre className="max-h-[16rem] overflow-auto rounded-2xl border border-border/70 bg-black/30 p-4 text-xs leading-6 text-muted-foreground">
                    {JSON.stringify(ingestResult, null, 2)}
                  </pre>
                </div>
              ) : (
                <div className="rounded-2xl border border-dashed border-border/70 bg-white/5 p-4 text-sm text-muted-foreground">
                  Upload a document or paste text to see the ingestion result here.
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card className="glass-panel">
            <CardHeader>
              <CardTitle>Grounded retrieval search</CardTitle>
              <CardDescription>
                Query the RAG index and view the generated answer with the supporting source chunks.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-4" onSubmit={handleQuery}>
                <div className="space-y-2">
                  <Label htmlFor="query">Knowledge query</Label>
                  <Textarea
                    id="query"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Ask a question about the ingested knowledge."
                    rows={4}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="topK">Top K sources</Label>
                  <Input
                    id="topK"
                    type="number"
                    min={1}
                    max={10}
                    value={topK}
                    onChange={(event) => setTopK(Number(event.target.value) || 5)}
                  />
                </div>
                {queryMutation.error ? (
                  <div className="rounded-2xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
                    {queryMutation.error instanceof Error ? queryMutation.error.message : "Unable to query knowledge"}
                  </div>
                ) : null}
                <Button type="submit" className="w-full" disabled={queryMutation.isPending}>
                  <Search className="h-4 w-4" />
                  {queryMutation.isPending ? "Searching..." : "Search knowledge"}
                </Button>
              </form>

              <div className="mt-6 space-y-4">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-primary" />
                  <h3 className="text-sm font-medium">Grounded answer</h3>
                </div>
                {queryResult ? (
                  <div className="space-y-4">
                    <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Answer</p>
                      <p className="mt-3 whitespace-pre-wrap text-sm leading-6">{queryResult.answer}</p>
                    </div>

                    <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                      <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Sources</p>
                      <div className="mt-4 space-y-3">
                        {sourceChunks.length > 0 ? (
                          sourceChunks.map((chunk) => (
                            <div key={chunk.chunk_id} className="rounded-2xl border border-border/70 bg-background/80 p-4">
                              <div className="flex flex-wrap items-center gap-2">
                                <Badge variant="outline">{chunk.chunk_id}</Badge>
                                {chunk.source ? <Badge variant="secondary">{chunk.source}</Badge> : null}
                                <Badge variant="default">Score {chunk.score.toFixed(2)}</Badge>
                              </div>
                              <p className="mt-3 text-sm leading-6 text-muted-foreground">{chunkSummary(chunk)}</p>
                            </div>
                          ))
                        ) : (
                          <p className="text-sm text-muted-foreground">No source chunks returned.</p>
                        )}
                      </div>
                    </div>

                    <details className="rounded-2xl border border-border/70 bg-white/5 p-4">
                      <summary className="cursor-pointer text-sm font-medium">Raw retrieval response</summary>
                      <pre className="mt-4 max-h-[16rem] overflow-auto text-xs leading-6 text-muted-foreground">
                        {JSON.stringify(queryResult, null, 2)}
                      </pre>
                    </details>
                  </div>
                ) : (
                  <div className="rounded-2xl border border-dashed border-border/70 bg-white/5 p-4 text-sm text-muted-foreground">
                    Search after ingesting documents to review a grounded answer and source chunks.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="glass-panel">
            <CardHeader>
              <CardTitle>RAG websocket feed</CardTitle>
              <CardDescription>Realtime hints for ingestion and retrieval operations.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-3 md:grid-cols-3">
                <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">WebSocket</p>
                  <div className="mt-3 flex items-center gap-2">
                    <RadioTower className="h-4 w-4 text-primary" />
                    <Badge variant={wsStatus === "connected" ? "success" : wsStatus === "error" ? "destructive" : "warning"}>
                      {wsStatus}
                    </Badge>
                  </div>
                </div>
                <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Ingestion</p>
                  <p className="mt-3 text-sm text-muted-foreground">
                    {ingestMutation.isPending ? "Indexing knowledge..." : "Ready"}
                  </p>
                </div>
                <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Retrieval</p>
                  <p className="mt-3 text-sm text-muted-foreground">
                    {queryMutation.isPending ? "Searching knowledge..." : "Ready"}
                  </p>
                </div>
              </div>

              {latestRagEvent ? (
                <div className="rounded-2xl border border-border/70 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">Latest event</p>
                  <p className="mt-2 text-sm font-medium">{latestRagEvent.message}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {latestRagEvent.event_type} - {latestRagEvent.timestamp}
                  </p>
                </div>
              ) : null}

              <div className="space-y-3">
                {ragEvents.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No RAG websocket events yet.</p>
                ) : (
                  ragEvents.map((event) => (
                    <div key={`${event.entity_id}-${event.timestamp}`} className="rounded-2xl border border-border/70 bg-white/5 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-medium">{event.message}</p>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {event.entity_type} - {event.entity_id} - {event.timestamp}
                          </p>
                        </div>
                        <Badge variant={event.event_type === "rag_ingestion_completed" ? "success" : "warning"}>
                          {event.event_type}
                        </Badge>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
