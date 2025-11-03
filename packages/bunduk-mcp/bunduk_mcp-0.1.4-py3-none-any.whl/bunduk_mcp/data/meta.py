"""Metadata parsing for ResourceTemplate links and licensing."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any
import csv
import re


@dataclass
class ResourceTemplate:
    """Template for generating resource URLs with attribution."""
    url_template: str
    attribution: str
    license: Optional[str] = None

    def format_url(self, **kwargs) -> str:
        """Format URL template with provided parameters."""
        return self.url_template.format(**kwargs)


def parse_meta_file(file_path: str) -> Dict[str, Any]:
    """Parse a CSV metadata file with Field/Value structure and return structured metadata."""
    metadata = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            row_data = {}
            for row in reader:
                field = row.get('Field', '')
                value = row.get('Value', '')
                if field and value:
                    row_data[field] = value

            # Extract metadata if we have data
            if row_data:
                # Decode HTML entities in URL template
                url_template = row_data.get('ResourceTemplate', '')
                import html
                url_template = html.unescape(url_template)

                metadata = {
                    'description': row_data.get('LongName', ''),
                    'license': row_data.get('License', ''),
                    'url_template': url_template,
                    'attribution': row_data.get('ShortName', ''),
                    'project_link': row_data.get('ProjectLink', ''),
                }
    except Exception as e:
        print(f"Error parsing meta file {file_path}: {e}")

    return metadata


def load_biogref_meta(references_dir: str) -> Dict[str, Any]:
    """Load biographical reference metadata."""
    references_path = Path(references_dir)
    meta_files = list(references_path.glob("biogref-*-meta.csv"))
    all_meta = {}

    for meta_file in meta_files:
        # Extract source name from filename (e.g., "biogref-dnb-meta.csv" -> "dnb")
        source = meta_file.stem.replace("-meta", "").replace("biogref-", "")
        source_meta = parse_meta_file(str(meta_file))
        if source_meta:
            all_meta[source] = source_meta

    return all_meta


def load_textref_meta(references_dir: str) -> Dict[str, Any]:
    """Load textual reference metadata."""
    references_path = Path(references_dir)
    meta_files = list(references_path.glob("textref*-meta.csv"))
    all_meta = {}

    for meta_file in meta_files:
        # Extract source name from filename (e.g., "textref-cbeta-meta.csv" -> "cbeta")
        source = meta_file.stem.replace("-meta", "").replace("textref-", "")
        source_meta = parse_meta_file(str(meta_file))
        if source_meta:
            all_meta[source] = source_meta

    return all_meta


def extract_resource_links(text: str) -> list[str]:
    """Extract resource links from text using regex patterns."""
    # Pattern to match resource URLs like biogref://source/person/id
    pattern = r'(biogref|textref)://([^/]+)/([^/]+)/([^/\s]+)'
    return re.findall(pattern, text)