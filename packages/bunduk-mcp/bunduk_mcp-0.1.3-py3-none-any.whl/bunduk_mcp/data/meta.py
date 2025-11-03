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
    """Parse a CSV metadata file and return structured metadata."""
    metadata = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Extract basic metadata
                if 'source' in row:
                    source = row['source']
                    metadata[source] = {
                        'description': row.get('description', ''),
                        'license': row.get('license', ''),
                        'url_template': row.get('url_template', ''),
                        'attribution': row.get('attribution', ''),
                    }
    except Exception as e:
        print(f"Error parsing meta file {file_path}: {e}")

    return metadata


def load_biogref_meta(references_dir: str) -> Dict[str, Any]:
    """Load biographical reference metadata."""
    meta_file = Path(references_dir) / "biogref-meta.csv"
    if not meta_file.exists():
        return {}
    return parse_meta_file(str(meta_file))


def load_textref_meta(references_dir: str) -> Dict[str, Any]:
    """Load textual reference metadata."""
    meta_files = list(Path(references_dir).glob("textref*-meta.csv"))
    all_meta = {}

    for meta_file in meta_files:
        source_meta = parse_meta_file(str(meta_file))
        all_meta.update(source_meta)

    return all_meta


def extract_resource_links(text: str) -> list[str]:
    """Extract resource links from text using regex patterns."""
    # Pattern to match resource URLs like biogref://source/person/id
    pattern = r'(biogref|textref)://([^/]+)/([^/]+)/([^/\s]+)'
    return re.findall(pattern, text)