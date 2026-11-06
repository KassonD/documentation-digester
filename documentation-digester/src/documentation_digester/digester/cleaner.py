from pathlib import Path
from bs4 import BeautifulSoup

# path to the generated Godot documentation
DOCS_PATH = Path(__file__).resolve().parent.parent /"data"/"godot_docs_built"

def clean_html(file_path):
    with open(file_path, "r", encoding="utf-8") as file: # read HTML file
        html = file.read()

    soup = BeautifulSoup(html, "html.parser") # parse the HTML
    content = soup.select_one('div.document[role="main"]') # find the main doc content

    if content is None:
        return None

    # removees unwanted elements
    for element in content.select("script, style, nav, footer, .headerlink, .admonition.attention"):
        element.decompose()
    
    return {
    "content": str(content),
    "source": file_path.relative_to(DOCS_PATH).as_posix(),
    }

def clean_all_html():
    excluded_files = {
        "404.html",
        "genindex.html",
        "search.html",
    }

    html_files = [
        file for file in DOCS_PATH.rglob("*.html")
        if file.name not in excluded_files
    ]

    print(f"Found {len(html_files)} documentation files.\n")

    for file_path in html_files[:5]:
        cleaned = clean_html(file_path)

        if cleaned:
            print(f"Successfully cleaned: {file_path.name}")
            print(f"Source: {cleaned['source']}\n")
        else:
            print(f"Failed to clean: {file_path.name}")

def get_cleaned_documents(limit=None):
    excluded_files = {
        "404.html",
        "genindex.html",
        "search.html",
    }

    documents = []

    for file_path in DOCS_PATH.rglob("*.html"):
        if file_path.name in excluded_files:
            continue

        cleaned = clean_html(file_path)

        if cleaned:
            documents.append(cleaned)

        if limit is not None and len(documents) >= limit:
            break

    return documents

if __name__ == "__main__":
    documents = get_cleaned_documents(limit=5)

    print(f"Cleaned {len(documents)} documents.\n")

    for document in documents:
        print(f"Source: {document['source']}")
        print(f"Content length: {len(document['content'])} characters\n")
    # clean_all_html()
    # test_file = DOCS_PATH/"classes"/"class_node.html"
    # cleaned = clean_html(test_file)
    # if cleaned:
    #     soup = BeautifulSoup(cleaned, "html.parser")
    #     print("Headings:", len(soup.find_all(["h1", "h2", "h3"])))
    #     print("Paragraphs:", len(soup.find_all("p")))
    #     print("Code blocks:", len(soup.find_all(["pre"])))
    #     print("\nFirst 1000 characters:")
    #     print(soup.get_text(separator=" ", strip=True)[:1000])
    # else:
    #     print("No content found")

        