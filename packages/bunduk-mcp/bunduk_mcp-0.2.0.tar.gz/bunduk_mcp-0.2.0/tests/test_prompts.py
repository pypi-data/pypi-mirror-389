from bunduk_mcp.server import (
    punctuate_zh_classical,
    extract_entities_zh_classical,
    translate_sentences_zh_en,
    render_html_annotations_prompt,
    render_html_bilingual_table,
)


def test_punctuate_prompt_contains_text():
    text = "孟子曰性善"
    out = punctuate_zh_classical(text)
    assert "Punctuate".lower() in out.lower() or "punctuate" in out.lower()
    assert text in out


def test_extract_entities_prompt_is_json_directive():
    text = "王安石至杭州。"
    out = extract_entities_zh_classical(text)
    assert "Return JSON".lower() in out.lower() or "json" in out.lower()
    assert text in out


def test_translate_prompt_is_messages():
    text = "學而時習之"
    msgs = translate_sentences_zh_en(text)
    assert isinstance(msgs, list) and len(msgs) >= 2


def test_render_annotations_prompt_has_inputs():
    t = "司馬光作資治通鑑"
    anns = "[{\"type\":\"person\",\"text\":\"司馬光\",\"start\":0,\"end\":3}]"
    out = render_html_annotations_prompt(t, anns)
    assert t in out and anns in out


def test_render_bilingual_table_prompt_has_title():
    s = "{\"sentences\":[{\"zh\":\"學而時習之\",\"en\":\"\"}]}"
    a = "{\"entities\":[]}"
    out = render_html_bilingual_table(s, a, title="Test")
    assert "Title" in out or "title" in out
    assert "HTML" in out or "html" in out
