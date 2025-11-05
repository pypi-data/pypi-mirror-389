from bunduk_mcp.schemas import AnnotationSpan
from bunduk_mcp.util import html_build_annotations, html_escape, person_score


def test_html_build_annotations_simple():
    text = "王安石游杭州"
    anns = [
        AnnotationSpan(start=0, end=3, type="person", label="王安石", link="http://example/person/1762"),
        AnnotationSpan(start=3, end=5, type="verb", label="游"),
    ]
    html = html_build_annotations(text, anns)
    assert "class=\"ent person\"" in html
    assert "data-link=\"http://example/person/1762\"" in html
    assert "王安石" in html


def test_html_build_annotations_overlap_longest_wins():
    text = "司馬光"
    # Overlapping: [0,2) and [0,3), longest should win
    anns = [
        AnnotationSpan(start=0, end=2, type="person", label="司馬"),
        AnnotationSpan(start=0, end=3, type="person", label="司馬光"),
    ]
    html = html_build_annotations(text, anns)
    # Only one span should be present
    assert html.count("<span") == 1
    assert "司馬光" in html


def test_person_score_features():
    row = {
        "person_name": "王安石",
        "born_year": "1014",
        "died_year": "1094",
        "dynasty": "宋",
        "jiguan": "河陽",
    }
    context = {"year": 1070, "dynastyTokens": ["宋"], "places": ["河陽"], "surface": "王安石"}
    explanations = person_score(row, context, source="cbdb")
    features = {e.feature for e in explanations}
    assert "dynasty" in features
    assert any(e.contribution >= 1 for e in explanations if e.feature.startswith("year"))
    assert "jiguan_comention" in features
    assert "exact_name" in features

