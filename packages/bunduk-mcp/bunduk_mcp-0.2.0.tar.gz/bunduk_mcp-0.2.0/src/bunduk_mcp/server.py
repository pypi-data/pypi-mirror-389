from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

from .data.loader import DataRegistry
from .update import check_updates as updater_check_updates, sync as updater_sync, get_paths
from .schemas import (
    AnnotationSpan,
    CHGISResult,
    DisambigCandidate,
    DisambigExplanation,
    DisambigResult,
    Person,
    PersonLite,
    TextRefLite,
)
from .util import (
    to_int,
    to_bool,
    score_confidence,
    person_score,
    html_build_annotations as html_build_annotations_impl,
    html_escape as html_escape_impl,
)


mcp = FastMCP("Chinese History MCP")

# Global registry variable
_registry = None

def get_registry():
    """Get the global DataRegistry instance, initializing if necessary."""
    global _registry
    if _registry is None or not hasattr(_registry, 'biogref') or not _registry.biogref:
        _paths = get_paths()
        _registry = DataRegistry(active_dir=_paths.active_dir)
    return _registry


# -------------- Resources --------------

# Resource for individual person data (processed JSON, not raw CSV)
@mcp.resource("data://persons/{source}/{person_id}", mime_type="application/json")
def get_person_resource(source: str, person_id: str) -> str:
    """Get processed person data as JSON resource.

    This follows MCP best practices by:
    - Using standard data:// URI scheme
    - Returning processed data (not raw CSV)
    - Providing structured JSON with proper MIME type
    """
    registry = get_registry()
    src = registry.biogref.get(source)
    if not src:
        raise ValueError(f"Unknown biogref source: {source}")

    row = src.by_id.get(person_id)
    if not row:
        raise ValueError(f"Person not found in {source}: {person_id}")

    link = registry.make_person_link(source, row)
    result = Person(
        source=source,
        person_id=str(row.get("person_id", "")),
        person_name=str(row.get("person_name", "")),
        born_year=to_int(row.get("born_year")),
        died_year=to_int(row.get("died_year")),
        dynasty=row.get("dynasty") or None,
        jiguan=row.get("jiguan") or None,
        link=link,
        primary_id=row.get("primary_id"),
        meta={"row": row},
    )

    return result.model_dump_json(ensure_ascii=False)


# Resource for individual text/work data (processed JSON, not raw CSV)
@mcp.resource("data://texts/{source}/{primary_id}", mime_type="application/json")
def get_text_resource(source: str, primary_id: str) -> str:
    """Get processed text data as JSON resource.

    This follows MCP best practices by:
    - Using standard data:// URI scheme
    - Returning processed data (not raw CSV)
    - Providing structured JSON with proper MIME type
    """
    registry = get_registry()
    src = registry.textref.get(source)
    if not src:
        raise ValueError(f"Unknown textref source: {source}")

    row = src.by_primary.get(primary_id)
    if not row:
        raise ValueError(f"Work not found in {source}: {primary_id}")

    link = registry.make_textref_link(source, row)
    result = TextRefLite(
        source=source,
        primary_id=primary_id,
        title=row.get("title", ""),
        author=row.get("author") or None,
        edition=row.get("edition") or None,
        fulltext_read=to_bool(row.get("fulltext_read")),
        fulltext_search=to_bool(row.get("fulltext_search")),
        fulltext_download=to_bool(row.get("fulltext_download")),
        image=to_bool(row.get("image")),
        link=link,
    )

    return result.model_dump_json(ensure_ascii=False)


# Resource for available data sources (metadata)
@mcp.resource("data://sources", mime_type="application/json")
def get_sources_resource() -> str:
    """Get available data sources as JSON resource.

    This follows MCP best practices by:
    - Using standard data:// URI scheme
    - Providing metadata about available sources
    - Allowing clients to discover available data
    """
    registry = get_registry()
    sources_info = {
        "biogref_sources": list(registry.biogref.keys()),
        "textref_sources": list(registry.textref.keys()),
        "references_dir": str(registry.references_dir)
    }

    import json
    return json.dumps(sources_info, ensure_ascii=False, indent=2)


# -------------- Tools: People --------------

