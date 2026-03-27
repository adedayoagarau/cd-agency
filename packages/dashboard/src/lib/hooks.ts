"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import {
  api,
  type APIAgent,
  type APIAgentDetail,
  type RunResult,
  type BrandDNAData,
  type MemoryEntryData,
  type MemoryStatsData,
  type ConnectorData,
  type HistoryRunData,
  type CouncilStatusData,
} from "./api";

// Generic hook for API calls with loading/error states
function useApiCall<T>(
  fetcher: () => Promise<T>,
  deps: unknown[] = []
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetcher();
      if (mountedRef.current) setData(result);
    } catch (e: unknown) {
      if (mountedRef.current) setError(e instanceof Error ? e.message : String(e));
    } finally {
      if (mountedRef.current) setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    mountedRef.current = true;
    refetch();
    return () => { mountedRef.current = false; };
  }, [refetch]);

  return { data, loading, error, refetch };
}

// ── Agent hooks ──

export function useAgents() {
  return useApiCall(() => api.listAgents().then((r) => r.agents));
}

export function useAgent(slug: string) {
  return useApiCall(() => api.getAgent(slug), [slug]);
}

export function useRunAgent() {
  const [result, setResult] = useState<RunResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (params: Parameters<typeof api.runAgent>[0]) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.runAgent(params);
      setResult(res);
      return res;
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { run, result, loading, error };
}

// ── Streaming hook ──

export function useStreamAgentRun() {
  const [chunks, setChunks] = useState("");
  const [evaluation, setEvaluation] = useState<Record<string, unknown> | null>(null);
  const [status, setStatus] = useState<"idle" | "running" | "done" | "error">("idle");

  const stream = (params: { agent_slug: string; content: string }) => {
    setChunks("");
    setEvaluation(null);
    setStatus("running");

    const ws = api.streamAgentRun(params);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "output") setChunks(data.content);
      if (data.type === "evaluation") setEvaluation(data);
      if (data.type === "done") {
        setStatus("done");
        ws.close();
      }
      if (data.type === "error") {
        setStatus("error");
      }
    };

    ws.onerror = () => setStatus("error");
  };

  return { stream, chunks, evaluation, status };
}

// ── Brand DNA hooks ──

export function useBrandDNA() {
  return useApiCall(() => api.getBrandDNA());
}

// ── Memory hooks ──

export function useMemorySearch(query: string, scope?: string) {
  return useApiCall(
    () =>
      query
        ? api.searchMemory(query, scope).then((r) => r.results)
        : Promise.resolve([] as MemoryEntryData[]),
    [query, scope]
  );
}

export function useMemoryStats() {
  return useApiCall(() => api.getMemoryStats());
}

// ── Connector hooks ──

export function useConnectors() {
  return useApiCall(() => api.listConnectors().then((r) => r.connectors));
}

// ── History hooks ──

export function useHistory(params?: {
  agent?: string;
  status?: string;
  limit?: number;
  offset?: number;
}) {
  return useApiCall(
    () => api.getHistory(params),
    [params?.agent, params?.status, params?.limit, params?.offset]
  );
}

// ── Config hooks ──

export function useQualityThresholds() {
  return useApiCall(() => api.getQualityThresholds());
}

export function useCouncilStatus() {
  return useApiCall(() => api.getCouncilStatus());
}

// ── Scoring hooks ──

export function useScoring() {
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const score = async (type: "readability" | "lint" | "a11y" | "all", text: string) => {
    setLoading(true);
    setError(null);
    try {
      let res;
      switch (type) {
        case "readability": res = await api.scoreReadability(text); break;
        case "lint": res = await api.scoreLint(text); break;
        case "a11y": res = await api.scoreA11y(text); break;
        case "all": res = await api.scoreAll(text); break;
      }
      setResult(res as unknown as Record<string, unknown>);
      return res;
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { score, result, loading, error };
}

// ── Validation hooks ──

export function useElementTypes() {
  return useApiCall(() => api.getElementTypes());
}

export function useValidate() {
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validate = async (text: string, elementType: string, platform?: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.validate(text, elementType, platform);
      setResult(res as unknown as Record<string, unknown>);
      return res;
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { validate, result, loading, error };
}

// ── Workflow hooks ──

export function useWorkflows() {
  return useApiCall(() => api.listWorkflows());
}

export function useWorkflow(slug: string) {
  return useApiCall(() => api.getWorkflow(slug), [slug]);
}

export function useRunWorkflow() {
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (slug: string, input: Record<string, string>) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.runWorkflow(slug, input);
      setResult(res as unknown as Record<string, unknown>);
      return res;
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
      return null;
    } finally {
      setLoading(false);
    }
  };

  return { run, result, loading, error };
}

// ── Preset hooks ──

export function usePresets() {
  return useApiCall(() => api.listPresets());
}

export function usePreset(name: string) {
  return useApiCall(() => api.getPreset(name), [name]);
}
