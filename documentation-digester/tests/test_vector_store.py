import numpy as np
import pytest


def _stored(store):
    return store.get_collection().get(include=["documents", "metadatas"])


def _upsert(store, c):
    store.upsert_chunks(c.ids, c.texts, c.embeddings, c.metadatas)


# ---------- upsert_chunks ----------

def test_upsert_stores_text_and_metadata(store, make_chunks):
    c = make_chunks()
    _upsert(store, c)
    stored = _stored(store)
    assert sorted(stored["ids"]) == sorted(c.ids)
    assert set(stored["documents"]) == set(c.texts)
    assert all(m["source_path"] == "a.html" for m in stored["metadatas"])


def test_reindexing_creates_no_duplicates(store, make_chunks):
    c = make_chunks()
    _upsert(store, c)
    _upsert(store, c)
    assert store.get_collection().count() == 2


def test_batches_cover_every_chunk(store, make_chunks):
    c = make_chunks(count=7)
    store.upsert_chunks(c.ids, c.texts, c.embeddings, c.metadatas, batch_size=3)
    assert store.get_collection().count() == 7


def test_empty_input_is_a_no_op(store):
    assert store.upsert_chunks([], [], [], []) is None


@pytest.mark.parametrize(
    "field, value",
    [
        ("ids", ["only-one"]),
        ("ids", ["same", "same"]),
        ("ids", ["", "ok"]),
        ("texts", ["ok", 5]),
        ("embeddings", [[0.1, 0.2], [0.1]]),
        ("embeddings", [[], []]),
        ("embeddings", [[float("nan")], [0.1]]),
        ("embeddings", [[float("inf")], [0.1]]),
        ("metadatas", [{"title": "no source"}, {"source_path": "a"}]),
        ("metadatas", [{"source_path": "  "}, {"source_path": "a"}]),
        ("metadatas", ["nope", {"source_path": "a"}]),
    ],
)
def test_invalid_input_is_rejected_and_nothing_is_written(store, make_chunks, field, value):
    c = make_chunks()
    setattr(c, field, value)
    with pytest.raises(ValueError):
        _upsert(store, c)
    assert store.get_collection().count() == 0


@pytest.mark.parametrize("batch_size", [0, -1, 1.5, True])
def test_bad_batch_size_is_rejected(store, make_chunks, batch_size):
    c = make_chunks()
    with pytest.raises(ValueError):
        store.upsert_chunks(c.ids, c.texts, c.embeddings, c.metadatas, batch_size=batch_size)


def test_raw_float32_vectors_are_rejected(store, make_chunks):
    """Sentence-Transformers returns float32, so embeddings must go through .tolist() first."""
    c = make_chunks()
    c.embeddings = list(np.asarray(c.embeddings, dtype=np.float32))
    with pytest.raises(ValueError):
        _upsert(store, c)


# ---------- delete_document / replace_document ----------

def test_delete_removes_only_that_document(store, make_chunks):
    _upsert(store, make_chunks("a.html"))
    _upsert(store, make_chunks("b.html"))
    store.delete_document("a.html")
    assert {m["source_path"] for m in _stored(store)["metadatas"]} == {"b.html"}


@pytest.mark.parametrize("path", ["", "   ", None])
def test_delete_rejects_blank_or_missing_path(store, path):
    with pytest.raises(ValueError):
        store.delete_document(path)


def test_replace_removes_outdated_chunks(store, make_chunks):
    _upsert(store, make_chunks(count=3, prefix="old"))
    new = make_chunks(count=1, prefix="new")
    store.replace_document("a.html", new.ids, new.texts, new.embeddings, new.metadatas)
    assert _stored(store)["ids"] == new.ids


def test_replace_leaves_other_documents_alone(store, make_chunks):
    other = make_chunks("b.html")
    _upsert(store, make_chunks("a.html"))
    _upsert(store, other)
    new = make_chunks("a.html", count=1, prefix="new")
    store.replace_document("a.html", new.ids, new.texts, new.embeddings, new.metadatas)
    assert set(other.ids) <= set(_stored(store)["ids"])


def test_replace_refuses_ids_owned_by_another_document(store, make_chunks):
    owned = make_chunks("b.html")
    _upsert(store, owned)
    with pytest.raises(ValueError):
        store.replace_document(
            "a.html", owned.ids, owned.texts, owned.embeddings,
            [{"source_path": "a.html"} for _ in owned.ids],
        )
    assert {m["source_path"] for m in _stored(store)["metadatas"]} == {"b.html"}


def test_replace_refuses_chunks_from_a_different_document(store, make_chunks):
    c = make_chunks("b.html")
    with pytest.raises(ValueError):
        store.replace_document("a.html", c.ids, c.texts, c.embeddings, c.metadatas)


def test_failed_replace_keeps_the_old_version(store, make_chunks):
    old = make_chunks(count=2, prefix="old")
    _upsert(store, old)
    bad = make_chunks(count=1, prefix="new")
    bad.embeddings = [[float("nan")] * 8]
    with pytest.raises(ValueError):
        store.replace_document("a.html", bad.ids, bad.texts, bad.embeddings, bad.metadatas)
    assert sorted(_stored(store)["ids"]) == sorted(old.ids)


# ---------- search_chunks ----------

def test_search_on_empty_database_returns_nothing(store, fake_embed):
    assert store.search_chunks(fake_embed("anything")) == []


def test_search_returns_exact_match_first_with_all_fields(store, make_chunks):
    c = make_chunks(count=5)
    _upsert(store, c)
    matches = store.search_chunks(c.embeddings[3], top_k=3)
    assert matches[0]["id"] == c.ids[3]
    assert matches[0]["text"] == c.texts[3]
    assert matches[0]["metadata"]["source_path"] == "a.html"
    assert set(matches[0]) == {"id", "text", "metadata", "distance"}


def test_search_results_are_closest_first(store, make_chunks):
    c = make_chunks(count=5)
    _upsert(store, c)
    distances = [m["distance"] for m in store.search_chunks(c.embeddings[0], top_k=5)]
    assert distances == sorted(distances)


def test_search_never_returns_more_than_stored(store, make_chunks):
    c = make_chunks(count=2)
    _upsert(store, c)
    assert len(store.search_chunks(c.embeddings[0], top_k=10)) == 2


@pytest.mark.parametrize("top_k", [0, -1, 1.5, True])
def test_search_rejects_bad_top_k(store, fake_embed, top_k):
    with pytest.raises(ValueError):
        store.search_chunks(fake_embed("q"), top_k=top_k)


@pytest.mark.parametrize(
    "vector",
    [[], [float("nan"), 0.1], [float("inf")], list(np.ones(8, dtype=np.float32))],
    ids=["empty", "nan", "inf", "float32-not-tolist"],
)
def test_search_rejects_bad_query_vectors(store, vector):
    with pytest.raises(ValueError):
        store.search_chunks(vector)