@mcp.tool()
def person_search(name: str, dynasty: Optional[str] = None, source: str = "all") -> List[PersonLite]:
    """Search people by name across BiogRef sources.

    - name: surface string to match (exact or substring)
    - dynasty: optional filter
    - source: 'all' or a specific biogref source (e.g., 'cbdb', 'ctext', 'ddbc', 'dnb')
    """
    registry = get_registry()
    sources = registry.biogref.keys() if source == "all" else [source]
    results: List[PersonLite] = []
    for s in sources:
        src = registry.biogref.get(s)
        if not src:
            continue
        # Search through all persons in the source
        for r in src.by_id.values():
            nm = r.get("person_name", "")
            if name in nm:
                if dynasty and (r.get("dynasty") or "") != dynasty:
                    continue
                link = registry.make_person_link(s, r)
                results.append(
                    PersonLite(
                        source=s,
                        person_id=str(r.get("person_id", "")),
                        person_name=nm,
                        born_year=to_int(r.get("born_year")),
                        died_year=to_int(r.get("died_year")),
                        dynasty=r.get("dynasty") or None,
                        jiguan=r.get("jiguan") or None,
                        link=link,
                    )
                )
    return results


@mcp.tool()
def person_get(source: str, person_id: str) -> Person:
    registry = get_registry()
    src = registry.biogref.get(source)
    if not src:
        raise ValueError(f"Unknown biogref source: {source}")
    row = src.by_id.get(person_id)
    if not row:
        raise ValueError(f"Person not found in {source}: {person_id}")
    link = registry.make_person_link(source, row)
    return Person(
        source=source,
        person_id=person_id,
        person_name=row.get("person_name", ""),
        born_year=to_int(row.get("born_year")),
        died_year=to_int(row.get("died_year")),
        dynasty=row.get("dynasty") or None,
        jiguan=row.get("jiguan") or None,
        link=link,
        primary_id=row.get("primary_id"),
        meta={"row": row},
    )


@mcp.tool()
def crosswalk_person(name: str, limit: int = 20) -> List[PersonLite]:
    """Aggregate people with the same/similar names across sources.

    Simple union by substring match; caller can pass to disambiguation tool for ranking.
    """
    hits = person_search(name=name, dynasty=None, source="all")
    # Deduplicate by (source, person_id)
    seen: set[tuple[str, str]] = set()
    unique: List[PersonLite] = []
    for h in hits:
        key = (h.source, h.person_id)
        if key in seen:
            continue
        seen.add(key)
        unique.append(h)
        if len(unique) >= limit:
            break
    return unique


# -------------- Tools: Texts --------------

@mcp.tool()
def text_search(title: str, author: Optional[str] = None, source: str = "all") -> List[TextRefLite]:
    registry = get_registry()
    sources = registry.textref.keys() if source == "all" else [source]
    results: List[TextRefLite] = []
    for s in sources:
        src = registry.textref.get(s)
        if not src:
            continue
        # Search through all texts in the source
        for r in src.by_primary.values():
            tl = r.get("title", "")
            if title in tl:
                if author and (r.get("author") or "") != author:
                    continue
                link = registry.make_textref_link(s, r)
                results.append(
                    TextRefLite(
                        source=s,
                        primary_id=r.get("primary_id", ""),
                        title=tl,
                        author=r.get("author") or None,
                        edition=r.get("edition") or None,
                        fulltext_read=to_bool(r.get("fulltext_read")),
                        fulltext_search=to_bool(r.get("fulltext_search")),
                        fulltext_download=to_bool(r.get("fulltext_download")),
                        image=to_bool(r.get("image")),
                        link=link,
                    )
                )
    return results


@mcp.tool()
def entity_resolve_people(names: List[str], dynasty: Optional[str] = None, source: str = "all") -> Dict[str, List[PersonLite]]:
    out: Dict[str, List[PersonLite]] = {}
    for n in names:
        out[n] = person_search(name=n, dynasty=dynasty, source=source)
    return out


@mcp.tool()
def entity_resolve_books(titles: List[str], source: str = "all") -> Dict[str, List[TextRefLite]]:
    out: Dict[str, List[TextRefLite]] = {}
    for t in titles:
        out[t] = text_search(title=t, author=None, source=source)
    return out


# -------------- Tools: Place / TGAZ and CBDB live --------------

_HTTP_TIMEOUT = float(os.environ.get("BUNDUK_HTTP_TIMEOUT", "10"))


