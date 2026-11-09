from .cleaner import save_cleaned_documents
from .chunker import chunk
# Embeddings import
from .vector_store import upsert_chunks

if __name__ == "__main__":
    print("Running...")

    save_cleaned_documents()

    chunks = chunk()

    # Implement embedding

    # Implement 

    print("Finished")

