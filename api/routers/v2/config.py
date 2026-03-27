from __future__ import annotations
from fastapi import APIRouter
from typing import Any, Dict
from pathlib import Path

router = APIRouter(prefix="/api/v2", tags=["config-v2"])

@router.get("/config/quality-thresholds")
async def get_quality_thresholds():
    try:
        from runtime.quality_config import QualityConfig
        config = QualityConfig()
        # Return default thresholds
        return {
            "readability": config.get_threshold("default", "readability"),
            "linter": config.get_threshold("default", "linter"),
            "accessibility": config.get_threshold("default", "accessibility"),
            "voice": config.get_threshold("default", "voice"),
            "composite": config.get_threshold("default", "composite"),
            "max_iterations": 3,
        }
    except Exception:
        return {
            "readability": 0.75,
            "linter": 0.80,
            "accessibility": 0.70,
            "voice": 0.75,
            "composite": 0.75,
            "max_iterations": 3,
        }

@router.put("/config/quality-thresholds")
async def update_quality_thresholds(thresholds: Dict[str, Any]):
    """Update quality thresholds and persist them via QualityConfig."""
    try:
        from runtime.quality_config import QualityConfig
        config = QualityConfig()
        for key, value in thresholds.items():
            if key == "max_iterations":
                config.set_max_iterations("default", int(value))
            else:
                config.set_threshold("default", key, float(value))
        config.save()
        return {"status": "updated", "thresholds": thresholds}
    except ImportError:
        # QualityConfig not available — fall back to file-based persistence
        import json
        from pathlib import Path
        config_path = Path(__file__).parent.parent.parent.parent / ".cd-agency-quality.json"
        existing = {}
        if config_path.exists():
            with open(config_path) as f:
                existing = json.load(f)
        existing.update(thresholds)
        with open(config_path, "w") as f:
            json.dump(existing, f, indent=2)
        return {"status": "updated", "thresholds": existing}
    except Exception as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to save thresholds: {exc}")

@router.get("/council/status")
async def council_status():
    try:
        from runtime.council_config import CouncilConfig
        config = CouncilConfig.from_config()
        return {
            "enabled": config.enabled,
            "min_models": config.min_models,
            "consensus_method": config.consensus_method,
            "trigger_conditions": config.trigger_conditions,
        }
    except Exception:
        return {
            "enabled": False,
            "min_models": 2,
            "consensus_method": "weighted_median",
            "trigger_conditions": [],
        }

@router.put("/council/config")
async def update_council_config(body: dict[str, Any]):
    """Update council configuration."""
    try:
        from runtime.council_config import CouncilConfig
        config = CouncilConfig.from_config()
        if "enabled" in body:
            config.enabled = body["enabled"]
        if "min_models" in body:
            config.min_models = body["min_models"]
        if "consensus_method" in body:
            config.consensus_method = body["consensus_method"]
        if "trigger_conditions" in body:
            config.trigger_conditions = body["trigger_conditions"]
        config.save()
        return {"status": "ok"}
    except ImportError:
        # Fallback: save to JSON file
        import json
        config_path = Path(".cd-agency-council.json")
        existing = {}
        if config_path.exists():
            existing = json.loads(config_path.read_text())
        existing.update(body)
        config_path.write_text(json.dumps(existing, indent=2))
        return {"status": "ok"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "ok", "version": "2.0.0"}