@mcp.tool()
def place_lookup(
    name: str,
    year: Optional[int] = None,
    feature_type: Optional[str] = None,
    parent: Optional[str] = None,
    fmt: str = "json",
) -> CHGISResult:
    """Lookup place via CHGIS TGAZ faceted search. Returns raw payload.

    If network is unavailable, returns ok=False with an error message.
    """
    base = "https://chgis.hudci.org/tgaz/placename"
    params: Dict[str, Any] = {"n": name}
    if year is not None:
        params["yr"] = year
    if feature_type:
        params["ftyp"] = feature_type
    if parent:
        params["p"] = parent
    if fmt:
        params["fmt"] = fmt
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            r = client.get(base, params=params)
            r.raise_for_status()
            payload: Any
            if fmt == "json":
                payload = r.json()
            else:
                payload = r.text
            return CHGISResult(query=params, ok=True, payload=payload)
    except Exception as e:
        return CHGISResult(query=params, ok=False, error=f"TGAZ lookup failed: {e}")


@mcp.tool()
def cbdb_person(id: Optional[str] = None, name: Optional[str] = None, format: str = "json") -> Dict[str, Any]:
    """Thin wrapper around CBDB person API.

    Provide either id or name. Returns raw JSON or text depending on 'format'.
    """
    if not id and not name:
        raise ValueError("Provide 'id' or 'name'")
    base = "https://cbdb.fas.harvard.edu/cbdbapi/person.php"
    params: Dict[str, Any] = {}
    if id:
        params["id"] = id
    if name:
        params["name"] = name
    if format:
        params["o"] = format
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            r = client.get(base, params=params)
            r.raise_for_status()
            if format == "json":
                return {"ok": True, "query": params, "payload": r.json()}
            else:
                return {"ok": True, "query": params, "payload": r.text}
    except Exception as e:
        return {"ok": False, "query": params, "error": f"CBDB request failed: {e}"}


# -------------- Tools: Disambiguation --------------

# replaced by util.to_int/ to_bool/ score_confidence/ person_score


@mcp.tool()
def disambig_person(name: str, context: Dict[str, Any], k: int = 5) -> DisambigResult:
    """Rank candidates sharing the same surface name using simple features.

    context can include: year, dynastyTokens[], places[], surface, docId
    """
    hits = person_search(name=name, dynasty=None, source="all")
    candidates: List[DisambigCandidate] = []
    for h in hits:
        # Recover row for more fields
        registry = get_registry()
        src = registry.biogref.get(h.source)
        if not src:
            continue
        row = src.by_id.get(h.person_id) or {}
        ex = person_score(row, context, h.source)
        total = sum(e.contribution for e in ex)
        candidates.append(
            DisambigCandidate(
                score=float(total),
                explanations=ex,
                confidence="low",  # set later
                id=h.person_id,
                source=h.source,
                display=h.person_name,
                link=h.link,
                extra={
                    "born_year": h.born_year,
                    "died_year": h.died_year,
                    "dynasty": h.dynasty,
                    "jiguan": h.jiguan,
                },
            )
        )
    # Sort and set confidence
    candidates.sort(key=lambda c: c.score, reverse=True)
    if candidates:
        top = candidates[0].score
        second = candidates[1].score if len(candidates) > 1 else top - 0.0
        delta = top - second
        conf = score_confidence(delta)
        candidates[0].confidence = conf
        for c in candidates[1:]:
            c.confidence = "low"
    needs_choice = False
    if len(candidates) >= 2:
        delta = candidates[0].score - candidates[1].score
        needs_choice = delta < 1
    return DisambigResult(
        name=name,
        context=context,
        needs_user_choice=needs_choice,
        candidates=candidates[:k],
    )


# -------------- Tools: HTML Builder --------------

def _place_score(result_item: Dict[str, Any], context: Dict[str, Any]) -> List[DisambigExplanation]:
    expl: List[DisambigExplanation] = []
    score = 0.0
    ctx_year = context.get("year")
    # TGAZ result structure may vary; attempt common fields
    years = result_item.get("years") or result_item.get("existYears")
    # feature type
    ftyp_ctx = context.get("featureType")
    ftyp = (result_item.get("ftyp") or result_item.get("featureType") or "").lower()
    if ftyp_ctx and ftyp:
        if ftyp_ctx.lower() == ftyp:
            expl.append(DisambigExplanation(feature="feature_type", contribution=2, note=ftyp))
            score += 2
        else:
            expl.append(DisambigExplanation(feature="feature_type_mismatch", contribution=-1, note=ftyp))
            score -= 1
    # parent
    parent_ctx = context.get("parent")
    parent = (result_item.get("parent") or result_item.get("partOf") or "")
    if parent_ctx and parent:
        if parent_ctx in parent:
            expl.append(DisambigExplanation(feature="parent", contribution=2, note=str(parent)))
            score += 2
        else:
            expl.append(DisambigExplanation(feature="parent_mismatch", contribution=-1))
            score -= 1
    # year compatibility (very approximate due to varying schemas)
    if ctx_year is not None:
        ok = False
        if isinstance(years, dict):
            start = years.get("start")
            end = years.get("end")
            if isinstance(start, int) and isinstance(end, int):
                if start <= ctx_year <= end:
                    ok = True
        if ok:
            expl.append(DisambigExplanation(feature="year_overlap", contribution=3))
            score += 3
        else:
            expl.append(DisambigExplanation(feature="year_unknown_or_mismatch", contribution=0))
    # Save total into first explanation note for transparency (optional)
    return expl


