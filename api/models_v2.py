from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class RunAgentRequest(BaseModel):
    agent_slug: str
    content: str
    model: Optional[str] = None
    enable_council: bool = False
    context: Optional[Dict[str, Any]] = None

class RunAgentResponse(BaseModel):
    run_id: str
    agent: str
    output: str
    evaluation: Dict[str, float]
    composite_score: float
    passed: bool
    iterations: int
    council_result: Optional[Dict[str, Any]] = None
    duration_ms: int

class AgentSummaryV2(BaseModel):
    slug: str
    name: str
    description: str
    model: str
    tools: List[str]
    tags: List[str]
    evaluation: Dict[str, Any]
    threshold: float

class BrandDNAResponse(BaseModel):
    voice_patterns: List[Dict[str, Any]]
    terminology: List[Dict[str, Any]]
    style_rules: List[Dict[str, Any]]
    sources: List[str]

class BrandDNAUpdate(BaseModel):
    voice_patterns: Optional[List[Dict[str, Any]]] = None
    terminology: Optional[List[Dict[str, Any]]] = None
    style_rules: Optional[List[Dict[str, Any]]] = None

class IngestRequest(BaseModel):
    content: Optional[str] = None
    file_path: Optional[str] = None

class MemorySearchRequest(BaseModel):
    query: str
    scope: Optional[str] = None
    limit: int = 20

class MemoryEntryResponse(BaseModel):
    key: str
    value: str
    category: str
    source_agent: str
    scope: str
    timestamp: Optional[str] = None
    relevance_score: Optional[float] = None

class MemoryStatsResponse(BaseModel):
    session_count: int
    project_count: int
    workspace_count: int
    total_entries: int

class ConnectorResponse(BaseModel):
    name: str
    type: str
    status: str
    last_sync: Optional[str] = None
    entry_count: int = 0

class ConnectorSyncRequest(BaseModel):
    connector_name: str
    sync_mode: str = "pull"
    dry_run: bool = False

class HistoryEntryResponse(BaseModel):
    agent_slug: str
    composite_score: float
    passed: bool
    iteration_count: int
    timestamp: str
    scores: Dict[str, Any]

class QualityThresholdsResponse(BaseModel):
    thresholds: Dict[str, float]

class CouncilStatusResponse(BaseModel):
    enabled: bool
    min_models: int
    consensus_method: str
    trigger_conditions: List[str]
