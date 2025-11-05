from __future__ import annotations

from typing import Any, List

from .schemas import AnnotationSpan, DisambigExplanation


def to_int(v: Any):
    try:
        if v in (None, "", "0"):
            return None
        return int(str(v))
    except Exception:
        return None


def to_bool(v: Any):
    if v is None:
        return None
    s = str(v).strip().lower()
    if s in ("1", "y", "yes", "true", "t"):
        return True
    if s in ("0", "n", "no", "false", "f"):
        return False
    return None


def score_confidence(delta_top_second: float) -> str:
    if delta_top_second >= 3:
        return "high"
    if delta_top_second >= 1:
        return "medium"
    return "low"


def person_score(row: dict, context: dict, source: str) -> List[DisambigExplanation]:
    expl: List[DisambigExplanation] = []
    # Dynasty
    ctx_dyns = {d for d in (context.get("dynastyTokens") or [])}
    row_dyn = (row.get("dynasty") or "").strip()
    if row_dyn and ctx_dyns:
        if row_dyn in ctx_dyns:
            expl.append(DisambigExplanation(feature="dynasty", contribution=3, note=row_dyn))
        else:
            expl.append(DisambigExplanation(feature="dynasty_mismatch", contribution=-2, note=row_dyn))
    # Year overlap
    ctx_year = context.get("year")
    by = to_int(row.get("born_year"))
    dy = to_int(row.get("died_year"))
    if ctx_year is not None and (by is not None or dy is not None):
        if by is None or dy is None:
            if by is not None and ctx_year >= by - 25:
                expl.append(DisambigExplanation(feature="year_partial", contribution=1))
        else:
            if by <= ctx_year <= dy:
                expl.append(DisambigExplanation(feature="year_overlap", contribution=3))
            elif (by - 25) <= ctx_year <= (dy + 25):
                expl.append(DisambigExplanation(feature="year_near", contribution=1))
            else:
                expl.append(DisambigExplanation(feature="year_mismatch", contribution=-2))
    # jiguan co-mention
    places = set(context.get("places", []) or [])
    jg = (row.get("jiguan") or "").strip()
    if jg and any(p in jg for p in places):
        expl.append(DisambigExplanation(feature="jiguan_comention", contribution=1, note=jg))
    # completeness
    completeness = sum(1 for k in ("born_year", "died_year", "dynasty", "jiguan") if (row.get(k) or ""))
    if completeness >= 3:
        expl.append(DisambigExplanation(feature="metadata_completeness", contribution=0.5))
    # exact orthography bonus
    surface = context.get("surface")
    if surface and (row.get("person_name") or "") == surface:
        expl.append(DisambigExplanation(feature="exact_name", contribution=0.5))
    return expl


def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def html_build_annotations(text: str, annotations: List[AnnotationSpan]) -> str:
    if not annotations:
        return text
    # Normalize and resolve overlaps
    cleaned: List[AnnotationSpan] = []
    for a in annotations:
        if 0 <= a.start < a.end <= len(text):
            cleaned.append(a)
    # Sort by start asc, length desc (so longer first for same start)
    cleaned.sort(key=lambda a: (a.start, -(a.end - a.start)))
    result_spans: List[AnnotationSpan] = []
    last_end = -1
    for a in cleaned:
        if a.start >= last_end:
            result_spans.append(a)
            last_end = a.end
        else:
            # Overlap: keep the earlier/longer one (already in result_spans)
            continue
    # Build HTML
    parts: List[str] = []
    idx = 0
    for a in result_spans:
        if idx < a.start:
            parts.append(text[idx : a.start])
        span_text = text[a.start : a.end]
        cls = f"ent {a.type}"
        data_link = f' data-link="{a.link}"' if a.link else ""
        title = a.title or a.label
        title_attr = f' title="{html_escape(title)}"' if title else ""
        parts.append(f"<span class=\"{cls}\"{data_link}{title_attr}>{html_escape(span_text)}</span>")
        idx = a.end
    if idx < len(text):
        parts.append(text[idx:])
    return "".join(parts)

