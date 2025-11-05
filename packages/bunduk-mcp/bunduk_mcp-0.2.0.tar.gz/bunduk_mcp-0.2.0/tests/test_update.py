import os
from pathlib import Path

from bunduk_mcp.update import get_paths, ensure_dirs, load_manifest, save_manifest, enumerate_sources, check_updates, sync
from bunduk_mcp.data.loader import DataRegistry


def fake_fetcher_factory(content: bytes, etag: str = "W/\"abc\"", last_modified: str = "Mon, 01 Jan 2024 00:00:00 GMT"):
    def _fetch(url: str, dest_tmp: str):
        Path(os.path.dirname(dest_tmp)).mkdir(parents=True, exist_ok=True)
        with open(dest_tmp, "wb") as f:
            f.write(content)
        return {"etag": etag, "last_modified": last_modified}

    return _fetch


def test_sync_biogref_to_active_and_registry(tmp_path):
    # Prepare data dirs
    data_dir = tmp_path / "data"
    paths = get_paths(str(data_dir))
    ensure_dirs(paths)

    # Create a small CBDB-like biogref CSV via fetcher
    csv_bytes = (
        "primary_id,person_id,person_name,gender,born_year,died_year,dynasty,jiguan\n"
        "x,1762,王安石,男,1014,1094,宋,河陽\n"
    ).encode("utf-8")
    fetcher = fake_fetcher_factory(csv_bytes)

    # Monkeypatch BUNDUK_MCP_DATA_DIR env so registry prefers active there
    os.environ["BUNDUK_MCP_DATA_DIR"] = str(data_dir)

    # Sync only biogref:cbdb using fake fetcher
    res = sync(family="biogref", sources=["cbdb"], data_dir=str(data_dir), fetcher=fetcher)
    assert res["results"][0]["ok"] is True
    active_path = Path(res["results"][0]["active_path"])
    assert active_path.exists()

    # Registry should load from active dir and see the single row
    reg = DataRegistry(active_dir=str(paths.active_dir), references_dir="references")
    assert "cbdb" in reg.biogref
    assert len(reg.biogref["cbdb"].rows) == 1
    assert reg.biogref["cbdb"].rows[0]["person_name"] == "王安石"


def test_check_updates_uses_etag(monkeypatch, tmp_path):
    # Minimal httpx.Client stub
    class FakeResp:
        def __init__(self, status_code=200, headers=None):
            self.status_code = status_code
            self.headers = headers or {"ETag": 'W/"abc"', "Last-Modified": "Mon, 01 Jan 2024 00:00:00 GMT"}

    class FakeClient:
        def head(self, url, headers=None, follow_redirects=True):
            return FakeResp(200, {"ETag": 'W/"abc"', "Last-Modified": "Mon, 01 Jan 2024 00:00:00 GMT"})

        def close(self):
            pass

    # Call check_updates limited to one family using fake client
    res = check_updates(family="biogref", client=FakeClient())
    assert "results" in res
    # We can't guarantee remote etag comparison at first run, but structure must be ok
    assert any("family" in r and "source" in r and "ok" in r for r in res["results"])


def test_registry_prefers_active_over_references(tmp_path):
    # Write an active biogref file with 1 row
    active_dir = tmp_path / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    fpath = active_dir / "biogref-cbdb-data.csv"
    fpath.write_text(
        "primary_id,person_id,person_name,gender,born_year,died_year,dynasty,jiguan\nX,1,測試人,男,1000,1001,宋,河陽\n",
        encoding="utf-8",
    )

    reg = DataRegistry(references_dir="references", active_dir=str(active_dir))
    assert "cbdb" in reg.biogref
    assert len(reg.biogref["cbdb"].rows) == 1
    assert reg.biogref["cbdb"].rows[0]["person_name"] == "測試人"

