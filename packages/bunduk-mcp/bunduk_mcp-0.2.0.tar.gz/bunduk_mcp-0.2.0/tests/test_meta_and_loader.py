from bunduk_mcp.data.meta import format_resource_template, load_biogref_meta, load_textref_meta
from bunduk_mcp.data.loader import DataRegistry


def test_format_resource_template_basic():
    tpl = "http://example.com/person/{person_id}?name={person_name}"
    row = {"person_id": "123", "person_name": "王安石"}
    out = format_resource_template(tpl, row)
    assert out == "http://example.com/person/123?name=王安石"


def test_load_meta_and_registry_links():
    reg = DataRegistry(references_dir="references")
    # Ensure some biogref sources loaded (cbdb expected in repo)
    assert "cbdb" in reg.biogref
    src = reg.biogref["cbdb"]
    # Find any row with a person_id
    assert src.rows, "CBDB rows should not be empty"
    any_row = src.rows[0]
    link = reg.make_person_link("cbdb", any_row)
    # If ResourceTemplate is present and person_id filled, we should get a link
    if src.meta.get("ResourceTemplate") and any_row.get("person_id"):
        assert isinstance(link, str)


def test_registry_textref_loaded():
    reg = DataRegistry(references_dir="references")
    # Expect at least one textref source in this repo
    assert len(reg.textref) >= 1
    # Validate index structures
    for s, src in reg.textref.items():
        assert isinstance(src.by_primary, dict)
        assert isinstance(src.by_title, dict)

