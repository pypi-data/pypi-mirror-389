"""Data loading and indexing functionality for BiogRef and TextRef datasets."""

import csv
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Set
import logging
from ..schemas import Person, TextRefLite
from .meta import load_biogref_meta, load_textref_meta

logger = logging.getLogger(__name__)


@dataclass
class DataSource:
    """Container for a data source with metadata and indices."""
    by_id: Dict[str, Any]
    by_primary: Dict[str, Any]  # For textref sources
    meta: Dict[str, Any]


class DataRegistry:
    """Registry for loading and indexing BiogRef/TextRef CSV files."""

    def __init__(self, references_dir: Optional[str] = None, active_dir: Optional[str] = None):
        """Initialize the data registry.

        Args:
            references_dir: Path to the references directory containing meta files and schemas
            active_dir: Path to the active data directory containing CSV files
        """
        # Primary data directory: data/active/ (for dynamic CSV data)
        # Secondary: references/ (only for meta files, not CSV data)
        self.data_dir = Path(active_dir or "data/active")
        self.references_dir = Path(references_dir or "references")
        self.biogref: Dict[str, DataSource] = {}
        self.textref: Dict[str, DataSource] = {}
        self._meta_data: Dict[str, Any] = {}
        self.load_all()

    def load_all(self) -> None:
        """Load all available datasets."""
        self._load_biogref_datasets()
        self._load_textref_datasets()

    def _load_biogref_datasets(self) -> None:
        """Load all biographical reference datasets from data/active/."""
        # Try data/active/ first (proper location), fallback to references/ for legacy compatibility
        biogref_files = list(self.data_dir.glob("biogref-*-data.csv"))
        if not biogref_files:
            # Fallback to references/ if no files in data/active/
            biogref_files = list(self.references_dir.glob("biogref-*-data.csv"))

        biogref_meta = load_biogref_meta(str(self.references_dir))

        for data_file in biogref_files:
            source = data_file.stem.replace("-data", "").replace("biogref-", "")
            try:
                rows = self._load_biogref_file(data_file)
                self.biogref[source] = DataSource(
                    by_id=rows,
                    by_primary={},  # Not used for biogref
                    meta=biogref_meta.get(source, {})
                )
                logger.info(f"Loaded {len(rows)} persons from {source} ({data_file.parent.name})")
            except Exception as e:
                logger.error(f"Error loading {data_file}: {e}")

    def _load_textref_datasets(self) -> None:
        """Load all textual reference datasets from data/active/."""
        # Try data/active/ first (proper location), fallback to references/ for legacy compatibility
        textref_files = list(self.data_dir.glob("textref-*.csv"))
        if not textref_files:
            # Fallback to references/ if no files in data/active/
            textref_files = list(self.references_dir.glob("textref*.csv"))

        textref_meta = load_textref_meta(str(self.references_dir))

        for data_file in textref_files:
            # Extract source name from filename
            if data_file.name.startswith("textref-"):
                source = data_file.stem.replace("-data", "").replace("textref-", "")
            else:
                source = data_file.stem.replace("textref", "")

            try:
                rows = self._load_textref_file(data_file)
                self.textref[source] = DataSource(
                    by_id={},  # Not used for textref
                    by_primary=rows,
                    meta=textref_meta.get(source, {})
                )
                logger.info(f"Loaded {len(rows)} texts from {source} ({data_file.parent.name})")
            except Exception as e:
                logger.error(f"Error loading {data_file}: {e}")

    def _load_biogref_file(self, file_path: Path) -> Dict[str, Any]:
        """Load persons from a biographical reference CSV file."""
        persons = {}

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    person_id = row.get('person_id', '')
                    if person_id:
                        persons[person_id] = row
                except Exception as e:
                    logger.warning(f"Error parsing person row: {e}")

        return persons

    def _load_textref_file(self, file_path: Path) -> Dict[str, Any]:
        """Load texts from a textual reference CSV file."""
        texts = {}

        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    primary_id = row.get('primary_id', '')
                    if primary_id:
                        texts[primary_id] = row
                except Exception as e:
                    logger.warning(f"Error parsing text row: {e}")

        return texts

    def make_person_link(self, source: str, row: Dict[str, Any]) -> Optional[str]:
        """Generate a link for a person record."""
        meta = self.biogref.get(source, {}).meta
        url_template = meta.get("url_template")

        if not url_template:
            return None

        try:
            return url_template.format(person_id=row.get("person_id", ""))
        except (KeyError, ValueError):
            return None

    def make_textref_link(self, source: str, row: Dict[str, Any]) -> Optional[str]:
        """Generate a link for a text reference record."""
        meta = self.textref.get(source, {}).meta
        url_template = meta.get("url_template")

        if not url_template:
            return None

        try:
            return url_template.format(primary_id=row.get("primary_id", ""))
        except (KeyError, ValueError):
            return None

    def reload(self) -> None:
        """Reload all datasets from data/active/."""
        self.biogref.clear()
        self.textref.clear()
        self._meta_data.clear()
        self.load_all()