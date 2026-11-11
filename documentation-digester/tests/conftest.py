"""Shared fixtures. Pytest loads this file automatically; nothing imports it."""
import hashlib
from types import SimpleNamespace

import pytest

from documentation_digester.digester import chunker, cleaner, vector_store

SAMPLE_PAGE = """<!DOCTYPE html><html><head><title>t</title><script>evil()</script></head><body>
<nav class="wy-nav-side">SIDEBAR MENU</nav>
<div role="navigation">BREADCRUMB</div>
<div role="main" class="document" itemscope="itemscope">
  <script>inline()</script><style>.x{}</style>
  <div class="admonition attention"><p>Here be dragons: unstable version.</p></div>
  <section id="using-signals"><h1>Using signals<a class="headerlink" href="#x">¶</a></h1>
    <div class="admonition attention"><p>Keep this important attention note.</p></div>
    <p>Signals are messages that nodes emit when something happens to them, so other nodes can react.</p>
    <section id="custom"><h2>Custom signals<a class="headerlink" href="#y">¶</a></h2>
      <p>Declare a custom signal with the signal keyword, then call emit on it whenever the event occurs.</p>
    </section>
  </section>
  <footer>PAGE FOOTER</footer>
</div>
<footer>SITE FOOTER</footer></body></html>"""


def _fake_vector(text: str, dimension: int = 8) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [byte / 255 for byte in digest[:dimension]]


@pytest.fixture
def fake_embed():
    """Deterministic stand-in for the Sentence-Transformers model: same text, same vector."""
    return _fake_vector


@pytest.fixture
def built_docs(tmp_path, monkeypatch):
    """A tiny built-docs folder, with the cleaner and chunker pointed at temporary folders."""
    root = tmp_path / "data" / "godot_docs_built"
    page = root / "getting_started" / "signals.html"
    page.parent.mkdir(parents=True)
    page.write_text(SAMPLE_PAGE, encoding="utf-8")
    index_page = SAMPLE_PAGE.replace("Using signals", "Welcome").replace("Custom signals", "Contents")
    index_page = index_page.replace("Declare a custom signal", "Browse the manual").replace("Signals are", "Pages are")
    (root / "index.html").write_text(index_page, encoding="utf-8")
    for name in ("404.html", "genindex.html", "search.html"):
        (root / name).write_text(SAMPLE_PAGE, encoding="utf-8")
    (root / "no_main.html").write_text("<html><body><p>nothing</p></body></html>", encoding="utf-8")

    clean = root.parent / "clean_html"
    monkeypatch.setattr(cleaner, "DOCS_PATH", root)
    monkeypatch.setattr(cleaner, "CLEAN_HTML_PATH", clean)
    monkeypatch.setattr(chunker, "_CLEAN_HTML_DIR_PATH", clean)
    return root


@pytest.fixture
def clean_dir(tmp_path, monkeypatch):
    """An empty clean_html folder, with the chunker pointed at it."""
    path = tmp_path / "clean_html"
    path.mkdir()
    monkeypatch.setattr(chunker, "_CLEAN_HTML_DIR_PATH", path)
    return path


@pytest.fixture
def store(tmp_path, monkeypatch):
    """The real vector_store module, writing to a throwaway Chroma database."""
    monkeypatch.setattr(vector_store, "CHROMA_PATH", tmp_path / "chroma")
    return vector_store


@pytest.fixture
def make_chunks():
    """Build the four parallel lists that upsert_chunks expects."""
    def build(source="a.html", count=2, prefix="chunk"):
        ids = [f"{source}:{prefix}:{i}" for i in range(count)]
        texts = [f"{source} {prefix} text {i}" for i in range(count)]
        return SimpleNamespace(
            ids=ids,
            texts=texts,
            embeddings=[_fake_vector(t) for t in texts],
            metadatas=[{"source_path": source, "title": "T"} for _ in ids],
        )

    return build