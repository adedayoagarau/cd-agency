"""Scrape endpoint — fetch and extract structured content from web pages."""

from __future__ import annotations

from typing import Annotated
from urllib.parse import urljoin, urlparse

from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import verify_api_key
from api.models import ScrapeRequest, ScrapeResponse

router = APIRouter(prefix="/scrape", tags=["scrape"])

MAX_CONTENT_BYTES = 1_048_576  # 1 MB
TIMEOUT_SECONDS = 10


@router.post("", response_model=ScrapeResponse)
async def scrape_url(
    body: ScrapeRequest,
    _auth: Annotated[str | None, Depends(verify_api_key)] = None,
) -> ScrapeResponse:
    """Fetch a web page and extract structured content.

    Extracts title, description, headings, paragraphs, links, images,
    meta tags, and raw text. No API key required (no LLM call).
    """
    try:
        import httpx
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="httpx not installed. Install with: pip install cd-agency[web]",
        )

    # Validate URL
    parsed = urlparse(body.url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="URL must use http or https scheme",
        )

    # Fetch
    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT_SECONDS,
            follow_redirects=True,
            max_redirects=5,
        ) as client:
            response = await client.get(
                body.url,
                headers={"User-Agent": "CD-Agency/0.5.0 (Content Audit)"},
            )
            response.raise_for_status()
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Request timed out after {TIMEOUT_SECONDS}s",
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream returned {exc.response.status_code}",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch URL: {exc}",
        )

    if len(response.content) > MAX_CONTENT_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Page content exceeds 1 MB limit",
        )

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type and "text" not in content_type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Expected HTML content, got: {content_type}",
        )

    # Parse
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="beautifulsoup4 not installed. Install with: pip install cd-agency[web]",
        )

    soup = BeautifulSoup(response.text, "html.parser")
    base_url = body.url

    # Title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # Meta description
    description = ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        description = meta_desc["content"].strip()

    # Headings
    headings = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text = tag.get_text(strip=True)
        if text:
            headings.append(f"{tag.name}: {text}")

    # Paragraphs
    paragraphs = []
    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text and len(text) > 10:
            paragraphs.append(text)

    # Links
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith(("http://", "https://")):
            links.append(href)
        elif href.startswith("/"):
            links.append(urljoin(base_url, href))

    # Images
    images = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        alt = img.get("alt", "")
        if src.startswith(("http://", "https://")):
            images.append(f"{src} | alt: {alt}" if alt else src)
        elif src.startswith("/"):
            full_src = urljoin(base_url, src)
            images.append(f"{full_src} | alt: {alt}" if alt else full_src)

    # Meta tags
    meta = {}
    for tag in soup.find_all("meta"):
        name = tag.get("name") or tag.get("property", "")
        content = tag.get("content", "")
        if name and content:
            meta[name] = content

    # Raw text
    for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
        script_or_style.decompose()
    raw_text = soup.get_text(separator="\n", strip=True)
    # Collapse blank lines
    lines = [line for line in raw_text.splitlines() if line.strip()]
    raw_text = "\n".join(lines[:500])  # Cap at 500 lines

    return ScrapeResponse(
        url=body.url,
        title=title,
        description=description,
        headings=headings[:50],
        paragraphs=paragraphs[:100],
        links=links[:100],
        images=images[:50],
        meta=meta,
        raw_text=raw_text,
    )
