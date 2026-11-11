import builtins

import pytest

from documentation_digester.digester import chunker, cleaner

PAGE = (
    '<div class="document" role="main"><section><h1>Signals</h1>'
    "<p>{intro}</p><section><h2>Custom</h2><p>{body}</p>"
    "<section><h3>Emit</h3><p>{tail}</p></section></section></section></div>"
)
LONG = "Nodes send signals to tell other nodes what happened in the game. " * 60
INTRO = "Signals let nodes talk to each other without holding direct references to them."
TAIL = "Call emit on the signal when the event happens so that listeners can respond."
HEADINGS = {"title": "Signals", "subtitle": "Custom", "topic": "Emit"}


def _page():
    return PAGE.format(intro=INTRO, body=LONG, tail=TAIL)


def _chunks():
    return chunker._chunk_documents(chunker._split_text(_page()))


def _write(folder, relative="page.html"):
    path = folder / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_page(), encoding="utf-8")
    return path


def test_cleaner_output_folder_is_chunker_input_folder():
    assert chunker._CLEAN_HTML_DIR_PATH.resolve() == cleaner.CLEAN_HTML_PATH.resolve()


def test_no_chunk_exceeds_the_size_limit():
    assert max(len(c.page_content) for c in _chunks()) <= chunker._CHUNK_SIZE


def test_heading_hierarchy_is_kept_in_metadata():
    tail = next(c for c in _chunks() if "Call emit" in c.page_content)
    assert {key: tail.metadata[key] for key in HEADINGS} == HEADINGS


def test_long_sections_overlap_between_chunks():
    pieces = [c.page_content for c in _chunks() if c.metadata.get("subtitle") == "Custom" and len(c.page_content) > 500]
    assert len(pieces) >= 2
    assert pieces[1][:40] in pieces[0]


def test_body_text_is_not_lost():
    joined = " ".join(c.page_content for c in _chunks())
    assert INTRO in joined and TAIL in joined


def test_reads_files_in_nested_folders(clean_dir):
    _write(clean_dir, "tutorials/scripting/page.html")
    assert any(INTRO in c.page_content for c in chunker.chunk())


def test_chunk_index_counts_up_from_zero_per_file(clean_dir):
    _write(clean_dir, "a.html")
    _write(clean_dir, "b/b.html")
    by_file = {}
    for c in chunker.chunk():
        by_file.setdefault(c.metadata["file_name"], []).append(c.metadata["chunk_index"])
    assert len(by_file) == 2
    assert all(indexes == list(range(len(indexes))) for indexes in by_file.values())


def test_chunks_from_one_file_share_a_document_id(clean_dir):
    _write(clean_dir)
    assert len({c.metadata["document_id"] for c in chunker.chunk()}) == 1


def test_files_are_read_as_utf8(clean_dir, monkeypatch):
    _write(clean_dir)
    seen, real_open = [], builtins.open

    def spy(*args, **kwargs):
        seen.append(kwargs.get("encoding"))
        return real_open(*args, **kwargs)

    monkeypatch.setattr(builtins, "open", spy)
    chunker.chunk()
    assert seen == ["utf-8"]


# Known defects. strict=True means the test reports a failure once the bug is fixed,
# so remember to delete the marker then.

@pytest.mark.xfail(strict=True, reason="BUG-1: file_name is the full path on the developer's machine, so citations are not portable")
def test_source_is_relative_to_clean_html(clean_dir):
    _write(clean_dir, "tutorials/page.html")
    for c in chunker.chunk():
        assert c.metadata.get("source_path", c.metadata["file_name"]) == "tutorials/page.html"


@pytest.mark.xfail(strict=True, reason="BUG-2: headings become standalone chunks that carry no information")
def test_headings_are_not_standalone_chunks():
    assert not [c for c in _chunks() if c.page_content.strip() in set(HEADINGS.values())]


@pytest.mark.xfail(strict=True, reason="BUG-3: inline code and links are pulled out of their sentences")
def test_inline_code_stays_in_its_sentence():
    html = "<div><h1>T</h1><p>Call the <code>connect()</code> method of the signal.</p></div>"
    text = " ".join(" ".join(c.page_content for c in chunker._split_text(html)).split())
    assert "Call the connect() method of the signal." in text


@pytest.mark.xfail(strict=True, reason="BUG-4: heading text is cut off around inline code, so citations name the wrong section")
def test_heading_with_inline_code_keeps_its_full_title():
    html = "<div><h1>T</h1><h2>The <code>UNSAFE_CAST</code> warning</h2><p>Body text.</p></div>"
    body = next(c for c in chunker._split_text(html) if "Body text" in c.page_content)
    assert body.metadata["subtitle"] == "The UNSAFE_CAST warning"