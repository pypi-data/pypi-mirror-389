# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bunduk MCP is a Model Context Protocol (MCP) server for Chinese history study. It provides:

- **Resources**: BiogRef (biographical references) and TextRef (textual references) CSV datasets as searchable resources
- **Tools**: Person/text search, entity resolution, place lookup, disambiguation, and HTML annotation builders
- **Online APIs**: Optional CBDB and CHGIS TGAZ enrichment (with graceful offline fallback)
- **Data Management**: Automated CSV dataset updates from remote sources

## Installation & Setup

```bash
# Install in editable mode
pip install -e .

# Or with uv
uv pip install -e .
```

## Running the Server

```bash
# Run as MCP server (stdio transport)
mcp-chinese-history

# Or directly
python -m bunduk_mcp.server
```

## Development Commands

```bash
# Run tests
pytest

# Run specific test file
pytest tests/test_server.py

# Run with coverage (if available)
pytest --cov=src/bunduk_mcp

# Install development dependencies
pip install -e ".[dev]"
```

## Architecture

### Core Components

- **`src/bunduk_mcp/server.py`**: Main MCP server with FastMCP, registers all resources, tools, and prompts
- **`src/bunduk_mcp/data/loader.py`**: DataRegistry class that loads and indexes BiogRef/TextRef CSV files
- **`src/bunduk_mcp/data/meta.py`**: Metadata parsing for ResourceTemplate links and licensing
- **`src/bunduk_mcp/schemas.py`**: Pydantic models for structured data (Person, TextRefLite, DisambigResult, etc.)
- **`src/bunduk_mcp/util.py`**: Utility functions for scoring, HTML building, and data normalization
- **`src/bunduk_mcp/update.py`**: Dataset synchronization logic for checking/downloading remote CSV updates

### Data Sources

The server works with CSV datasets in the `references/` directory:

- **BiogRef sources**: CBDB, ctext, DDBC, DNB (biographical data)
- **TextRef sources**: CBETA, ctext catalog, Kanripo (textual data)
- **Meta files**: Each dataset has corresponding `-meta.csv` files with licensing and link templates

### MCP Resources

- `biogref://{source}/person/{person_id}` → Person JSON with link attribution
- `textref://{source}/work/{primary_id}` → TextRefLite JSON with fulltext flags

### Key Tools

- **Person search**: `person_search()`, `person_get()`, `crosswalk_person()`
- **Text search**: `text_search()`, `entity_resolve_people()`, `entity_resolve_books()`
- **Enrichment**: `place_lookup()` (CHGIS TGAZ), `cbdb_person()` (CBDB API)
- **Disambiguation**: `disambig_person()`, `disambig_place()` with scoring
- **HTML building**: `html_build_annotations()` for creating annotated HTML
- **Dataset management**: `dataset_list()`, `dataset_reload()`, `dataset_sync()`

### Environment Variables

- `BUNDUK_MCP_REFERENCES_DIR`: Override path to CSV files (default: `references`)
- `BUNDUK_HTTP_TIMEOUT`: HTTP timeout for external API calls (default: 10 seconds)

## Testing Strategy

The test suite covers:
- Data loading and indexing functionality
- CSV parsing with BOM handling
- Person and text search behavior
- Disambiguation scoring logic
- Dataset update mechanisms

Tests use lightweight pytest framework without heavy dependencies.

## Network Behavior

The server is designed to be **offline-first**:
- All core functionality works with local CSV files
- Online tools (`place_lookup`, `cbdb_person`) return clear errors when unavailable
- Dataset sync tools fetch updates but maintain graceful fallbacks