# Bunduk MCP — Chinese History Study Server

MCP server exposing BiogRef/TextRef CSVs as resources and tools for Chinese history study, with optional live CBDB and CHGIS TGAZ enrichments.

## Quick Start

- Requirements: Python 3.10+
- Data: CSVs are expected under `references/` (already present in this repo).

Install (editable):

```
pip install -e .
```

Run (stdio transport):

```
mcp-chinese-history
```

or

```
python -m bunduk_mcp.server
```

This starts an MCP stdio server suitable for MCP-compatible clients.

## Implemented

- Resources: `biogref://{source}/person/{person_id}`, `textref://{source}/work/{primary_id}`
- Tools: person.search, person.get, crosswalk.person, text.search
- Entity resolution: entity.resolve_people, entity.resolve_books
- Place lookup (TGAZ): place.lookup (online; safe fallback if offline)
- CBDB API thin wrapper: cbdb.person (online; safe fallback if offline)
- Disambiguation: disambig.person (rule-based scoring)
- HTML builder: html.build_annotations (deterministic wrapping with tooltips)
- Dataset management (scaffold): dataset.list, dataset.reload (update/sync stubbed)

## Configuration

- `BUNDUK_MCP_REFERENCES_DIR` — override path to CSVs (default: `references`)
- `BUNDUK_HTTP_TIMEOUT` — HTTP timeout seconds (default: 10)

## Notes

- Network-enriched tools return clear errors when offline; the rest work fully offline using local CSV files.
- CSV BOM is handled; fields are normalized but values preserve Chinese text.
- See `MCP_PLAN.md` for design, scenarios, and roadmap.

