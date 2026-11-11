"""End to end: real cleaner, chunker, metadata preparation and Chroma, with a fake embedding model."""
import pytest

from documentation_digester.digester import embeddings, pipeline


@pytest.fixture
def indexed(built_docs, store, fake_embed, monkeypatch):
    monkeypatch.setattr(embeddings, "embed_documents", lambda texts: [fake_embed(t) for t in texts])
    pipeline.main()
    return store


def test_pipeline_indexes_the_docs(indexed):
    stored = indexed.get_collection().get(include=["documents", "metadatas"])
    assert stored["ids"]
    assert any("custom signal with the signal keyword" in text for text in stored["documents"])
    assert all(m["source_path"] and m["title"] for m in stored["metadatas"])


def test_stored_chunks_are_clean(indexed):
    text = " ".join(indexed.get_collection().get()["documents"])
    for noise in ("SIDEBAR MENU", "SITE FOOTER", "Here be dragons", "¶"):
        assert noise not in text


def test_running_twice_creates_no_duplicates(indexed):
    before = indexed.get_collection().count()
    pipeline.main()
    assert indexed.get_collection().count() == before


def test_search_finds_the_right_chunk_and_cites_its_page(indexed, fake_embed):
    target = next(
        text for text in indexed.get_collection().get()["documents"]
        if "custom signal with the signal keyword" in text
    )
    top = indexed.search_chunks(fake_embed(target), top_k=1)[0]
    assert top["text"] == target
    assert top["metadata"]["subtitle"] == "Custom signals"
    assert top["metadata"]["source_path"].replace("\\", "/").endswith("getting_started/signals.html")


def test_empty_docs_folder_indexes_nothing(tmp_path, store, monkeypatch, capsys):
    from documentation_digester.digester import chunker, cleaner

    monkeypatch.setattr(cleaner, "DOCS_PATH", tmp_path / "none")
    monkeypatch.setattr(cleaner, "CLEAN_HTML_PATH", tmp_path / "clean")
    monkeypatch.setattr(chunker, "_CLEAN_HTML_DIR_PATH", tmp_path / "clean")
    pipeline.main()
    assert "No chunks found" in capsys.readouterr().out
    assert store.get_collection().count() == 0