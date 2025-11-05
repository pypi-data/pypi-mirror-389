# MCP Plan: Chinese History Study Assistant (MCP Server, Python SDK)

Status: proposal for your review and consent

## Summary
Build a local-first Model Context Protocol (MCP) server (Python SDK) that exposes your reference datasets as searchable tools and browsable resources so LLM clients can reliably explore people, places, and texts in Chinese history. Online APIs (CBDB, CHGIS TGAZ) are optional enrichments.

Scenarios from `references/senarios.md` are incorporated below. The plan now maps tools and prompts directly to your three desired outputs.

## Goals
- Unify core study tasks around three pillars: People, Places, Texts.
- Provide fast, offline lookup over your CSV snapshots; add online API enrichment when available.
- Return structured results (validated via Pydantic) for dependable downstream use by LLMs.
- Keep implementation simple: start with CSV loaders + FastMCP; evolve to DuckDB/SQLite only if needed.

## Data Sources (from `references/`)
- Biographical references (BiogRef schema: `references/biogref-schema.csv`):
  - CBDB: `biogref-cbdb-data.csv`, meta `biogref-cbdb-meta.csv`
  - ctext: `biogref-ctext-data.csv`, meta `biogref-ctext-meta.csv`
  - DDBC: `biogref-ddbc-data.csv`, meta `biogref-ddbc-meta.csv`
  - DNB (Academia Sinica): `biogref-dnb-data.csv`, meta `biogref-dnb-meta.csv`
- Textual references (TextRef schema):
  - CBETA: `textref-cbeta.csv`, meta `textref-cbeta-meta.csv`
  - ctext catalog: `textref-ctext-catalog.csv`, meta `textref-ctext-meta.csv`
  - Kanripo: `textref-kanripo.csv`, meta `textref-kanripo-meta.csv`
- External reference docs:
  - CBDB API snapshot: `references/cbdb-api.md`
  - CHGIS Temporal Gazetteer (TGAZ): `references/chgis-tgw.md`

## Server Design (Python MCP SDK)
We’ll use the official MCP Python SDK with FastMCP for concise registration of resources and tools.

### Resources (read-only URIs)
Expose file-backed and dynamic resources so clients can browse and fetch by URI.
- biogref://{source}/person/{person_id}
  - Reads from corresponding `biogref-<source>-data.csv` and returns a normalized Person JSON.
- textref://{source}/work/{primary_id}
  - Reads from `textref-<source>.csv` rows; returns title/author/flags.
- tgaz://placename{?n,yr,ftyp,p,fmt=json}
  - Proxies CHGIS TGAZ faceted search (when online). Returns raw JSON/XML text.
- Optional: file://references/{name}.csv as convenience static resources.

Each resource will include a stable `displayName` and leverage URI templates for argument completion.

### Tools (search, crosswalk, enrichment)
Structured outputs with Pydantic models to keep LLM interactions robust.
- person.search(name, dynasty?, source?="all") -> list[PersonLite]
  - Fuzzy/exact search across BiogRef CSVs; include source, person_id, name, born_year, died_year, dynasty, jiguan, and resource URL from meta ResourceTemplate.
- person.get(source, person_id) -> Person
  - Fetch and normalize a single record from a chosen source.
- crosswalk.person(name, limit=20) -> list[CrosswalkHit]
  - Aggregate same/similar names across CBDB/ctext/DDBC/DNB with simple scoring.
- text.search(title, author?, source?="all") -> list[TextRefLite]
  - Search TextRef catalogs; return primary_id, title, author, edition, fulltext flags, and resource link.
- place.search(name, year?, feature_type?, parent?, fmt="json") -> CHGISResult
  - Call TGAZ faceted search (online only). If offline, return a clear error with guidance.
- cbdb.person(id | name, format="json") -> Any
  - Thin wrapper around CBDB API for live details (online only) to complement CSV snapshots.

Note: Online tools are optional; the server remains useful fully offline via CSV-backed tools/resources.

### Prompts (optional, for convenience)
- explain.person(source, person_id): Injects normalized Person into a short analysis prompt.
- contextualize.place(query, year?): Summarizes CHGIS results and suggests likely matches.

## Implementation Plan
1) Bootstrap FastMCP server
- Create `src/server.py` using FastMCP; support stdio transport first, SSE later.

2) CSV loaders and registry
- `src/data/loader.py`: lazy loaders for each CSV; small in-memory indices by `person_name` and `primary_id`.
- `src/data/meta.py`: parse per-source meta (ResourceTemplate, License, ProjectLink) to build outbound links.

