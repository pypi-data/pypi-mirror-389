"""Data loading and indexing functionality for BiogRef and TextRef datasets."""

import csv
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Set
import logging
try:
    import importlib.resources as importlib_resources
except ImportError:
    # Python < 3.7 fallback
    import importlib_resources
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
        self._package_data_paths: Dict[str, Path] = {}
        self._find_package_data()
        self.load_all()

    def _find_package_data(self) -> None:
        """Find CSV files in package data when installed as a package."""
        try:
            # Try to find data files in the package using importlib.resources
            package_files = []
            try:
                # For Python 3.9+
                if hasattr(importlib_resources, 'files'):
                    package = importlib_resources.files('bunduk_mcp')

                    # Look in references directory
                    try:
                        ref_path = package.joinpath('references')
                        if ref_path.is_dir():
                            ref_files = list(ref_path.rglob('*.csv'))
                            package_files.extend(ref_files)
                            logger.debug(f"Found {len(ref_files)} CSV files in references/")
                    except Exception as e:
                        logger.debug(f"References directory not found: {e}")

                    # Look in data/active directory
                    try:
                        active_path = package.joinpath('data', 'active')
                        if active_path.is_dir():
                            active_files = list(active_path.glob('*.csv'))
                            package_files.extend(active_files)
                            logger.debug(f"Found {len(active_files)} CSV files in data/active/")
                    except Exception as e:
                        logger.debug(f"Data/active directory not found: {e}")

            except (AttributeError, TypeError, ImportError):
                # Fallback for older Python versions using pkg_resources
                try:
                    import pkg_resources

                    # Check references directory
                    try:
                        if pkg_resources.resource_exists('bunduk_mcp', 'references'):
                            ref_files = [
                                Path(pkg_resources.resource_filename('bunduk_mcp', f'references/{f}'))
                                for f in pkg_resources.resource_listdir('bunduk_mcp', 'references')
                                if f.endswith('.csv')
                            ]
                            package_files.extend(ref_files)
                            logger.debug(f"Found {len(ref_files)} CSV files in references/ via pkg_resources")
                    except Exception as e:
                        logger.debug(f"Could not load references via pkg_resources: {e}")

                    # Check data/active directory
                    try:
                        if pkg_resources.resource_exists('bunduk_mcp', 'data/active'):
                            active_files = [
                                Path(pkg_resources.resource_filename('bunduk_mcp', f'data/active/{f}'))
                                for f in pkg_resources.resource_listdir('bunduk_mcp', 'data/active')
                                if f.endswith('.csv')
                            ]
                            package_files.extend(active_files)
                            logger.debug(f"Found {len(active_files)} CSV files in data/active/ via pkg_resources")
                    except Exception as e:
                        logger.debug(f"Could not load data/active via pkg_resources: {e}")

                except ImportError:
                    pass

            # Map package files to their paths - use filename as key for primary lookup
            for file_path in package_files:
                if isinstance(file_path, str):
                    file_path = Path(file_path)

                # Use filename as primary key, but also store full path for reference
                key_name = file_path.name
                self._package_data_paths[key_name] = file_path

                # Also store with relative path for more specific lookups
                try:
                    if 'data/active' in str(file_path) or 'data\\active' in str(file_path):
                        relative_key = f"data/active/{file_path.name}"
                        self._package_data_paths[relative_key] = file_path
                    elif 'references' in str(file_path):
                        relative_key = f"references/{file_path.name}"
                        self._package_data_paths[relative_key] = file_path
                except Exception:
                    pass

            if self._package_data_paths:
                logger.info(f"Found {len(self._package_data_paths)} CSV files in package data")
                for key in sorted(self._package_data_paths.keys()):
                    logger.debug(f"  Package data: {key}")

        except Exception as e:
            logger.warning(f"Could not load package data: {e}")
            self._package_data_paths = {}

    def _resolve_file_path(self, file_path: Path) -> Optional[Path]:
        """Resolve file path, checking package data if local file doesn't exist."""
        # First try the direct path
        if file_path.exists():
            return file_path

        # Try to find in package data by exact filename match first
        package_file = self._package_data_paths.get(file_path.name)
        if package_file and self._package_file_exists(package_file):
            return package_file

        # Try to find by relative path (data/active/filename.csv, references/filename.csv)
        relative_path = file_path.relative_to(Path.cwd()) if file_path.is_absolute() else file_path
        relative_key = str(relative_path)

        package_file = self._package_data_paths.get(relative_key)
        if package_file and self._package_file_exists(package_file):
            return package_file

        # Try to find by partial path matching
        for pkg_key, pkg_path in self._package_data_paths.items():
            if pkg_path.name == file_path.name and self._package_file_exists(pkg_path):
                return pkg_path

        logger.debug(f"Could not resolve file path: {file_path}")
        return None

    def _package_file_exists(self, package_file: Path) -> bool:
        """Check if a package file exists, handling both Path and Traversable objects."""
        try:
            # For importlib.resources Traversable objects
            if hasattr(package_file, 'is_file') and callable(package_file.is_file):
                return package_file.is_file()
            # For regular Path objects
            elif hasattr(package_file, 'exists'):
                return package_file.exists()
            else:
                # Fallback: try to open it
                with open(package_file, 'rb'):
                    return True
        except Exception:
            return False

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

        # If no local files found, try to find expected files in package data
        if not biogref_files and self._package_data_paths:
            logger.debug("No local biogref files found, looking in package data")
            # Look for biogref data files in package data
            expected_files = ["biogref-cbdb-data.csv", "biogref-ctext-data.csv", "biogref-ddbc-data.csv", "biogref-dnb-data.csv"]
            for filename in expected_files:
                if filename in self._package_data_paths:
                    biogref_files.append(Path(filename))

        # Resolve file paths (check package data if local files don't exist)
        resolved_files = []
        for data_file in biogref_files:
            resolved_path = self._resolve_file_path(data_file)
            if resolved_path:
                resolved_files.append(resolved_path)
            else:
                logger.warning(f"Could not find data file: {data_file}")

        biogref_meta = load_biogref_meta(str(self.references_dir))

        for data_file in resolved_files:
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

        # If no local files found, try to find expected files in package data
        if not textref_files and self._package_data_paths:
            logger.debug("No local textref files found, looking in package data")
            # Look for textref data files in package data
            expected_files = ["textref-cbeta.csv", "textref-ctext-catalog.csv", "textref-kanripo.csv"]
            for filename in expected_files:
                if filename in self._package_data_paths:
                    textref_files.append(Path(filename))

        # Resolve file paths (check package data if local files don't exist)
        resolved_files = []
        for data_file in textref_files:
            resolved_path = self._resolve_file_path(data_file)
            if resolved_path:
                resolved_files.append(resolved_path)
            else:
                logger.warning(f"Could not find data file: {data_file}")

        textref_meta = load_textref_meta(str(self.references_dir))

        for data_file in resolved_files:
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

        # Handle both regular files and package traversable objects
        try:
            if hasattr(file_path, 'open') and callable(file_path.open):
                # Package traversable object
                with file_path.open('r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            person_id = row.get('person_id', '')
                            if person_id:
                                persons[person_id] = row
                        except Exception as e:
                            logger.warning(f"Error parsing person row: {e}")
            else:
                # Regular file path
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            person_id = row.get('person_id', '')
                            if person_id:
                                persons[person_id] = row
                        except Exception as e:
                            logger.warning(f"Error parsing person row: {e}")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {}

        return persons

    def _load_textref_file(self, file_path: Path) -> Dict[str, Any]:
        """Load texts from a textual reference CSV file."""
        texts = {}

        # Handle both regular files and package traversable objects
        try:
            if hasattr(file_path, 'open') and callable(file_path.open):
                # Package traversable object
                with file_path.open('r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            primary_id = row.get('primary_id', '')
                            if primary_id:
                                texts[primary_id] = row
                        except Exception as e:
                            logger.warning(f"Error parsing text row: {e}")
            else:
                # Regular file path
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            primary_id = row.get('primary_id', '')
                            if primary_id:
                                texts[primary_id] = row
                        except Exception as e:
                            logger.warning(f"Error parsing text row: {e}")
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {}

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