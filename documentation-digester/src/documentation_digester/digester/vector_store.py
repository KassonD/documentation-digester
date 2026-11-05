from pathlib import Path

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

def upsert_chunks(ids: list[str], texts: list[str], embeddings: list[list[float]], metadatas: list[dict],) -> None:
    """Insert new chunks or update chunks that already exist.

    Each chunk has an ID, text, embedding, and metadata.
    Items at the same index in each list belong to the same chunk.

    ids: Unique ID for each chunk.
    texts: Actual text from each chunk.
    embeddings: List of numbers representing each chunk's meaning.
    metadatas: Details about each chunk, such as its source file.

    This function stores embeddings but doesn't generate them.
    It also doesn't delete old chunks that aren't in the input."""
    if not (len(ids) == len(texts) == len(embeddings) == len(metadatas)):
        raise ValueError("All input lists must have the same length.")
    
    if not ids:
        return
    
    collection = get_collection()
    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )