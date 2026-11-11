from .cleaner import save_cleaned_documents
from .chunker import chunk
from .embeddings import prepare_chunks_for_storage
from .vector_store import upsert_chunks

def main() -> None:
    print("Running...")
    save_cleaned_documents()

    print("Splitting cleaned documentation into chunks...")
    chunks = chunk()


    if not chunks:
        print("No chunks found. Check the cleaned HTML directory.")
        return

    print(f"Generating emebddings for {len(chunks)} chunks...")
    records = prepare_chunks_for_storage(chunks)

    print("Saving chunks to Chroma...")
    upsert_chunks(**records)

    print(f"Finished indexing {len(records['ids'])} chunks.")

if __name__ == "__main__":
    main()