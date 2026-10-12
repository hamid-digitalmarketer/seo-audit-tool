"""Core SEO audit analysis engine.

Parses HTML and produces structured findings about on-page SEO signals.
Uses only the Python standard library for parsing so the core logic is
portable and easy to test.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser

DEFAULT_TITLE_MIN = 30
DEFAULT_TITLE_MAX = 60
DEFAULT_DESC_MIN = 70
DEFAULT_DESC_MAX = 160


@dataclass
class Issue:
    """A single SEO finding."""

    severity: str  # "critical" | "warning" | "info"
    category: str
    message: str
    recommendation: str

    def as_row(self) -> list[str]:
        return [self.severity, self.category, self.message, self.recommendation]


@dataclass
class PageData:
    """Parsed on-page signals for one page."""

    url: str
    title: str = ""
    meta_description: str = ""
    canonical: str = ""
    noindex: bool = False
    h1: list[str] = field(default_factory=list)
    h2: list[str] = field(default_factory=list)
    images: list[tuple[str, str]] = field(default_factory=list)  # (src, alt)
    links: list[str] = field(default_factory=list)
    status: int = 200
    final_url: str = ""
    issues: list[Issue] = field(default_factory=list)


class _SeoParser(HTMLParser):
    """Collects SEO-relevant signals from one HTML document."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.titles: list[str] = []
        self.meta_desc: str | None = None
        self.canonical: str | None = None
        self.noindex = False
        self.h1: list[str] = []
        self.h2: list[str] = []
        self.images: list[tuple[str, str]] = []
        self.links: list[str] = []
        self._in_title = False
        self._in_h1 = False
        self._in_h2 = False

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "h1":
            self._in_h1 = True
            self.h1.append("")
        elif tag == "h2":
            self._in_h2 = True
            self.h2.append("")
        elif tag == "meta":
            name = (attrs.get("name") or "").lower()
            prop = (attrs.get("property") or "").lower()
            content = attrs.get("content", "")
            if name == "description" and not self.meta_desc:
                self.meta_desc = content
            elif name == "robots" and "noindex" in content.lower():
                self.noindex = True
            elif prop == "og:description" and not self.meta_desc:
                self.meta_desc = content
        elif tag == "link" and (attrs.get("rel") or "").lower() == "canonical":
            self.canonical = attrs.get("href", "")
        elif tag == "img":
            src = attrs.get("src", "")
            alt = attrs.get("alt", "")
            self.images.append((src, alt))
        elif tag == "a":
            href = attrs.get("href", "")
            if href and not href.startswith(("#", "mailto:", "tel:", "javascript:")):
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "h1":
            self._in_h1 = False
        elif tag == "h2":
            self._in_h2 = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.titles.append(data)
        elif self._in_h1 and self.h1:
            self.h1[-1] += data
        elif self._in_h2 and self.h2:
            self.h2[-1] += data