@mcp.tool()
def disambig_place(name: str, context: Dict[str, Any], k: int = 5) -> DisambigResult:
    """Rank place candidates using place_lookup payload and context (year/ftyp/parent)."""
    # Try to fetch candidates via place_lookup with json format
    resp = place_lookup(name=name, year=context.get("year"), feature_type=context.get("featureType"), parent=context.get("parent"), fmt="json")
    candidates: List[DisambigCandidate] = []
    if not resp.ok or not isinstance(resp.payload, (dict, list)):
        return DisambigResult(name=name, context=context, needs_user_choice=True, candidates=[])
    # Normalize payload to list of items
    items: List[Dict[str, Any]]
    if isinstance(resp.payload, list):
        items = resp.payload
    else:
        items = resp.payload.get("results") or resp.payload.get("placenames") or []
    for it in items:
        ex = _place_score(it, context)
        total = sum(e.contribution for e in ex)
        pid = str(it.get("id") or it.get("tgazId") or it.get("uid") or "")
        disp = str(it.get("name") or it.get("display") or name)
        link = None
        # If item includes canonical URLs
        url = it.get("url") or it.get("uri")
        if isinstance(url, str):
            link = url
        candidates.append(
            DisambigCandidate(
                score=float(total),
                explanations=ex,
                confidence="low",
                id=pid,
                source="tgaz",
                display=disp,
                link=link,
                extra={k: it.get(k) for k in ("ftyp", "parent", "years") if k in it},
            )
        )
    candidates.sort(key=lambda c: c.score, reverse=True)
    if candidates:
        top = candidates[0].score
        second = candidates[1].score if len(candidates) > 1 else top - 0.0
        delta = top - second
        conf = _score_confidence(delta)
        candidates[0].confidence = conf
        for c in candidates[1:]:
            c.confidence = "low"
    needs_choice = False
    if len(candidates) >= 2:
        delta = candidates[0].score - candidates[1].score
        needs_choice = delta < 1
    return DisambigResult(name=name, context=context, needs_user_choice=needs_choice, candidates=candidates[:k])

@mcp.tool()
def html_build_annotations(text: str, annotations: List[AnnotationSpan]) -> str:
    """Wrap non-overlapping spans with <span> tags. Conflicts -> longest-span precedence.

    Returns HTML string with spans of the form:
      <span class="ent person" data-link="..." title="...">...</span>
    """
    # Delegate to util implementation (deterministic wrapping)
    return html_build_annotations_impl(text, annotations)


def _html_escape(s: str) -> str:
    return html_escape_impl(s)


# -------------- Tools: Dataset management (scaffold) --------------

@mcp.tool()
def dataset_list() -> Dict[str, Any]:
    """List active datasets from data/active/ and manifest information."""
    registry = get_registry()
    active_dir = registry.data_dir

    # List files in active directory
    files = []
    if os.path.exists(active_dir):
        for name in sorted(os.listdir(active_dir)):
            if name.endswith(".csv"):
                path = os.path.join(active_dir, name)
                try:
                    st = os.stat(path)
                    files.append({"file": name, "bytes": st.st_size, "modified": st.st_mtime})
                except Exception:
                    files.append({"file": name})

    # Get manifest information if available
    manifest_info = {}
    manifest_path = os.path.join(os.path.dirname(active_dir), "manifest.json")
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
                manifest_info = {
                    "last_sync": manifest.get("last_sync"),
                    "version": manifest.get("version"),
                    "created_at": manifest.get("created_at"),
                    "configuration": manifest.get("configuration", {})
                }
        except Exception:
            pass

    return {
        "active_dir": str(active_dir),
        "files": files,
        "biogref_sources": list(registry.biogref.keys()),
        "textref_sources": list(registry.textref.keys()),
        "manifest": manifest_info
    }


