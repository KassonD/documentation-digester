from pathlib import Path
from math import isfinite

import chromadb

# Find the repository root and set where Chroma saves its database.
PROJECT_ROOT = Path(__file__).resolve().parents[4]
CHROMA_PATH = PROJECT_ROOT / "data" / "chroma"
COLLECTION_NAME = "documentation"

def get_collection():
    """
    Open the Chroma database and get the documentation collection.

    If the collection doesn't exist, create it. The database is saved
    locally so the data stays available after restarting the app.

    Embeddings will come from the embedding pipeline, so we don't
    need Chroma to generate them.
    """
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=None,
    )

def upsert_chunks( ids: list[str], texts: list[str], embeddings: list[list[float]], metadatas: list[dict], batch_size: int = 256,) -> None:
    """
    Insert new chunks or update chunks that already exist.

    Each chunk has an ID, text, embedding, and metadata.
    Items at the same index in each list belong to the same chunk.

    ids: Unique ID for each chunk.
    texts: Actual text from each chunk.
    embeddings: List of numbers representing each chunk's meaning.
    metadatas: Details about each chunk, such as its source file.
    batch_size: Number of chunks to store in each batch.

    This function stores embeddings but doesn't generate them.
    It also doesn't delete old chunks that aren't in the input.
    """
    if not (len(ids) == len(texts) == len(embeddings) == len(metadatas)):
        raise ValueError("All input lists must have the same length.")

    if not isinstance(batch_size, int) or batch_size < 1:
        raise ValueError("batch_size must be a positive integer.")

    if not ids:
        return

    # Check IDs before writing any batches.
    if any(
        not isinstance(chunk_id, str) or not chunk_id.strip()
        for chunk_id in ids
    ):
        raise ValueError("Each chunk needs a nonempty string ID.")

    if len(set(ids)) != len(ids):
        raise ValueError("Chunk IDs must be unique within the input.")

    # Every vector must have the same number of values.
    dimension = len(embeddings[0])
    if dimension == 0:
        raise ValueError("Embeddings cannot be empty.")

    for embedding in embeddings:
        if len(embedding) != dimension:
            raise ValueError("All embeddings must have the same dimensions.")

        if any(
            not isinstance(value, (int, float)) or not isfinite(value)
            for value in embedding
        ):
            raise ValueError("Embeddings must contain finite numbers.")

    # Require source information so document updates and deletion work.
    for metadata in metadatas:
        if not isinstance(metadata, dict):
            raise ValueError("Each chunk's metadata must be a dictionary.")

        source_path = metadata.get("source_path")
        if not isinstance(source_path, str) or not source_path.strip():
            raise ValueError("Each chunk needs a nonempty source_path.")

    if any(not isinstance(text, str) for text in texts):
        raise ValueError("Each chunk's text must be a string.")

    # Respect both our requested batch size and Chroma's limit.
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    batch_size = min(batch_size, client.get_max_batch_size())
    collection = get_collection()

    # Store only the chunks belonging to the current batch.
    for start in range(0, len(ids), batch_size):
        end = start + batch_size

        collection.upsert(
            ids=ids[start:end],
            documents=texts[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
        )
def delete_document(source_path: str) -> None:
    """
    Delete all stored chunks belonging to one document.

    source_path must match the value saved in each chunk's metadata.
    This removes the chunks from Chroma, not the original source file.
    """
    # Reject an empty or whitespace-only path.
    if not source_path.strip():
        raise ValueError("source_path cannot be empty.")

    collection = get_collection()

    # Only delete chunks whose source_path matches this document.
    collection.delete(
        where={"source_path": source_path},
    )


def replace_document(source_path: str, ids: list[str], texts: list[str], embeddings: list[list[float]], metadatas: list[dict], ) -> None:
    """Store a document's new chunks and remove its outdated chunks.

    Every incoming chunk must belong to this document.
    Use delete_document() if there are no remaining chunks.
    """
    if not isinstance(source_path, str) or not source_path.strip():
        raise ValueError("source_path cannot be empty.")

    if not (len(ids) == len(texts) == len(embeddings) == len(metadatas)):
        raise ValueError("All input lists must have the same length.")

    if not ids:
        raise ValueError("Use delete_document() to remove all chunks.")

    # Make sure every chunk belongs to this document.
    for metadata in metadatas:
        if (
            not isinstance(metadata, dict)
            or metadata.get("source_path") != source_path
        ):
            raise ValueError("Every chunk must belong to this document.")

    if any(
        not isinstance(chunk_id, str) or not chunk_id.strip()
        for chunk_id in ids
    ):
        raise ValueError("Each chunk needs a nonempty string ID.")

    if len(set(ids)) != len(ids):
        raise ValueError("Chunk IDs must be unique within the input.")

    collection = get_collection()
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    batch_size = min(256, client.get_max_batch_size())

    # Prevent incoming IDs from overwriting another document's chunks.
    for start in range(0, len(ids), batch_size):
        existing = collection.get(
            ids=ids[start:start + batch_size],
            include=["metadatas"],
        )

        for metadata in existing["metadatas"]:
            if metadata is None or metadata.get("source_path") != source_path:
                raise ValueError (
                    "A chunk ID already belongs to another document."
                )

    # Get the IDs currently stored for this document.
    old_chunks = collection.get(
        where={"source_path": source_path},
        include=[],
    )

    # Save all new chunks before deleting outdated ones.
    upsert_chunks(ids, texts, embeddings, metadatas)

    new_ids = set(ids)
    outdated_ids = [
        chunk_id
        for chunk_id in old_chunks["ids"]
        if chunk_id not in new_ids
    ]

    # Delete the old chunks that aren't in the new version.
    for start in range(0, len(outdated_ids), batch_size):
        collection.delete(
            ids=outdated_ids[start:start + batch_size],
        )

def search_chunks(query_embedding: list[float], top_k: int = 5,) -> list[dict]:
    """
    Return the closest stored chunks for a query embedding.

    The query must use the same embedding model as the stored chunks.
    Each match includes its ID, text, metadata, and distance.
    A smaller distance means a closer match.
    """
    if type(top_k) is not int or top_k < 1:
        raise ValueError("top_k must be a positive integer.")
    
    if any (type(value) not in (int, float) or not isfinite(value) for value in query_embedding):
        raise ValueError("The query embedding must contain finite numbers.")
    
    collection = get_collection()

    # Return no matches if nothing has been indexed.
    count = collection.count()
    if count == 0:
        return []
    
    # Chroma expects a list of query vectors, even for one query.
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, count),
        include=["documents", "metadatas", "distances"],
    )

    # Index 0 selects the results for our single query.
    matches = []

    for index, chunk_id in enumerate(results["ids"][0]):
        matches.append({
            "id": chunk_id,
            "text": results["documents"][0][index],
            "metadata": results["metadatas"][0][index],
            "distance": results["distances"][0][index],
        })
    
    return matches