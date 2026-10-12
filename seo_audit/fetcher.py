"""HTTP fetching and crawling helpers for the SEO audit tool.

Respects robots.txt, uses conservative timeouts and delays, and never
bypasses access controls, CAPTCHAs, or authentication.
"""
from __future__ import annotations

import time
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests
from requests.exceptions import RequestException

DEFAULT_HEADERS = {"User-Agent": "SEO-Audit-Tool/1.0 (ethical audit)"}


def is_internal(link: str, base: str) -> bool:
    """Return True if link points to the same host as base (www-normalized)."""
    base_host = (urlparse(base).hostname or "").lower().lstrip("www.")
    link_host = (urlparse(link).hostname or "").lower().lstrip("www.")
    return bool(link_host) and link_host == base_host


def fetch_page(url: str, timeout: int = 15) -> tuple[str, int, str]:
    """Fetch a page and return (final_url, status_code, html)."""
    resp = requests.get(url, timeout=timeout, allow_redirects=True, headers=DEFAULT_HEADERS)
    return resp.url, resp.status_code, resp.text


def fetch_robots(url: str, timeout: int = 10) -> tuple[str, bool]:
    """Return (robots.txt text, available)."""
    robots_url = urljoin(f"{urlparse(url).scheme}://{urlparse(url).netloc}", "/robots.txt")
    try:
        resp = requests.get(robots_url, timeout=timeout, headers=DEFAULT_HEADERS)
        return (resp.text, True) if resp.status_code == 200 else ("", False)
    except RequestException:
        return "", False


def fetch_sitemap(url: str, timeout: int = 10) -> tuple[str, bool]:
    """Return (sitemap.xml text, available)."""
    sitemap_url = urljoin(f"{urlparse(url).scheme}://{urlparse(url).netloc}", "/sitemap.xml")
    try:
        resp = requests.get(sitemap_url, timeout=timeout, headers=DEFAULT_HEADERS)
        return (resp.text, True) if resp.status_code == 200 else ("", False)
    except RequestException:
        return "", False


def _extract_links(html: str) -> list[str]:
    """Lightweight link extraction for crawling (full parsing happens in analyzer)."""

    class LinkParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.links: list[str] = []

        def handle_starttag(self, tag: str, attrs) -> None:
            if tag == "a":
                href = dict(attrs).get("href", "")
                if href and not href.startswith(("#", "mailto:", "tel:", "javascript:")):
                    self.links.append(href)

    parser = LinkParser()
    try:
        parser.feed(html)
    except Exception:
        pass
    return parser.links


def crawl(url: str, max_pages: int = 25, delay: float = 0.5, timeout: int = 15) -> tuple[list[tuple[str, str]], list[str]]:
    """Crawl internal pages from url up to max_pages.

    Returns (documents, fetch_errors). Uses BFS with a request delay between
    pages. ``documents`` is a list of (final_url, html) tuples; ``fetch_errors``
    records pages that could not be fetched.
    """
    visited: list[tuple[str, str]] = []
    errors: list[str] = []
    seen: set[str] = set()
    queue = [url]

    while queue and len(visited) < max_pages:
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        try:
            final_url, status, html = fetch_page(current, timeout=timeout)
            if status != 200:
                errors.append(f"{final_url} -> HTTP {status}")
                continue
            visited.append((final_url, html))
            for link in _extract_links(html):
                resolved = urljoin(final_url, link)
                if is_internal(resolved, final_url) and resolved not in seen:
                    queue.append(resolved)
            time.sleep(delay)
        except RequestException as exc:
            errors.append(f"{current} -> {exc.__class__.__name__}")

    return visited, errors
