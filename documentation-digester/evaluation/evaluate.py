"""Measure search quality, citation accuracy, chunk quality and latency on the real index.

Run from the folder that has pyproject.toml:
    uv run python -m evaluation.evaluate
    uv run python -m evaluation.evaluate --k 5 --label "MiniLM, 1000/150 chunks"
    uv run python -m evaluation.evaluate --api-url http://127.0.0.1:8000   (also times the full /chat call)

Writes a Markdown report to evaluation/results/.
"""
import argparse
import json
import math
import re
import statistics
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

from documentation_digester.digester import cleaner, embeddings, vector_store

HERE = Path(__file__).parent
GOLDEN_PATH = HERE / "golden_questions.json"
RESULTS_DIR = HERE / "results"
HEADING_KEYS = ("topic", "subtitle", "title")   # deepest heading first
FRAGMENT_CHARS = 50
MAX_CHARS = 1000
TEXT_MATCH_THRESHOLD = 0.8


# ---------- small pure helpers (unit tested) ----------

def squash(text: str) -> str:
    """Lowercase and drop all whitespace so formatting differences don't matter."""
    return "".join(text.split()).casefold()


def relative_page(source_path: str) -> str:
    """'C:\\...\\clean_html\\tutorials\\a.html' or 'tutorials/a.html' -> 'tutorials/a.html'."""
    path = source_path.replace("\\", "/")
    if "/clean_html/" in path:
        path = path.split("/clean_html/", 1)[1]
    return path.lstrip("./")


def chunk_section(metadata: dict) -> str:
    """The most specific heading a chunk sits under."""
    return next((metadata[key] for key in HEADING_KEYS if metadata.get(key)), "")


def hit_at(flags: list[bool], k: int) -> float:
    return 1.0 if any(flags[:k]) else 0.0


def reciprocal_rank(flags: list[bool]) -> float:
    return next((1 / rank for rank, ok in enumerate(flags, 1) if ok), 0.0)


def precision_at(flags: list[bool], k: int) -> float:
    return sum(flags[:k]) / k


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile: always a value that was really measured."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(pct / 100 * len(ordered)) - 1)]


def text_match_ratio(chunk_text: str, page_text_squashed: str, size: int = 5) -> float:
    """Share of the chunk's 5-word runs that appear on the page (tolerates small reordering)."""
    words = chunk_text.split()
    if len(words) < size:
        return 1.0 if squash(chunk_text) in page_text_squashed else 0.0
    runs = [squash(" ".join(words[i:i + size])) for i in range(len(words) - size + 1)]
    return sum(run in page_text_squashed for run in runs) / len(runs)


# ---------- reading the built docs ----------

class DocsPages:
    """Loads built HTML pages once and answers 'is this heading/text on that page?'."""

    def __init__(self, root: Path):
        self.root = root
        self._cache: dict[str, tuple[set[str], str] | None] = {}

    def _load(self, page: str):
        if page not in self._cache:
            path = self.root / page
            if not path.is_file():
                self._cache[page] = None
            else:
                soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
                main = soup.select_one('div.document[role="main"]') or soup
                for link in main.select(".headerlink"):
                    link.decompose()
                headings = {squash(h.get_text()) for h in main.find_all(["h1", "h2", "h3", "h4"])}
                self._cache[page] = (headings, squash(main.get_text()))
        return self._cache[page]

    def exists(self, page: str) -> bool:
        return self._load(page) is not None

    def has_heading(self, page: str, heading: str) -> bool:
        loaded = self._load(page)
        return bool(loaded) and squash(heading) in loaded[0]

    def text_ratio(self, page: str, text: str) -> float:
        loaded = self._load(page)
        return text_match_ratio(text, loaded[1]) if loaded else 0.0


# ---------- evaluation ----------

@dataclass
class Golden:
    id: str
    question: str
    page: str
    sections: list[str]


@dataclass
class Outcome:
    golden: Golden
    results: list[dict]
    section_flags: list[bool]
    page_flags: list[bool]
    citation_problems: list[list[str]] = field(default_factory=list)
    embed_ms: float = 0.0
    search_ms: float = 0.0


def load_golden(path: Path = GOLDEN_PATH) -> list[Golden]:
    return [Golden(**row) for row in json.loads(path.read_text(encoding="utf-8"))]


def check_golden(golden: list[Golden], docs: DocsPages) -> list[str]:
    """Labels that don't exist in this build (e.g. docs built from a different Godot version)."""
    problems = []
    for g in golden:
        if not docs.exists(g.page):
            problems.append(f"{g.id}: page not in build: {g.page}")
        elif not any(docs.has_heading(g.page, s) for s in g.sections):
            problems.append(f"{g.id}: section not on page: {g.sections}")
    return problems


