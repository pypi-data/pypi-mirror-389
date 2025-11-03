from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


# BiogRef / Person
class PersonLite(BaseModel):
    source: str
    person_id: str
    person_name: str
    born_year: Optional[int] = None
    died_year: Optional[int] = None
    dynasty: Optional[str] = None
    jiguan: Optional[str] = None
    link: Optional[str] = None


class Person(PersonLite):
    primary_id: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


# TextRef / Work
class TextRefLite(BaseModel):
    source: str
    primary_id: str
    title: str
    author: Optional[str] = None
    edition: Optional[str] = None
    fulltext_read: Optional[bool] = None
    fulltext_search: Optional[bool] = None
    fulltext_download: Optional[bool] = None
    image: Optional[bool] = None
    link: Optional[str] = None


# Place lookup (CHGIS / TGAZ)
class CHGISResult(BaseModel):
    query: Dict[str, Any]
    ok: bool
    payload: Optional[Any] = None
    error: Optional[str] = None


# Disambiguation
class DisambigExplanation(BaseModel):
    feature: str
    contribution: float
    note: Optional[str] = None


class DisambigCandidate(BaseModel):
    score: float
    explanations: List[DisambigExplanation] = Field(default_factory=list)
    confidence: str
    id: str
    source: str
    display: str
    link: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class DisambigResult(BaseModel):
    name: str
    context: Dict[str, Any]
    needs_user_choice: bool
    candidates: List[DisambigCandidate]


# Annotation input for HTML builder
class AnnotationSpan(BaseModel):
    start: int
    end: int
    type: str
    label: str
    link: Optional[str] = None
    title: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


