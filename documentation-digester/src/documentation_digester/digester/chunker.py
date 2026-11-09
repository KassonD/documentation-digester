import uuid
from langchain_core.documents import Document
from langchain_text_splitters import HTMLHeaderTextSplitter, RecursiveCharacterTextSplitter
from pathlib import Path

_CHUNK_SIZE = 1000
_CHUNK_OVERLAP = 150
_CLEAN_HTML_DIR_PATH = Path(__file__).parent.parent / "data" / "clean_html"
_HEADERS_TO_SPLIT_ON = [
    ("h1", "title"),
    ("h2", "subtitle"),
    ("h3", "topic"),
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

def _set_metadata(chunks: list[Document], file_name: str):
    document_id = uuid.uuid4()

    for index, chunk in enumerate(chunks):
        chunk.metadata.update({
            "document_id": document_id,
            "file_name": file_name,
            "chunk_index": index
        })

# Returns documents created using the clean html files
def chunk() -> list[Document]:
    chunks = []

    for file_path in _CLEAN_HTML_DIR_PATH.rglob("*.html"):
        if file_path.is_file():
            with open(file_path, "r") as file:
                content = file.read()
                documents = _split_text(content)
                chunked_documents = _chunk_documents(documents)
                _set_metadata(chunks=chunked_documents, file_name=file.name)
                chunks.extend(chunked_documents)

    return chunks

# dlist = chunk()

# for d in dlist:
#     print("---\n", d.page_content)
#     print(d.metadata)
