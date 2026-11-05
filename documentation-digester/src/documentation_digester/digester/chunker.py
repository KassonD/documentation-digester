from langchain_core.documents import Document
from langchain_text_splitters import HTMLHeaderTextSplitter, RecursiveCharacterTextSplitter

cleaned_html = """
<h1>CharacterBody2D</h1>

<p>
    CharacterBody2D is a physics-based body
    that is controlled by the user.
</p>

<h2>Movement</h2>

<p>
    CharacterBody2D provides a velocity property
    that controls its movement.
</p>

<h3>move_and_slide()</h3>

<p>
    This method moves the body based on its velocity.
</p>

<h2>Collision</h2>

<p>
    CharacterBody2D can detect collisions
    with other physics bodies.
</p>
"""

headers_to_split_on = [
    ("h1", "title"),
    ("h2", "subtitle"),
    ("h3", "topic"),
]

def split_text(html_content: str) -> list[Document]:
    html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    return html_splitter.split_text(html_content)

def chunk_documents(documents: list[Document]) -> list[Document]:
    recursive_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    return recursive_splitter.split_documents(documents)

documents = split_text(cleaned_html)
chunked_documents = chunk_documents(documents)

print ("DOCUMENTS\n")

for document in documents:
    print("---\n", document.page_content)
    print(document)

print ("CHUNKS\n")

for document in chunked_documents:
    print("---\n", document.page_content)
    print(document.metadata)