def citation_problems(result: dict, docs: DocsPages) -> list[str]:
    page = relative_page(result["metadata"].get("source_path", ""))
    section = chunk_section(result["metadata"])
    if not page or not docs.exists(page):
        return [f"page not found: {page or '(none)'}"]
    problems = []
    if not section:
        problems.append("no section heading")
    elif not docs.has_heading(page, section):
        problems.append(f"section not on page: {section}")
    if docs.text_ratio(page, result["text"]) < TEXT_MATCH_THRESHOLD:
        problems.append("text doesn't match page")
    return problems


def run_question(g: Golden, k: int, docs: DocsPages) -> Outcome:
    start = time.perf_counter()
    vector = embeddings.embed_query(g.question)
    embedded = time.perf_counter()
    results = vector_store.search_chunks(vector, top_k=k)
    done = time.perf_counter()

    golden_sections = {squash(s) for s in g.sections}
    page_flags = [relative_page(r["metadata"].get("source_path", "")) == g.page for r in results]
    section_flags = [
        ok and squash(chunk_section(r["metadata"])) in golden_sections
        for ok, r in zip(page_flags, results)
    ]
    return Outcome(
        golden=g,
        results=results,
        section_flags=section_flags,
        page_flags=page_flags,
        citation_problems=[citation_problems(r, docs) for r in results],
        embed_ms=(embedded - start) * 1000,
        search_ms=(done - embedded) * 1000,
    )


def audit_chunks(batch_size: int = 5000) -> dict:
    """Index-wide chunk quality, read straight from Chroma."""
    collection = vector_store.get_collection()
    total = collection.count()
    lengths, keys, pages = [], Counter(), set()
    empty = fragments = heading_only = oversized = no_source = no_title = 0
    for offset in range(0, total, batch_size):
        batch = collection.get(include=["documents", "metadatas"], limit=batch_size, offset=offset)
        for text, meta in zip(batch["documents"], batch["metadatas"]):
            text, meta = (text or "").strip(), meta or {}
            length = len(text)
            lengths.append(length)
            empty += length == 0
            fragments += 0 < length < FRAGMENT_CHARS
            oversized += length > MAX_CHARS
            heading_only += bool(text) and squash(text) in {squash(meta.get(k, "")) for k in HEADING_KEYS}
            no_source += not meta.get("source_path")
            no_title += not meta.get("title")
            keys[(meta.get("source_path"), text)] += 1
            pages.add(meta.get("source_path"))
    return {
        "Total chunks": total,
        "Pages indexed": len(pages),
        "Empty": empty,
        f"Fragments under {FRAGMENT_CHARS} characters": fragments,
        "Chunks that are only a heading": heading_only,
        f"Over {MAX_CHARS} characters": oversized,
        "Duplicate chunks (same page and text)": sum(c - 1 for c in keys.values()),
        "Missing source_path": no_source,
        "Missing title": no_title,
        "Median characters": statistics.median(lengths) if lengths else 0,
        "95th percentile characters": percentile(lengths, 95) if lengths else 0,
    }


def time_api(api_url: str, questions: list[str]) -> list[float]:
    import httpx

    timings = []
    with httpx.Client(base_url=api_url, timeout=120) as client:
        for question in questions:
            start = time.perf_counter()
            client.post("/chat", json={"question": question}).raise_for_status()
            timings.append((time.perf_counter() - start) * 1000)
    return timings


# ---------- report ----------

def _row(*cells) -> str:
    return "| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in cells) + " |"


def _latency_rows(name: str, values: list[float]) -> str:
    return _row(name, len(values), f"{percentile(values, 50):.1f}", f"{percentile(values, 95):.1f}", f"{max(values):.1f}")