@mcp.tool()
def dataset_reload() -> Dict[str, Any]:
    """Reload in-memory indices from current active CSV files."""
    registry = get_registry()
    registry.reload()
    return {"ok": True, "biogref_sources": list(registry.biogref.keys()), "textref_sources": list(registry.textref.keys())}


@mcp.tool()
def dataset_check_updates(family: str = "all", sources: Optional[List[str]] = None) -> Dict[str, Any]:
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            res = updater_check_updates(family=family, sources=sources, client=client)
            return {"ok": True, **res}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@mcp.tool()
def dataset_sync(family: str = "all", sources: Optional[List[str]] = None, force: bool = False) -> Dict[str, Any]:
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
            res = updater_sync(family=family, sources=sources, client=client)
        # Reload registry to pick up new active files
        registry = get_registry()
        registry.reload()
        return {"ok": True, **res, "biogref_sources": list(registry.biogref.keys()), "textref_sources": list(registry.textref.keys())}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# -------------- Entrypoint --------------

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Chinese History MCP Server")
    parser.add_argument("transport", nargs="?", default="stdio", help="Transport: stdio (default)")
    args = parser.parse_args()

    if args.transport != "stdio":
        raise SystemExit("Only stdio transport is scaffolded in this version")

    _run_stdio()


def _run_stdio() -> None:
    # FastMCP handles stdio transport internally
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

# -------------- Prompts --------------

@mcp.prompt(title="punctuate.zh-classical")
def punctuate_zh_classical(text: str, style: str = "conservative") -> str:
    return (
        "You are a careful editor of Classical Chinese.\n"
        "Task: Add punctuation to the provided Classical Chinese text.\n"
        "Constraints:\n"
        f"- Style: {style} (prefer minimal edits; avoid adding particles).\n"
        "- Preserve original orthography; do not modernize or translate.\n"
        "- Keep line breaks; do not merge or split lines unless necessary.\n"
        "Output: Return only the punctuated text.\n\n"
        f"Text:\n{text}\n"
    )


@mcp.prompt(title="extract.entities.zh-classical")
def extract_entities_zh_classical(text: str) -> str:
    return (
        "Extract named entities from Classical Chinese text.\n"
        "Entity types: person, place, book, date.\n"
        "Return JSON with an array 'entities', each item: {type, text, start, end}.\n"
        "- Indices are 0-based [start,end) character offsets over the given input.\n"
        "- Do not overlap spans; prefer longer spans for nested names.\n"
        "- Do not normalize the surface text.\n"
        "Output ONLY JSON.\n\n"
        f"Text:\n{text}\n"
    )


@mcp.prompt(title="translate.sentences.zh-en")
def translate_sentences_zh_en(text: str) -> list[base.Message]:
    return [
        base.UserMessage(
            "You translate Classical Chinese to concise, faithful modern English.\n"
            "Split the text into sentences and translate each sentence.\n"
            "Return JSON with an array 'sentences', items: {zh, en}.\n"
            "Keep ordering; avoid explanation; output ONLY JSON.\n"
        ),
        base.UserMessage(text),
    ]


@mcp.prompt(title="render.html.annotations")
def render_html_annotations_prompt(text: str, annotations_json: str) -> str:
    return (
        "Render annotated HTML.\n"
        "Given original 'text' and 'annotations' (JSON array from entity resolution),\n"
        "wrap spans with <span class=\"ent TYPE\" data-link=\"...\" title=\"...\">..</span>.\n"
        "Avoid overlapping markup; if overlaps present, prefer the longest span.\n"
        "Do not add commentary.\n"
        "Output: standalone HTML fragment with spans only.\n\n"
        f"text=\n{text}\n\nannotations=\n{annotations_json}\n"
    )


@mcp.prompt(title="render.html.bilingual_table")
def render_html_bilingual_table(sentences_json: str, annotations_json: str, title: str = "") -> str:
    return (
        "Render an HTML table with per-sentence Chinese and English, and an entity list.\n"
        "Inputs:\n"
        "- sentences_json: JSON array 'sentences' with {zh, en}.\n"
        "- annotations_json: JSON array 'entities' with {type, text, start, end, link?}.\n"
        "Output: a minimal table with columns: Zh, En.\n"
        "Below the table, include a section 'Entities' listing each unique entity with link if present.\n"
        "No extra prose.\n\n"
        f"Title: {title}\n\n"
        f"sentences=\n{sentences_json}\n\nannotations=\n{annotations_json}\n"
    )
