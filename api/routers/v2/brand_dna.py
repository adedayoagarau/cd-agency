from __future__ import annotations
from fastapi import APIRouter, HTTPException
from api.models_v2 import BrandDNAResponse, BrandDNAUpdate, IngestRequest

router = APIRouter(prefix="/api/v2/brand-dna", tags=["brand-dna-v2"])

@router.get("", response_model=BrandDNAResponse)
async def get_brand_dna():
    from runtime.brand_dna import load_brand_dna
    dna = load_brand_dna()
    return BrandDNAResponse(
        voice_patterns=[vars(p) for p in dna.voice_patterns] if dna.voice_patterns else [],
        terminology=[vars(t) for t in dna.terminology] if dna.terminology else [],
        style_rules=[vars(r) for r in dna.style_rules] if dna.style_rules else [],
        sources=dna.source_samples if dna.source_samples else [],
    )

@router.put("")
async def update_brand_dna(update: BrandDNAUpdate):
    from runtime.brand_dna import load_brand_dna, save_brand_dna, VoicePattern, TerminologyEntry, StyleRule
    dna = load_brand_dna()

    if update.voice_patterns is not None:
        dna.voice_patterns = [VoicePattern(**p) for p in update.voice_patterns]
    if update.terminology is not None:
        dna.terminology = [TerminologyEntry(**t) for t in update.terminology]
    if update.style_rules is not None:
        dna.style_rules = [StyleRule(**r) for r in update.style_rules]

    save_brand_dna(dna)
    return {"status": "updated"}

@router.post("/ingest")
async def ingest_brand_content(request: IngestRequest):
    from runtime.brand_dna import BrandDNAProcessor
    from pathlib import Path

    processor = BrandDNAProcessor()

    if request.file_path:
        result = processor.ingest_file(Path(request.file_path))
        return {"patterns_extracted": len(result.voice_patterns) if result else 0}
    elif request.content:
        result = processor.ingest([request.content])
        return {"patterns_extracted": len(result.voice_patterns) if result else 0}
    else:
        raise HTTPException(status_code=400, detail="Provide content or file_path")