def analyze_html(html: str, url: str = "https://example.com/", limits: dict | None = None) -> PageData:
    """Analyze a single HTML document and return PageData with issues."""
    limits = limits or {}
    title_min = limits.get("title_min", DEFAULT_TITLE_MIN)
    title_max = limits.get("title_max", DEFAULT_TITLE_MAX)
    desc_min = limits.get("desc_min", DEFAULT_DESC_MIN)
    desc_max = limits.get("desc_max", DEFAULT_DESC_MAX)

    parser = _SeoParser()
    try:
        parser.feed(html)
    except Exception:
        parser = _SeoParser()

    title = " ".join(" ".join(parser.titles).split()).strip()
    meta_description = (parser.meta_desc or "").strip()
    canonical = (parser.canonical or "").strip()

    page = PageData(
        url=url,
        title=title,
        meta_description=meta_description,
        canonical=canonical,
        noindex=parser.noindex,
        h1=[h.strip() for h in parser.h1 if h.strip()],
        h2=[h.strip() for h in parser.h2 if h.strip()],
        images=parser.images,
        links=parser.links,
        final_url=url,
    )

    if not title:
        page.issues.append(
            Issue("critical", "Title", "Page title is missing.", "Add a unique, descriptive title (30-60 characters).")
        )
    else:
        if len(title) < title_min:
            page.issues.append(
                Issue("warning", "Title", f"Title is too short ({len(title)} chars).", f"Aim for {title_min}-{title_max} characters.")
            )
        if len(title) > title_max:
            page.issues.append(
                Issue("warning", "Title", f"Title is too long ({len(title)} chars).", f"Keep titles under {title_max} characters to avoid truncation.")
            )

    if not meta_description:
        page.issues.append(
            Issue("warning", "Meta description", "Meta description is missing.", "Add a compelling 70-160 character description.")
        )
    else:
        if len(meta_description) < desc_min:
            page.issues.append(
                Issue("info", "Meta description", f"Meta description is short ({len(meta_description)} chars).", f"Expand toward {desc_min}-{desc_max} characters.")
            )
        if len(meta_description) > desc_max:
            page.issues.append(
                Issue("warning", "Meta description", f"Meta description is too long ({len(meta_description)} chars).", f"Keep descriptions under {desc_max} characters.")
            )

    if not page.h1:
        page.issues.append(Issue("warning", "Headings", "No H1 heading found.", "Add exactly one H1 that summarizes the page topic."))
    elif len(page.h1) > 1:
        page.issues.append(Issue("warning", "Headings", f"Multiple H1 headings found ({len(page.h1)}).", "Use one H1 per page; use H2/H3 for sub-sections."))

    if not canonical:
        page.issues.append(
            Issue("info", "Canonical", "Canonical URL not declared.", "Add a self-referencing canonical URL to prevent duplicate-content issues.")
        )
    if page.noindex:
        page.issues.append(Issue("info", "Indexability", "Page is marked noindex.", "Remove noindex if the page should appear in search results."))

    missing_alt = [src for src, alt in page.images if not alt.strip()]
    if missing_alt:
        page.issues.append(
            Issue("warning", "Images", f"{len(missing_alt)} image(s) missing alt text.", "Add descriptive alt attributes to every meaningful image.")
        )

    return page


def aggregate(pages: list[PageData]) -> dict:
    """Aggregate per-page issues and detect cross-page problems."""
    by_page = {p.url: p for p in pages}

    title_counts: dict[str, list[str]] = {}
    for p in pages:
        if p.title:
            title_counts.setdefault(p.title.lower(), []).append(p.url)
    duplicates = {t: urls for t, urls in title_counts.items() if len(urls) > 1}

    desc_counts: dict[str, list[str]] = {}
    for p in pages:
        if p.meta_description:
            desc_counts.setdefault(p.meta_description.lower(), []).append(p.url)
    desc_dups = {d: urls for d, urls in desc_counts.items() if len(urls) > 1}

    for urls in duplicates.values():
        for u in urls:
            by_page[u].issues.append(
                Issue("warning", "Duplicate title", f"Title is duplicated across {len(urls)} pages.", "Make each page title unique.")
            )
    for urls in desc_dups.values():
        for u in urls:
            by_page[u].issues.append(
                Issue("warning", "Duplicate meta description", f"Meta description duplicated across {len(urls)} pages.", "Write unique descriptions per page.")
            )

    all_issues = [i for p in pages for i in p.issues]
    counts = {"critical": 0, "warning": 0, "info": 0}
    categories: dict[str, int] = {}
    for i in all_issues:
        counts[i.severity] += 1
        categories[i.category] = categories.get(i.category, 0) + 1

    return {
        "pages": pages,
        "by_page": by_page,
        "total_pages": len(pages),
        "issue_counts": counts,
        "categories": categories,
        "issues": all_issues,
        "duplicate_titles": duplicates,
        "duplicate_descriptions": desc_dups,
    }
