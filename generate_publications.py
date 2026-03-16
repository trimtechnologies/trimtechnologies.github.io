#!/usr/bin/env python3
"""
generate_publications.py
────────────────────────
Reads publications.bib and injects a JavaScript array (PUBLICATIONS_DATA)
into index.html so that the website renders from the .bib file without
any live API calls.

Usage:
    python generate_publications.py

Requirements:
    pip install bibtexparser

Folder layout expected:
    your-site/
    ├── index.html          ← template (contains the <!--PUBLICATIONS_DATA--> marker)
    ├── style.css
    ├── publications.bib    ← your BibTeX database
    ├── generate_publications.py
    └── pdf/                ← place your PDF files here
        ├── okey2022boostedenml.pdf
        └── ...

Custom BibTeX fields recognised:
    featured   = {true|false}   whether to show in the "Featured" default view
    pdf        = {filename.pdf} path relative to /pdf/ folder
    thumb      = {filename.png} path relative to /assets/img/pubs/
    code       = {https://...}  link to code repository
    html       = {https://...}  link to project / paper webpage
    authorlinks = {Name1:url1, Name2:url2}  hyperlinks for individual authors
"""

import json
import re
import sys
import os

try:
    import bibtexparser
    from bibtexparser.bparser import BibTexParser
    from bibtexparser.customization import convert_to_unicode
except ImportError:
    print("ERROR: bibtexparser not found.\nRun:  pip install bibtexparser")
    sys.exit(1)

# ── Config ────────────────────────────────────────────────────────────────────
BIB_FILE   = "publications.bib"
HTML_IN    = "index.html"
HTML_OUT   = "index.html"          # overwrite in place (keep a backup first!)
MARKER     = "/*PUBLICATIONS_DATA*/"   # placeholder inside index.html JS block

# Venue classifications (substring match, case-insensitive)
JOURNAL_KEYWORDS = [
    "access", "sensors", "sustainability", "computers", "computer communications",
    "expert systems", "journal", "transactions", "letters", "review", "magazine",
    "signal processing", "electronic imaging", "abuad", "infocomp",
]
CONFERENCE_KEYWORDS = [
    "conference", "symposium", "workshop", "proceedings", "iswcs", "softcom",
    "cyber nigeria", "igarss", "icassp",
]

def classify(entry):
    etype = entry.get("ENTRYTYPE", "").lower()
    if etype in ("article",):
        return "journal"
    if etype in ("inproceedings", "proceedings"):
        return "conference"
    venue = (entry.get("journal", "") + entry.get("booktitle", "")).lower()
    for kw in JOURNAL_KEYWORDS:
        if kw in venue:
            return "journal"
    for kw in CONFERENCE_KEYWORDS:
        if kw in venue:
            return "conference"
    return "other"

def clean(text):
    """Strip LaTeX commands and braces."""
    text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)  # \cmd{x} → x
    text = re.sub(r'\{([^}]*)\}', r'\1', text)              # {x}     → x
    text = re.sub(r'\\["\'^`~=.](.)' , r'\1', text)        # accents
    text = text.replace("\\&", "&").replace("\\%", "%")
    return text.strip()

def parse_authors(raw):
    """Return list of author name strings."""
    parts = [p.strip() for p in raw.split(" and ")]
    names = []
    for p in parts:
        if "," in p:
            last, first = p.split(",", 1)
            names.append(f"{first.strip()} {last.strip()}")
        else:
            names.append(p)
    return [clean(n) for n in names]

def parse_authorlinks(raw):
    """Parse 'LastName1:url1, LastName2:url2' into a dict."""
    links = {}
    if not raw:
        return links
    for item in raw.split(","):
        item = item.strip()
        if ":" in item:
            key, url = item.split(":", 1)
            links[key.strip()] = url.strip()
    return links

def build_bibtex_string(entry):
    """Re-emit a clean BibTeX string for the modal display."""
    etype = entry.get("ENTRYTYPE", "misc")
    key   = entry.get("ID", "unknown")
    skip  = {"ENTRYTYPE", "ID", "featured", "pdf", "thumb", "code",
              "html", "authorlinks"}
    lines = [f"@{etype}{{{key},"]
    for field, val in entry.items():
        if field in skip:
            continue
        val = clean(val)
        lines.append(f"  {field:<12} = {{{val}}},")
    lines.append("}")
    return "\n".join(lines)

def entry_to_dict(entry):
    authors_raw = entry.get("author", "")
    authors     = parse_authors(authors_raw)
    alinks_raw  = entry.get("authorlinks", "")
    alinks      = parse_authorlinks(alinks_raw)

    # venue string
    venue = clean(entry.get("journal", entry.get("booktitle", "")))
    vol   = entry.get("volume", "")
    num   = entry.get("number", "")
    pages = entry.get("pages", "")
    if vol:
        venue += f", Vol. {vol}"
    if num:
        venue += f" ({num})"
    if pages:
        venue += f", pp. {pages}"

    return {
        "id":          entry.get("ID", ""),
        "title":       clean(entry.get("title", "")),
        "authors":     authors,
        "authorlinks": alinks,
        "venue":       venue,
        "year":        int(entry.get("year", 0)),
        "type":        classify(entry),
        "doi":         entry.get("doi", ""),
        "abstract":    clean(entry.get("abstract", "")),
        "featured":    entry.get("featured", "false").strip().lower() == "true",
        "pdf":         entry.get("pdf", ""),
        "thumb":       entry.get("thumb", ""),
        "code":        entry.get("code", ""),
        "html":        entry.get("html", ""),
        "bibtex":      build_bibtex_string(entry),
    }

def main():
    # ── Parse BibTeX ──────────────────────────────────────────────────────────
    if not os.path.exists(BIB_FILE):
        print(f"ERROR: {BIB_FILE} not found.")
        sys.exit(1)

    parser = BibTexParser(common_strings=True)
    parser.customization = convert_to_unicode
    with open(BIB_FILE, encoding="utf-8") as f:
        bib_db = bibtexparser.load(f, parser=parser)

    pubs = [entry_to_dict(e) for e in bib_db.entries]
    # sort newest first
    pubs.sort(key=lambda p: p["year"], reverse=True)

    js_array = json.dumps(pubs, indent=2, ensure_ascii=False)
    injection = f"const LOCAL_PUBS = {js_array};"

    # ── Inject into HTML ──────────────────────────────────────────────────────
    if not os.path.exists(HTML_IN):
        print(f"ERROR: {HTML_IN} not found.")
        sys.exit(1)

    with open(HTML_IN, encoding="utf-8") as f:
        html = f.read()

    if MARKER not in html:
        print(f"ERROR: marker '{MARKER}' not found in {HTML_IN}.\n"
              f"Make sure the script block in index.html starts with {MARKER}")
        sys.exit(1)

    # Replace everything between /*PUBLICATIONS_DATA*/ and the next semicolon-terminated array
    pattern = r'/\*PUBLICATIONS_DATA\*/.*?(?=\n// ──)'
    replacement = injection
    new_html = re.sub(pattern, replacement, html, flags=re.DOTALL)
    if new_html == html:
        # Fallback: simple text replacement of just the marker line
        new_html = html.replace(MARKER, injection.rstrip(";"))

    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"✓  Processed {len(pubs)} publications from {BIB_FILE}")
    print(f"✓  Written to {HTML_OUT}")
    featured = sum(1 for p in pubs if p["featured"])
    print(f"   {featured} featured  |  {len(pubs)-featured} hidden (set featured=true to show)")

if __name__ == "__main__":
    main()