3) Schemas
- `src/schemas.py`: Pydantic models for Person, PersonLite, CrosswalkHit, TextRefLite, CHGISResult (as raw payload + echo of query).

4) Resources and tools
- Register `@mcp.resource(...)` for biogref/textref/tgaz.
- Register `@mcp.tool()` for search/crosswalk/enrichment functions.
- Validate outputs; return helpful errors for missing IDs or offline-only features.

5) Packaging and run
- `pyproject.toml` with `modelcontextprotocol` dependency; `uv`-friendly.
- CLI entry: `uv run mcp-chinese-history` (stdio). Option flags for SSE (`--port 8000`).

6) Basic tests
- Lightweight unit tests for CSV loaders and search behavior (no heavy framework required initially).

7) Documentation
- Usage instructions, sample queries, limitations, and data licensing notes.

## Client/Transport
- Default: stdio (works with most MCP clients, including code editors).
- Optional: Streamable HTTP (SSE) for browser-hosted clients.

## Constraints and Notes
- Licensing: Respect each source’s license; tools will return source attribution and outbound links.
- Internationalization: Return fields as-is (Chinese where present), plus normalized keys in English.
- Performance: Start simple; introduce DuckDB/SQLite only if CSV scale requires it.

## Consent Checklist (please confirm)
- Scenarios: the primary user tasks (e.g., “find a person across datasets”, “locate a place by name and year”, “discover texts by dynasty/author”).
- Online calls: enable optional live CBDB and CHGIS lookups when network is available.
- Output: default structured JSON responses; optional short explanatory prompts.
- Search behavior: exact + simple fuzzy matching for names/titles.
- Language: preserve Chinese names/fields; English keys and summaries.

## Next Steps
- You confirm/update scenarios and checklist.
- I’ll scaffold the FastMCP server, CSV loaders, schemas, and the initial set of tools/resources.
- We iterate on behavior (matching, ranking, and any crosswalk heuristics) using your feedback.

---

References (Context7 doc snippets consulted)
- MCP Python SDK: servers, tools, resources, resource templates, stdio/SSE transports.
- Examples: simple-tool, simple-resource, prompts, streamable HTTP.

## Scenario Mapping (from references/senarios.md)

### Scenario 1 — Punctuate, extract entities, link to refs
- LLM tasks (prompted):
  - Punctuate classical Chinese text.
  - Extract entities with spans: people, places, book titles, dates. Return JSON with types and character offsets.
- MCP tools/resources (server tasks):
  - entity.resolve_people(names[, dynasty, source]) -> list[PersonLite] from BiogRef CSVs with links (use meta ResourceTemplate).
  - entity.resolve_books(titles[, source]) -> list[TextRefLite] from TextRef CSVs with links.
  - place.lookup(name[, yr, ftyp, parent, fmt]) -> CHGIS TGAZ (online) with clear offline fallback.
  - Optional: resources biogref://{source}/person/{person_id}, textref://{source}/work/{primary_id} for direct fetch.
- Output: LLM formats a readable summary with linked references using returned URLs.

### Scenario 2 — Annotated HTML with hover tooltips
- LLM tasks (prompted): use entities + resolved links to decide where to annotate.
- MCP tool (helper):
  - html.build_annotations(text, annotations) -> html
    - Input: text and non-overlapping entity spans with {type, start, end, label, link, meta}.
    - Output: HTML with <span class="ent person|place|book|date" data-link="..." title="...">..</span>.
    - Notes: if spans overlap, server chooses longest-span precedence and logs dropped overlaps.
- Provide a small CSS snippet in docs; client controls actual styling and tooltip behavior.

### Scenario 3 — Bilingual per-sentence + annotation table
- LLM tasks (prompted): split sentences, translate to English, carry entity span indices per sentence.
- MCP helper options:
  - html.build_bilingual_table(sentences, translations, annotations) -> html table (deterministic rendering), or
  - prompts.render_bilingual_table to let the LLM format directly using a template.

## Updated Tools (server)
- person.search(name, dynasty?, source?="all") -> list[PersonLite]
- person.get(source, person_id) -> Person
- crosswalk.person(name, limit=20) -> list[CrosswalkHit]
- text.search(title, author?, source?="all") -> list[TextRefLite]
- place.lookup(name, year?, feature_type?, parent?, fmt="json") -> CHGISResult
- cbdb.person(id | name, format="json") -> Any
- entity.resolve_people(names[], dynasty?, source?="all") -> dict{name: [PersonLite, ...]}
- entity.resolve_books(titles[], source?="all") -> dict{title: [TextRefLite, ...]}
- html.build_annotations(text, annotations[]) -> html (deterministic)
- Optional later: html.build_bilingual_table(...)

