"""Checks the evaluation tool's own math, so the numbers in the report can be trusted."""
import pytest

from evaluation.evaluate import (
    DocsPages, check_golden, chunk_section, Golden, hit_at, load_golden,
    percentile, precision_at, reciprocal_rank, relative_page, text_match_ratio,
)


def test_hit_rate():
    assert hit_at([False, True], 1) == 0
    assert hit_at([False, True], 2) == 1
    assert hit_at([], 5) == 0


def test_reciprocal_rank_uses_first_correct_result():
    assert reciprocal_rank([False, False, True, True]) == pytest.approx(1 / 3)
    assert reciprocal_rank([False]) == 0


def test_precision_divides_by_k():
    assert precision_at([True], 5) == pytest.approx(0.2)


def test_percentile_nearest_rank():
    data = list(range(1, 101))
    assert percentile(data, 50) == 50
    assert percentile(data, 95) == 95
    assert percentile([7], 95) == 7


@pytest.mark.parametrize("raw", [
    r"C:\Users\aaron\x\src\documentation_digester\data\clean_html\tutorials\a.html",
    "/home/x/data/clean_html/tutorials/a.html",
    "tutorials/a.html",
    "./tutorials/a.html",
])
def test_relative_page_handles_absolute_and_relative_paths(raw):
    assert relative_page(raw) == "tutorials/a.html"


def test_chunk_section_uses_the_deepest_heading():
    assert chunk_section({"title": "A", "subtitle": "B", "topic": "C"}) == "C"
    assert chunk_section({"title": "A", "subtitle": "B"}) == "B"
    assert chunk_section({}) == ""


def test_text_match_tolerates_whitespace_but_not_other_text():
    page = "".join("Signals let nodes talk to each other without references.".split()).casefold()
    assert text_match_ratio("Signals let  nodes\ntalk to each other", page) == 1
    assert text_match_ratio("Shaders run on the graphics card", page) == 0


@pytest.fixture
def docs(tmp_path):
    page = tmp_path / "a" / "b.html"
    page.parent.mkdir()
    page.write_text(
        '<div class="document" role="main"><h1>Page<a class="headerlink">¶</a></h1>'
        "<h2>Target</h2><p>Some real content here for testing.</p></div>",
        encoding="utf-8",
    )
    return DocsPages(tmp_path)


def test_docs_pages_finds_headings_and_text(docs):
    assert docs.exists("a/b.html") and not docs.exists("a/missing.html")
    assert docs.has_heading("a/b.html", "Page") and docs.has_heading("a/b.html", " target ")
    assert docs.text_ratio("a/b.html", "Some real content here for testing.") == 1


def test_check_golden_flags_labels_missing_from_the_build(docs):
    golden = [
        Golden("ok", "q", "a/b.html", ["Target"]),
        Golden("no_page", "q", "x.html", ["Target"]),
        Golden("no_section", "q", "a/b.html", ["Nope"]),
    ]
    assert [p.split(":")[0] for p in check_golden(golden, docs)] == ["no_page", "no_section"]


def test_golden_questions_file_is_well_formed():
    golden = load_golden()
    assert len(golden) >= 30
    assert len({g.id for g in golden}) == len(golden)
    assert len({g.question for g in golden}) == len(golden)
    assert all(g.page.endswith(".html") and g.sections for g in golden)