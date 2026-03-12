"""CD Agency Runtime — Load, validate, and execute content design agents."""

from runtime.agent import Agent, AgentOutput
from runtime.loader import load_agent, load_agents_from_directory
from runtime.registry import AgentRegistry
from runtime.config import Config
from runtime.knowledge import (
    load_knowledge_file,
    resolve_knowledge_refs,
    list_knowledge_files,
    search_knowledge,
)
from runtime.preflight import (
    ClarifyingQuestion,
    PreflightResult,
    run_preflight,
    build_assumption_block,
)
from runtime.constraints import (
    ConstraintViolation,
    ConstraintResult,
    validate_content,
    validate_character_limit,
    validate_localization,
    validate_platform_conventions,
    validate_accessibility,
    get_element_limit,
    list_element_types,
)
from runtime.design_system import (
    ComponentConstraint,
    DesignSystem,
    load_design_system,
    load_design_system_from_config,
)
from runtime.postprocess import (
    ContentFragment,
    PostprocessResult,
    extract_fragments,
    postprocess_output,
)
from runtime.versioning import (
    ContentVersion,
    ContentHistory,
)

__all__ = [
    "Agent",
    "AgentOutput",
    "load_agent",
    "load_agents_from_directory",
    "AgentRegistry",
    "Config",
    "load_knowledge_file",
    "resolve_knowledge_refs",
    "list_knowledge_files",
    "search_knowledge",
    # Preflight
    "ClarifyingQuestion",
    "PreflightResult",
    "run_preflight",
    "build_assumption_block",
    # Constraints
    "ConstraintViolation",
    "ConstraintResult",
    "validate_content",
    "validate_character_limit",
    "validate_localization",
    "validate_platform_conventions",
    "validate_accessibility",
    "get_element_limit",
    "list_element_types",
    # Design System
    "ComponentConstraint",
    "DesignSystem",
    "load_design_system",
    "load_design_system_from_config",
    # Post-processing
    "ContentFragment",
    "PostprocessResult",
    "extract_fragments",
    "postprocess_output",
    # Versioning
    "ContentVersion",
    "ContentHistory",
]
