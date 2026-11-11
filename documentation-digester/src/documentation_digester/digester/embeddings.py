from functools import lru_cache
from sentence_transformers import SentenceTransformer
import hashlib
from langchain_core.documents import Document


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Load the Sentence-Transformers model once
    and reuse it for future requests.
    """
    model = SentenceTransformer(MODEL_NAME)
    return model

    
def embed_documents(texts: list[str]) -> list[list[float]]:
    """
    Convert multiple documentation text chunks into
    384-dimensional numerical embedding vectors.
    """

    if not texts:
        return []

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False
    )

    return embeddings.tolist()



def embed_query(question: str) -> list[float]:
    """
    Convert a user's natural-language question
    into a 384-dimensional embedding vector.
    """

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Question cannot be empty.")

    model = get_embedding_model()

    embedding = model.encode(
        question,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    return embedding.tolist()


def prepare_chunks_for_storage(chunks: list[Document]) -> dict:
    """
    Convert LangChain document chunks into the four lists
    required by the vector database.
    """
    if not chunks:
        return {
            "ids": [],
            "texts": [],
            "embeddings": [],
            "metadatas": []
        }

    texts = []
    ids = []
    metadatas = []

    for chunk in chunks:
        text = chunk.page_content

        if not text or not text.strip():
            raise ValueError("Document chunks cannot be empty.")

        metadata = dict(chunk.metadata)

        # Use the full source path when available.
        # The filename is a temporary fallback.
        source_path = metadata.get("source_path") or metadata.get("file_name")

        if not isinstance(source_path, str) or not source_path.strip():
            raise ValueError("Each chunk must include source information.")

        metadata["source_path"] = source_path

        # Chroma metadata values must be supported scalar types.
        # For example, convert UUID objects into strings.
        metadata = {
            key: value if isinstance(value, (str, int, float, bool))
            else str(value)
            for key, value in metadata.items()
            if value is not None
        }

        # Create a repeatable ID from source, position, and text.
        chunk_key = (
            f"{source_path}:"
            f"{metadata.get('chunk_index', '')}:"
            f"{text}"
        )

        chunk_id = hashlib.sha256(
            chunk_key.encode("utf-8")
        ).hexdigest()

        ids.append(chunk_id)
        texts.append(text)
        metadatas.append(metadata)

    embeddings = embed_documents(texts)

    return {
        "ids": ids,
        "texts": texts,
        "embeddings": embeddings,
        "metadatas": metadatas
    }

