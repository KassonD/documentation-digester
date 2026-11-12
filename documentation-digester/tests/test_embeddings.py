import pytest
import numpy as np
from langchain_core.documents import Document

from documentation_digester.digester.embeddings import (
    get_embedding_model,
    embed_documents,
    embed_query,
    prepare_chunks_for_storage,
)


def test_model_dimensions():
    model = get_embedding_model()
    assert model.get_embedding_dimension() == 384


def test_document_embeddings():
    texts = [
        "Godot nodes communicate through signals.",
        "Scenes organize nodes into trees.",
    ]

    vectors = embed_documents(texts)

    assert len(vectors) == 2
    assert all(len(vector) == 384 for vector in vectors)


def test_query_embedding():
    vector = embed_query("How do Godot signals work?")

    assert len(vector) == 384


def test_empty_document_list():
    assert embed_documents([]) == []


def test_empty_query():
    with pytest.raises(ValueError):
        embed_query("")


def test_semantic_similarity():
    documents = [
        "Signals allow Godot nodes to communicate.",
        "Godot supports 3D materials and textures.",
    ]

    query = "How can nodes send messages?"

    vectors = embed_documents(documents)
    query_vector = embed_query(query)

    scores = [
        np.dot(query_vector, vector)
        for vector in vectors
    ]

    assert scores[0] > scores[1]


def test_metadata_preservation():
    chunks = [
        Document(
            page_content="Signals connect Godot nodes.",
            metadata={
                "source_path": "tutorials/signals.html",
                "file_name": "signals.html",
                "chunk_index": 0,
                "title": "Signals",
            },
        )
    ]

    result = prepare_chunks_for_storage(chunks)

    assert len(result["ids"]) == 1
    assert len(result["embeddings"][0]) == 384
    assert result["metadatas"][0]["source_path"] == "tutorials/signals.html"
    assert result["metadatas"][0]["title"] == "Signals"


def test_consistent_chunk_ids():
    chunks = [
        Document(
            page_content="Godot nodes use signals.",
            metadata={
                "source_path": "tutorials/signals.html",
                "chunk_index": 0,
            },
        )
    ]

    first = prepare_chunks_for_storage(chunks)
    second = prepare_chunks_for_storage(chunks)

    assert first["ids"] == second["ids"]