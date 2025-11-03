from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx

from .data.meta import load_biogref_meta, load_textref_meta


@dataclass
class Paths:
    base_dir: str
    cache_dir: str
    active_dir: str
    manifest_path: str


def get_paths(data_dir: Optional[str] = None) -> Paths:
    base = data_dir or os.environ.get("BUNDUK_MCP_DATA_DIR", "data")
    cache = os.path.join(base, "cache")
    active = os.path.join(base, "active")
    manifest = os.path.join(base, "manifest.json")
    return Paths(base, cache, active, manifest)


def ensure_dirs(paths: Paths) -> None:
    os.makedirs(paths.cache_dir, exist_ok=True)
    os.makedirs(paths.active_dir, exist_ok=True)
    os.makedirs(paths.base_dir, exist_ok=True)


def load_manifest(paths: Paths) -> Dict[str, Any]:
    if not os.path.exists(paths.manifest_path):
        return {"sources": {}}
    with open(paths.manifest_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {"sources": {}}


def save_manifest(paths: Paths, manifest: Dict[str, Any]) -> None:
    tmp = paths.manifest_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    os.replace(tmp, paths.manifest_path)


def enumerate_sources(references_dir: Optional[str] = None) -> List[Dict[str, str]]:
    refs = references_dir or os.environ.get("BUNDUK_MCP_REFERENCES_DIR", "references")
    biog = load_biogref_meta(refs)
    text = load_textref_meta(refs)
    items: List[Dict[str, str]] = []
    for src, meta in biog.items():
        url = meta.get("DataURL")
        if url:
            items.append({"family": "biogref", "source": src, "url": url})
    for src, meta in text.items():
        url = meta.get("DataURL")
        if url:
            items.append({"family": "textref", "source": src, "url": url})
    return items


def _manifest_key(family: str, source: str) -> str:
    return f"{family}:{source}"


def _target_filenames(paths: Paths, family: str, source: str, ts: str) -> Tuple[str, str]:
    if family == "biogref":
        cache_name = f"biogref-{source}-data-{ts}.csv"
        active_name = f"biogref-{source}-data.csv"
    else:
        cache_name = f"textref-{source}-{ts}.csv"
        active_name = f"textref-{source}.csv"
    return (
        os.path.join(paths.cache_dir, family, source, cache_name),
        os.path.join(paths.active_dir, active_name),
    )


def _ensure_family_dirs(paths: Paths, family: str, source: str) -> None:
    os.makedirs(os.path.join(paths.cache_dir, family, source), exist_ok=True)
    os.makedirs(paths.active_dir, exist_ok=True)


def _validate_csv_header(family: str, csv_path: str) -> Tuple[bool, str]:
    try:
        with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            header_lower = {h.strip().lower() for h in header}
        if family == "biogref":
            required = {"primary_id", "person_id", "person_name"}
        else:
            required = {"primary_id", "title"}
        missing = required - header_lower
        if missing:
            return False, f"Missing columns: {', '.join(sorted(missing))}"
        return True, ""
    except Exception as e:
        return False, f"Validation error: {e}"


def check_updates(
    family: str = "all",
    sources: Optional[List[str]] = None,
    *,
    data_dir: Optional[str] = None,
    references_dir: Optional[str] = None,
    client: Optional[httpx.Client] = None,
) -> Dict[str, Any]:
    paths = get_paths(data_dir)
    manifest = load_manifest(paths)
    items = enumerate_sources(references_dir)
    if family != "all":
        items = [i for i in items if i["family"] == family]
    if sources:
        wanted = set(sources)
        items = [i for i in items if i["source"] in wanted]

    results: List[Dict[str, Any]] = []
    use_client = client or httpx.Client()
    try:
        for it in items:
            key = _manifest_key(it["family"], it["source"])
            entry = manifest.get("sources", {}).get(key, {})
            headers: Dict[str, str] = {}
            if entry.get("etag"):
                headers["If-None-Match"] = entry["etag"]
            if entry.get("last_modified"):
                headers["If-Modified-Since"] = entry["last_modified"]
            status = None
            etag = None
            last_mod = None
            changed = True
            try:
                r = use_client.head(it["url"], headers=headers, follow_redirects=True)
                status = r.status_code
                etag = r.headers.get("ETag")
                last_mod = r.headers.get("Last-Modified")
                if status == 304:
                    changed = False
                elif etag and entry.get("etag") and etag == entry.get("etag"):
                    changed = False
            except Exception as e:
                results.append({"family": it["family"], "source": it["source"], "ok": False, "error": str(e)})
                continue
            results.append({
                "family": it["family"],
                "source": it["source"],
                "ok": True,
                "status": status,
                "changed": changed,
                "etag": etag,
                "last_modified": last_mod,
            })
    finally:
        if client is None:
            use_client.close()
    return {"results": results}


def sync(
    family: str = "all",
    sources: Optional[List[str]] = None,
    *,
    data_dir: Optional[str] = None,
    references_dir: Optional[str] = None,
    client: Optional[httpx.Client] = None,
    fetcher: Optional[Any] = None,
) -> Dict[str, Any]:
    """Download changed datasets, validate, write cache and activate. Returns summary.

    `fetcher(url, dest_tmp)` may be provided for testing; it should write the file to dest_tmp and
    return a dict with optional 'etag' and 'last_modified'.
    """
    paths = get_paths(data_dir)
    ensure_dirs(paths)
    manifest = load_manifest(paths)
    items = enumerate_sources(references_dir)
    if family != "all":
        items = [i for i in items if i["family"] == family]
    if sources:
        wanted = set(sources)
        items = [i for i in items if i["source"] in wanted]

    now = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    use_client = client or httpx.Client()
    out: List[Dict[str, Any]] = []
    try:
        for it in items:
            fam = it["family"]
            src = it["source"]
            url = it["url"]
            key = _manifest_key(fam, src)
            _ensure_family_dirs(paths, fam, src)
            cache_path, active_path = _target_filenames(paths, fam, src, now)
            tmp_path = cache_path + ".tmp"

            # Fetch
            info: Dict[str, Any] = {}
            try:
                if fetcher:
                    info = fetcher(url, tmp_path) or {}
                else:
                    with use_client.stream("GET", url, follow_redirects=True) as r:
                        r.raise_for_status()
                        with open(tmp_path, "wb") as f:
                            for chunk in r.iter_bytes():
                                f.write(chunk)
                    info = {"etag": r.headers.get("ETag"), "last_modified": r.headers.get("Last-Modified")}
            except Exception as e:
                out.append({"family": fam, "source": src, "ok": False, "error": f"download failed: {e}"})
                # cleanup
                try:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                except Exception:
                    pass
                continue

            # Validate header
            valid, reason = _validate_csv_header(fam, tmp_path)
            if not valid:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
                out.append({"family": fam, "source": src, "ok": False, "error": f"validation failed: {reason}"})
                continue

            # Compute sha256
            sha256 = hashlib.sha256()
            with open(tmp_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            digest = sha256.hexdigest()

            # Move to cache and activate
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            os.replace(tmp_path, cache_path)
            # Copy to active (atomic replace)
            os.makedirs(os.path.dirname(active_path), exist_ok=True)
            # Use copyfileobj for simplicity
            with open(cache_path, "rb") as src_f, open(active_path + ".tmp", "wb") as dst_f:
                shutil.copyfileobj(src_f, dst_f)
            os.replace(active_path + ".tmp", active_path)

            # Update manifest
            manifest.setdefault("sources", {})[key] = {
                "family": fam,
                "source": src,
                "data_url": url,
                "etag": info.get("etag"),
                "last_modified": info.get("last_modified"),
                "sha256": digest,
                "active_path": active_path,
                "active_version": now,
                "downloaded_at": datetime.utcnow().isoformat() + "Z",
            }
            out.append({
                "family": fam,
                "source": src,
                "ok": True,
                "active_path": active_path,
                "sha256": digest,
            })
    finally:
        save_manifest(paths, manifest)
        if client is None:
            use_client.close()
    return {"results": out, "active_dir": paths.active_dir}

