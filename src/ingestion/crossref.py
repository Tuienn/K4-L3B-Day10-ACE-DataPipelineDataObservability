from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from html.parser import HTMLParser
import json
import logging
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.config import Settings
from core.utils import ensure_parent, normalize_whitespace, write_json


class _PlainTextParser(HTMLParser):
    """Keep text content while separating adjacent HTML/JATS paragraphs."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag.split(":")[-1] in {"p", "br", "div", "title", "sec", "li"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        self.handle_starttag(tag, [])


def _text(value: object) -> str:
    if not isinstance(value, str):
        return ""
    parser = _PlainTextParser()
    parser.feed(value)
    parser.close()
    return normalize_whitespace("".join(parser.parts))


def _date(value: object) -> str:
    if not isinstance(value, dict):
        return ""
    parts = value.get("date-parts")
    if isinstance(parts, list) and parts and isinstance(parts[0], list):
        fields = parts[0]
        if 1 <= len(fields) <= 3 and all(type(field) is int for field in fields):
            try:
                return date(*(fields + [1] * (3 - len(fields)))).isoformat()
            except ValueError:
                pass
    timestamp = value.get("date-time")
    if isinstance(timestamp, str):
        try:
            return date.fromisoformat(timestamp[:10]).isoformat()
        except ValueError:
            pass
    return ""


def _items(payload: dict) -> list:
    message = payload.get("message") if isinstance(payload, dict) else None
    items = message.get("items") if isinstance(message, dict) else None
    if not isinstance(items, list):
        raise ValueError("Expected a Crossref work-list payload with message.items.")
    return items


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Parse a Crossref work-list; skip items without a DOI or title.

    Pseudo-code:
    1. Duyet `payload["message"]["items"]`.
    2. Lay DOI, title, abstract, authors, subject, dates, URLs.
    3. Chuan hoa text va bo record khong hop le.
    4. Tra ve list `PaperRecord`.
    """
    records = []
    for item in _items(payload):
        if not isinstance(item, dict):
            continue
        paper_id = _text(item.get("DOI"))
        titles = item.get("title", [])
        if isinstance(titles, str):
            titles = [titles]
        title = next((_text(value) for value in titles if _text(value)), "") if isinstance(titles, list) else ""
        if not paper_id or not title:
            continue

        authors = []
        author_items = item.get("author") or []
        for author in author_items if isinstance(author_items, list) else []:
            if not isinstance(author, dict):
                continue
            name = normalize_whitespace(" ".join(
                part for part in (_text(author.get("given")), _text(author.get("family"))) if part
            )) or _text(author.get("name"))
            if name:
                authors.append(name)
        subjects = item.get("subject") or []
        if isinstance(subjects, str):
            subjects = [subjects]
        categories = [_text(value) for value in subjects if _text(value)] if isinstance(subjects, list) else []
        published = next((value for key in (
            "published", "published-online", "published-print", "issued", "created"
        ) if (value := _date(item.get(key)))), "")
        updated = next((value for key in ("deposited", "indexed", "created")
                        if (value := _date(item.get(key)))), published)
        abs_url = _text(item.get("URL")) or f"https://doi.org/{paper_id}"
        links = item.get("link") or []
        pdf_url = next((_text(link.get("URL")) for link in links
                        if isinstance(link, dict) and link.get("content-type") == "application/pdf"
                        and _text(link.get("URL"))), abs_url) if isinstance(links, list) else abs_url
        records.append(PaperRecord(
            paper_id=paper_id, title=title, summary=_text(item.get("abstract")),
            authors=authors, categories=categories,
            primary_category=categories[0] if categories else "",
            published=published, updated=updated, abs_url=abs_url, pdf_url=pdf_url,
            comment=f"Crossref record {paper_id}",
        ))
    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Fetch Crossref or use the existing offline snapshot, saving both artifacts.

    Pseudo-code:
    1. Tao params tu `settings.source_query`, `settings.source_filter`, `settings.max_results`.
    2. Goi API voi retry cho cac status code nhu 429/503.
    3. Luu raw response vao `settings.paths.raw_api_response`.
    4. Parse payload bang `parse_crossref_payload`.
    5. Luu records vao `settings.paths.raw_records_json`.
    """
    raw_path = settings.paths.raw_api_response
    if not settings.refresh_source and raw_path.exists():
        raw_content = raw_path.read_bytes()
        payload = json.loads(raw_content)
    else:
        params = {"query": settings.source_query, "rows": settings.max_results}
        if settings.source_filter:
            params["filter"] = settings.source_filter
        retry = Retry(
            total=3, backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504), allowed_methods={"GET"},
            respect_retry_after_header=True,
        )
        try:
            with requests.Session() as session:
                session.mount("https://", HTTPAdapter(max_retries=retry))
                response = session.get(
                    "https://api.crossref.org/works", params=params, timeout=(10, 60),
                    headers={"User-Agent": "day10-data-observability-lab/0.1"},
                )
                response.raise_for_status()
                raw_content = response.content
                payload = json.loads(raw_content)
                _items(payload)
        except (requests.RequestException, ValueError) as exc:
            if not raw_path.exists():
                raise
            logging.getLogger(__name__).warning(
                "Crossref request failed; using snapshot %s: %s", raw_path, exc
            )
            raw_content = raw_path.read_bytes()
            payload = json.loads(raw_content)

    records = parse_crossref_payload(payload)
    ensure_parent(raw_path)
    raw_path.write_bytes(raw_content)
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """TODO(student): doc JSON snapshot va map thanh `PaperRecord`."""
    raise NotImplementedError("Student task: implement raw record loading.")