## Updated Prompts (client-facing via MCP prompts)
- punctuate.zh-classical: conservative, citation-preserving punctuation.
- extract.entities.zh-classical: return JSON with {type, text, start, end}; strong guidelines for person/place/book/date.
- translate.sentences.zh-en: faithful, concise per-sentence translation.
- render.html.annotations: guidance to merge tool outputs into accessible HTML with tooltips.
- render.html.bilingual_table: rows per sentence with zh, en, entity rows.

## End-to-End Flow Examples
- Scenario 1:
  1) Call prompt punctuate.zh-classical
  2) Call prompt extract.entities.zh-classical -> entities with spans
  3) Call entity.resolve_people/books and place.lookup
  4) LLM formats readable enriched text with links

- Scenario 2:
  1) Steps 1–3 as above
  2) Call html.build_annotations(text, annotations)
  3) LLM returns final HTML with CSS hint and data-link attributes

- Scenario 3:
  1) Steps 1–3 as above
  2) Call translate.sentences.zh-en prompt
  3) Either call html.build_bilingual_table(...) or render via prompt

## Notes on Linking
- Use each source’s Meta `ResourceTemplate` to construct outbound links (e.g., CBDB person pages).
- Always include `source`, `id`, `display`, `link`, and `license` in results for attribution.

## Constraints Update
- TGAZ and CBDB live calls depend on network availability; offline mode returns actionable error + how to retry.
- Entity spans must be non-overlapping for deterministic HTML tools; conflicts are reported with choices made.

## Automated Dataset Updates (biogref/textref)

Yes — we can automate checking, downloading, and hot-updating the MCP using the DataURL fields in your meta CSVs and timestamps from the import pages.

Design overview
- Metadata sources:
  - BiogRef meta CSVs: `references/biogref-*-meta.csv` (contain `DataURL`, `MetaURL`, `ResourceTemplate`).
  - TextRef meta CSVs: `references/textref-*-meta.csv`.
  - Import pages: `references/biogref-mm-import.md`, `references/textref-mm-import.md` (human-readable timestamps for context).
- Network behavior:
  - Use HTTP HEAD with conditional headers (If-None-Match/If-Modified-Since) to detect changes via ETag or Last-Modified.
  - On change, stream-download to a temp file, verify CSV header conformity, compute sha256, atomically swap the active file, then trigger in-memory reload.
- Storage layout:
  - `data/cache/{family}/{source}/` (e.g., `data/cache/biogref/cbdb/`) with versioned files `data-YYYYmmdd-HHMMSS.csv`.
  - `data/active/{family}/{source}.csv` is a symlink or copy to the latest.
  - `data/manifest.json` records source, url, etag/last_modified, sha256, bytes, downloaded_at, active_version.
- Hot reload:
  - After a successful sync, rebuild the in-memory indices and replace references in the registry without server restart.
  - Reads use `data/active/...` so lookup is consistent across reload boundaries.
- Retention:
  - Keep the last N versions per source (configurable); delete older to save space.

MCP tools for automation
- dataset.list() -> list active datasets with version, size, etag/last_modified, downloaded_at.
- dataset.check_updates(sources?[], family?="all") -> report which remote CSVs changed (no download).
- dataset.sync(sources?[], family?="all", force=false) -> fetch and activate changed datasets.
- dataset.reload() -> force rebuild indices from active files (no download).
- dataset.verify(source) -> recompute sha256 and header conformity for the active file.

Scheduling options
- Manual by tools: call `dataset.check_updates` and `dataset.sync` on demand.
- On start: check and sync if older than X hours (configurable env var `SYNC_MAX_AGE_HOURS`, default 24).
- Periodic background task: `--auto-sync 3600` to check hourly (SSE or stdio both fine). Safe to disable.

Validation and safety
- CSV header validation against BiogRef/TextRef schemas (e.g., `references/biogref-schema.csv`, textref schema URLs in meta). Mismatch -> abort activation, keep previous version.
- Atomic writes: download to `*.tmp`, then rename to final; update manifest, then swap active symlink.
- Timeouts and backoff on network errors; clear errors returned in tool responses.
- Respect licenses: include `License` from meta in manifest and tool outputs.

