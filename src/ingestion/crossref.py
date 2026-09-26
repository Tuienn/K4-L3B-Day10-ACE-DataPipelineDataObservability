from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
import re
import time
import requests

from core.config import Settings

logger = logging.getLogger(__name__)


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


def _clean_text(text: str) -> str:
    """Loại bỏ thẻ XML/HTML (như <jats:p>) và chuẩn hóa khoảng trắng."""
    cleaned = re.sub(r"<[^>]+>", " ", text)
    return " ".join(cleaned.split())


def _extract_date(date_dict: dict | None) -> str:
    """Trích xuất ngày dạng YYYY-MM-DD từ cấu trúc date của Crossref."""
    if not date_dict or not isinstance(date_dict, dict):
        return ""
    date_parts = date_dict.get("date-parts", [])
    if date_parts and isinstance(date_parts, list) and len(date_parts) > 0:
        parts = date_parts[0]
        if isinstance(parts, list) and len(parts) >= 1:
            year = parts[0]
            month = parts[1] if len(parts) >= 2 else 1
            day = parts[2] if len(parts) >= 3 else 1
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    dt = date_dict.get("date-time")
    if dt and isinstance(dt, str):
        return dt.split("T")[0]
    return ""


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    """Bóc tách cấu trúc payload JSON từ API Crossref thành danh sách các đối tượng PaperRecord.

    1. Duyệt `payload["message"]["items"]`.
    2. Lấy DOI, title, abstract, authors, subject, dates, URLs.
    3. Chuẩn hóa text và loại bỏ các thẻ HTML/XML rác như <jats:p>.
    4. Trả về list `PaperRecord`.
    """
    items = []
    if isinstance(payload, dict):
        message = payload.get("message")
        if isinstance(message, dict):
            items = message.get("items", [])
        elif "items" in payload:
            items = payload.get("items", [])
    elif isinstance(payload, list):
        items = payload

    records: list[PaperRecord] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        paper_id = str(item.get("DOI", "")).strip()
        if not paper_id:
            continue

        # Title
        raw_title = item.get("title", "")
        if isinstance(raw_title, list):
            raw_title = raw_title[0] if raw_title else ""
        title = _clean_text(str(raw_title))
        if not title:
            continue

        # Summary / Abstract
        raw_abstract = item.get("abstract", "") or ""
        summary = _clean_text(str(raw_abstract))

        # Authors
        authors: list[str] = []
        for author in item.get("author", []):
            if isinstance(author, dict):
                given = author.get("given", "").strip()
                family = author.get("family", "").strip()
                name = " ".join(part for part in [given, family] if part)
                if name:
                    authors.append(name)
            elif isinstance(author, str) and author.strip():
                authors.append(author.strip())

        # Categories
        categories = [str(cat).strip() for cat in item.get("subject", []) if str(cat).strip()]
        primary_category = categories[0] if categories else ""

        # Published & Updated
        published = (
            _extract_date(item.get("published"))
            or _extract_date(item.get("created"))
            or _extract_date(item.get("deposited"))
        )
        updated = _extract_date(item.get("updated")) or published

        # URLs
        url = item.get("URL") or f"https://doi.org/{paper_id}"

        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                abs_url=url,
                pdf_url=url,
                comment=f"Crossref record {paper_id}",
            )
        )

    return records


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    """Gọi API Crossref (hoặc kích hoạt fallback đọc snapshot mẫu), lưu JSON gốc
    vào data/raw/crossref_response.json và lưu danh sách records vào data/raw/crossref_records.json.
    """
    raw_response_path = settings.paths.raw_api_response
    raw_records_path = settings.paths.raw_records_json

    payload: dict | None = None
    should_fetch = settings.refresh_source or not raw_response_path.exists()

    if should_fetch:
        endpoint = "https://api.crossref.org/works"
        params: dict[str, str | int] = {
            "query": settings.source_query,
            "rows": settings.max_results,
        }
        if settings.source_filter:
            params["filter"] = settings.source_filter

        headers = {
            "User-Agent": "DataObservabilityLab/1.0 (mailto:student@example.com)"
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(endpoint, params=params, headers=headers, timeout=15)
                if response.status_code == 200:
                    payload = response.json()
                    break
                elif response.status_code in {429, 503}:
                    logger.warning("Crossref API rate limit hit (%d). Retrying...", response.status_code)
                    time.sleep(2**attempt)
                else:
                    logger.warning("Crossref API returned status %d", response.status_code)
                    break
            except requests.RequestException as e:
                logger.warning("Error connecting to Crossref API: %s. Attempt %d/%d", e, attempt + 1, max_retries)
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)

    if payload is not None:
        raw_response_path.parent.mkdir(parents=True, exist_ok=True)
        with open(raw_response_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    elif raw_response_path.exists():
        with open(raw_response_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    else:
        raise RuntimeError("Failed to fetch from Crossref API and no local snapshot available.")

    records = parse_crossref_payload(payload)

    raw_records_path.parent.mkdir(parents=True, exist_ok=True)
    with open(raw_records_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, ensure_ascii=False, indent=2)

    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    """Đọc JSON snapshot và map thành danh sách `PaperRecord`."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return [PaperRecord(**item) for item in data]
    elif isinstance(data, dict):
        return parse_crossref_payload(data)
    return []
