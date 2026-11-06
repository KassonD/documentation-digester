from pathlib import Path
from bs4 import BeautifulSoup

# path to the generated Godot documentation
DOCS_PATH = Path(__file__).resolve().parent.parent /"data"/"godot_docs_built"
CLEAN_HTML_PATH = DOCS_PATH.parent/"clean_html"

def clean_html(file_path):
    with open(file_path, "r", encoding="utf-8") as file: # read HTML file
        html = file.read()

    soup = BeautifulSoup(html, "html.parser") # parse the HTML
    content = soup.select_one('div.document[role="main"]') # find the main doc content

    if content is None:
        return None

    # removees unwanted elements
    for element in content.select(
    "script, style, nav, footer, .headerlink"
    ):
        element.decompose()

    # Remove only the unstable documentation version warning
    for warning in content.select(".admonition.attention"):
        if "Here be dragons" in warning.get_text():
            warning.decompose()
    
    return {
    "content": str(content),
    "source": file_path.relative_to(DOCS_PATH).as_posix(),
    }

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


def save_cleaned_documents(limit=None):
    CLEAN_HTML_PATH.mkdir(parents=True, exist_ok=True)

    documents = get_cleaned_documents(limit=limit)

    for document in documents:
        source = Path(document["source"])

        # Preserve the original folder structure
        output_path = CLEAN_HTML_PATH / source
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as file:
            file.write(document["content"])

    print(f"Saved {len(documents)} cleaned HTML files.")


def validate_cleaner():
    html_files = list(DOCS_PATH.rglob("*.html"))

    excluded_files = {
        "404.html",
        "genindex.html",
        "search.html",
    }

    successful = 0
    failed = []
    empty = []

    for index, file_path in enumerate(html_files, start=1):
        if index % 100 == 0:
            print(f"Processing {index}/{len(html_files)} files...", flush=True)
        if file_path.name in excluded_files:
            continue

        try:
            cleaned = clean_html(file_path)

            if cleaned is None:
                failed.append(file_path.name)
                continue

            soup = BeautifulSoup(cleaned["content"], "html.parser")
            text = soup.get_text(strip=True)

            if not text:
                empty.append(file_path.name)
            else:
                successful += 1

        except Exception as e:
            failed.append(f"{file_path.name}: {e}")

    print(f"Successfully cleaned: {successful}")
    print(f"Failed: {len(failed)}")
    print(f"Empty documents: {len(empty)}")

    if failed:
        print("\nFailed files:")
        for file in failed:
            print(file)

    if empty:
        print("\nEmpty files:")
        for file in empty:
            print(file)



if __name__ == "__main__":
    save_cleaned_documents()




        