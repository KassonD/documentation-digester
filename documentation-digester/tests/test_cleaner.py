from bs4 import BeautifulSoup

from documentation_digester.digester import cleaner


def _clean(built_docs):
    return cleaner.clean_html(built_docs / "getting_started" / "signals.html")


def _text(built_docs):
    return BeautifulSoup(_clean(built_docs)["content"], "html.parser").get_text()


def test_keeps_main_content_and_headings(built_docs):
    content = _clean(built_docs)["content"]
    assert "<h1>" in content and "<h2>" in content
    assert "emit when something happens" in content


def test_strips_menus_footers_and_scripts(built_docs):
    text = _text(built_docs)
    for noise in ("SIDEBAR MENU", "BREADCRUMB", "SITE FOOTER", "PAGE FOOTER", "inline()", "evil()"):
        assert noise not in text


def test_removes_heading_permalink_symbol(built_docs):
    assert "¶" not in _text(built_docs)


def test_removes_only_the_unstable_version_warning(built_docs):
    text = _text(built_docs)
    assert "Here be dragons" not in text
    assert "Keep this important attention note" in text


def test_source_is_relative_with_forward_slashes(built_docs):
    assert _clean(built_docs)["source"] == "getting_started/signals.html"


def test_page_without_main_content_returns_none(built_docs):
    assert cleaner.clean_html(built_docs / "no_main.html") is None


def test_skips_404_genindex_and_search_pages(built_docs):
    sources = {doc["source"] for doc in cleaner.get_cleaned_documents()}
    assert sources == {"index.html", "getting_started/signals.html"}


def test_limit_is_respected(built_docs):
    assert len(cleaner.get_cleaned_documents(limit=1)) == 1


def test_save_keeps_folder_structure(built_docs):
    cleaner.save_cleaned_documents()
    assert (cleaner.CLEAN_HTML_PATH / "getting_started" / "signals.html").is_file()