def build_report(outcomes, k, cold_ms, audit, skipped, api_ms, label) -> str:
    n = len(outcomes)

    def avg(fn):
        return sum(fn(o) for o in outcomes) / n

    lines = [f"# Retrieval evaluation", "",
             f"- Run: {datetime.now():%Y-%m-%d %H:%M}",
             f"- Questions scored: {n}" + (f" ({len(skipped)} skipped, see below)" if skipped else ""),
             f"- Results per question (k): {k}"]
    if label:
        lines.append(f"- Configuration: {label}")

    lines += ["", "## Search quality", "",
              "A hit means the right section (or page) appears in the top results. MRR rewards ranking it higher: "
              "1.0 means always first, 0.5 means second on average.", "",
              "| Metric | Right section | Right page |", "|---|---|---|"]
    for cut in sorted({1, 3, k}):
        lines.append(_row(f"Hit rate @{cut}", f"{avg(lambda o: hit_at(o.section_flags, cut)):.0%}",
                          f"{avg(lambda o: hit_at(o.page_flags, cut)):.0%}"))
    lines.append(_row(f"MRR @{k}", f"{avg(lambda o: reciprocal_rank(o.section_flags)):.2f}",
                      f"{avg(lambda o: reciprocal_rank(o.page_flags)):.2f}"))
    lines.append(_row(f"Precision @{k}", f"{avg(lambda o: precision_at(o.section_flags, k)):.2f}",
                      f"{avg(lambda o: precision_at(o.page_flags, k)):.2f}"))
    lines += ["", f"Precision @{k} can't go above {1 / k:.2f} for section matches when one section answers a question, "
                  "so hit rate and MRR are the better measures here."]

    checked = sum(len(o.citation_problems) for o in outcomes)
    bad = [p for o in outcomes for p in o.citation_problems if p]
    reasons = Counter(re.sub(r":.*", "", reason) for p in bad for reason in p)
    lines += ["", "## Citation accuracy", "",
              f"**{checked - len(bad)} of {checked}** returned results cite a page that exists, a heading on that page, "
              "and text that matches the page."]
    if reasons:
        lines += ["", "| Problem | Results |", "|---|---|"] + [_row(r, c) for r, c in reasons.most_common()]

    lines += ["", "## Latency", "", "Milliseconds per question, after one warm-up query.", "",
              "| Step | Runs | Median | 95th percentile | Max |", "|---|---|---|---|---|",
              _latency_rows("Embed question", [o.embed_ms for o in outcomes]),
              _latency_rows("Vector search", [o.search_ms for o in outcomes]),
              _latency_rows("Question to results", [o.embed_ms + o.search_ms for o in outcomes])]
    if api_ms:
        lines.append(_latency_rows("Full /chat call (includes the LLM)", api_ms))
    lines += ["", f"Cold start (loading the model and database on the first query): {cold_ms:.0f} ms."]

    lines += ["", "## Chunk quality", "", "| Check | Value |", "|---|---|"]
    lines += [_row(name, f"{value:,.0f}" if isinstance(value, (int, float)) else value) for name, value in audit.items()]

    lines += ["", "## Every question", "",
              "| # | Question | Expected section | Rank found | Top result |", "|---|---|---|---|---|"]
    for o in outcomes:
        rank = next((i for i, ok in enumerate(o.section_flags, 1) if ok), None)
        top = o.results[0] if o.results else None
        top_text = f"{relative_page(top['metadata'].get('source_path', ''))} — {chunk_section(top['metadata'])}" if top else "none"
        lines.append(_row(o.golden.id, o.golden.question, f"{o.golden.page} — {o.golden.sections[0]}",
                          rank or "missed", top_text))

    if skipped:
        lines += ["", "## Skipped questions", "",
                  "These labels don't match your build, probably because it uses a different Godot docs version.", ""]
        lines += [f"- {s}" for s in skipped]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval on the real index.")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--docs", type=Path, default=cleaner.DOCS_PATH, help="built HTML folder")
    parser.add_argument("--label", default="", help="describe this configuration in the report")
    parser.add_argument("--api-url", default="", help="also time the full /chat call, e.g. http://127.0.0.1:8000")
    args = parser.parse_args()

    if vector_store.get_collection().count() == 0:
        raise SystemExit("The index is empty. Run the pipeline first.")

    docs = DocsPages(args.docs)
    golden = load_golden()
    skipped = check_golden(golden, docs)
    skipped_ids = {s.split(":")[0] for s in skipped}
    golden = [g for g in golden if g.id not in skipped_ids]
    if not golden:
        raise SystemExit("No golden questions match this build. Check --docs.")

    print("Warming up (loads the model)...")
    start = time.perf_counter()
    vector_store.search_chunks(embeddings.embed_query("warm up"), top_k=args.k)
    cold_ms = (time.perf_counter() - start) * 1000

    print(f"Running {len(golden)} questions...")
    outcomes = [run_question(g, args.k, docs) for g in golden]

    print("Auditing chunks...")
    audit = audit_chunks()

    api_ms = []
    if args.api_url:
        print("Timing the API...")
        api_ms = time_api(args.api_url, [g.question for g in golden])

    report = build_report(outcomes, args.k, cold_ms, audit, skipped, api_ms, args.label)
    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / f"report_{datetime.now():%Y%m%d_%H%M%S}.md"
    out.write_text(report, encoding="utf-8")

    section_hit = sum(hit_at(o.section_flags, args.k) for o in outcomes) / len(outcomes)
    print(f"\nRight section in top {args.k}: {section_hit:.0%}")
    print(f"Report saved to {out}")


if __name__ == "__main__":
    main()