Config
- `config/sources.yaml` (optional) to override DataURLs, disable sources, set retention, and schedule.
- Env vars: `SYNC_MAX_AGE_HOURS`, `SYNC_RETENTION`, `HTTP_TIMEOUT`, `HTTP_USER_AGENT`.

Implementation notes
- Use `httpx` (async) with conditional requests and streaming.
- Compute sha256 incrementally while streaming; verify line endings and UTF-8.
- For DNB files with BOM, normalize during load (don’t mutate source file).
- Expose progress via tool result fields and log notifications when supported.

## Disambiguation Strategy (people and places)

Goal: deterministically rank candidates sharing the same surface name using lightweight, explainable features. Expose results with scores and rationale; allow user overrides and cache selections for repeatability.

Inputs available
- People: `person_name`, `born_year`, `died_year`, `dynasty`, `jiguan`, `source` (CBDB/ctext/DDBC/DNB).
- Places (TGAZ): name `n`, `yr` range, `ftyp` (e.g., xian, zhou), parent `p`, canonical ID.
- Context (from LLM extraction):
  - Document/segment time hints: explicit years, reign periods, dynasty tokens (e.g., 宋, 明, 清).
  - Co-mentioned places and persons.
  - Optional: document metadata (work title, author) if known.

Feature scoring (people)
- Dynasty match (exact token match): +3; unknown dynasty: 0; mismatch: −2.
- Time compatibility (if context year or range known):
  - Overlaps life span: +3; adjacent within 25y: +1; otherwise: −2.
- Ancestral home `jiguan` co-mentions: if any place in text resolves to same prefecture/county: +1.
- Cross-source support: candidate appears in ≥2 sources: +1.
- Name variant normalization (later): handle trivial variants (e.g., whitespace, rare/simplified variants) +1.
- Tie-breakers: more complete metadata (has years/dynasty/jiguan) +0.5; exact-orthography match +0.5.

Feature scoring (places)
- Year filter: candidate exists at `yr` (from context or text) +3; near miss (±25y) +1; mismatch −2.
- Feature type `ftyp` match (e.g., xian/zhou/jun): +2; mismatch −1.
- Parent `p` match (if known or inferred from co-mentions): +2; mismatch −1.
- Frequency: placename appears multiple times in text +1 for consistent choice.
- Crosswalk: if candidate has multiple spellings mapping to same canonical ID (TGAZ), +1.

Outputs
- Return top-K ranked candidates with:
  - `score`, `explanations` (feature->contribution), `normalized_name`, `source`, `id`, `link`, `lifespan`/`years` (where applicable), and `confidence` bucket: high (Δ≥3), medium (Δ in [1,3)), low (Δ<1).
- If low confidence or near-tie, include `needs_user_choice=true` and present top 3.

MCP tools (disambiguation)
- disambig.person(name, context, k=5) -> DisambigResult[Person]
  - `context`: {years?: [start,end] | year?, dynastyTokens?: string[], places?: string[], docId?: string}
- disambig.place(name, context, k=5) -> DisambigResult[Place]
  - `context`: {year?, featureType?, parent?, placesInText?: string[], docId?: string}
- disambig.apply_override(docId, mentionKey, chosen: {source,id}) -> void
  - Persist user choice for a document/session to `disambig/overrides.json`.
- disambig.get_override(docId, mentionKey) -> {source,id} | null

Overrides and caching
- `disambig/overrides.json` stores per-document selections keyed by a stable `mentionKey` (e.g., sha1 of surface form + start/end indices).
- On resolve, server checks override first; if present, returns chosen candidate with `origin="override"` and sets `confidence="locked"`.
- Provide a simple retention/cleanup tool or allow doc-level purge.

Workflow integration
1) LLM punctuates and extracts entities with spans and context hints (Scenario 1).
2) Call `disambig.person`/`disambig.place` with that context.
3) If `needs_user_choice`, present top 3 with reasons; after user picks, call `disambig.apply_override`.
4) Downstream tools (`html.build_annotations`) consume chosen links for stable rendering (Scenarios 2–3).

Notes and future improvements
- Expand name normalization with alias tables when available; integrate pinyin/字號/別稱 from richer sources later.
- For places, support multi-hop parents and historical region inference using TGAZ hierarchy traversal when needed.
- Optionally incorporate a lightweight ML re-ranker; keep current rule-based scorer as deterministic fallback.
