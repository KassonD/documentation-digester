import uuid
from langchain_core.documents import Document
from langchain_text_splitters import HTMLHeaderTextSplitter, RecursiveCharacterTextSplitter
# from langchain_experimental.text_splitter import SemanticChunker
from pathlib import Path

class Header:
    TITLE = "title"
    SUBTITLE = "subtitle"
    TOPIC = "topic"

_CHUNK_SIZE = 1000
_CHUNK_OVERLAP = 150
_CLEAN_HTML_DIR_PATH = Path(__file__).parent.parent / "data" / "clean_html"
_HEADERS_TO_SPLIT_ON = [
    ("h1", Header.TITLE),
    ("h2", Header.SUBTITLE),
    ("h3", Header.TOPIC),
]

# Turns the clean html into LangChain documents
def _split_text(html_content: str) -> list[Document]:
    html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=_HEADERS_TO_SPLIT_ON)
    return html_splitter.split_text(html_content)

# Splits the documents into chunks.
# If a document has too much content, another document will be created.
# This prevents documents from having too much unrelated content.
def _chunk_documents(documents: list[Document]) -> list[Document]:
    recursive_splitter = RecursiveCharacterTextSplitter(chunk_size=_CHUNK_SIZE, chunk_overlap=_CHUNK_OVERLAP)
    return recursive_splitter.split_documents(documents)


def _process_chunks(chunks: list[Document], file_name: str) -> list[Document]:
    processed_chunks = []
    index = 0
    document_id = uuid.uuid4()

    for chunk in chunks:
        page_content = chunk.page_content.strip()
        if (
            page_content != chunk.metadata.get(Header.TITLE, "").strip() and
            page_content != chunk.metadata.get(Header.SUBTITLE, "").strip() and
            page_content != chunk.metadata.get(Header.TOPIC, "").strip()
        ):
            chunk.metadata.update({
                "document_id": document_id,
                "file_name": file_name,
                "chunk_index": index
            })
            processed_chunks.append(chunk)
            index += 1


    return processed_chunks

# Returns documents created using the clean html files
def chunk() -> list[Document]:
    chunks = []

    for file_path in _CLEAN_HTML_DIR_PATH.rglob("*.html"):
        if file_path.is_file():
            with open(file=file_path, mode="r", encoding="utf-8") as file:
                print(file.name)
                content = file.read()
                documents = _split_text(content)
                chunked_documents = _chunk_documents(documents)
                processed_chunks = _process_chunks(chunks=chunked_documents, file_name=file.name)
                chunks.extend(processed_chunks)

    return chunks

if __name__ == "__main__":
    dlist = chunk()

    for d in dlist:
        with open("output.txt", "a", encoding="utf-8") as file:
            print("---\n", d.page_content, file=file)
            print(d.metadata, file=file)
