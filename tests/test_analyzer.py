"""Unit tests for seo_audit.analyzer."""

import pytest

from seo_audit.analyzer import analyze_html, aggregate, PageData


GOOD_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Professional SEO Audit Tool - Example Page Title</title>
    <meta name="description" content="This is a sufficiently long meta description for the example page that helps demonstrate the audit logic.">
    <link rel="canonical" href="https://example.com/page">
</head>
<body>
    <h1>Example Page</h1>
    <h2>Sub section</h2>
    <p><a href="/other">Internal link</a></p>
    <img src="/img/a.png" alt="Description of image a">
</body>
</html>
"""

BAD_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Short</title>
    <meta name="robots" content="noindex">
</head>
<body>
    <img src="/img/missing-alt.png">
    <a href="#fragment">Anchor</a>
</body>
</html>
"""


def test_good_html_has_no_critical_issues():
    page = analyze_html(GOOD_HTML, "https://example.com/page")
    assert all(i.severity != "critical" for i in page.issues)


def test_missing_title_is_critical():
    page = analyze_html("<html><body><h1>Hi</h1></body></html>", "https://example.com/")
    titles = [i for i in page.issues if i.category == "Title"]
    assert any(i.severity == "critical" for i in titles)


def test_noindex_detected():
    page = analyze_html('<html><head><meta name="robots" content="noindex"></head></html>')
    assert page.noindex is True
    assert any(i.category == "Indexability" for i in page.issues)


def test_missing_alt_detected():
    page = analyze_html('<html><body><img src="/a.png"></body></html>')
    assert any(i.category == "Images" for i in page.issues)


def test_multiple_h1_detected():
    page = analyze_html("<html><body><h1>One</h1><h1>Two</h1></body></html>")
    assert any("Multiple H1" in i.message for i in page.issues)


def test_duplicate_titles_across_pages():
    p1 = analyze_html("<html><head><title>Same Title</title></head></html>", "https://example.com/a")
    p2 = analyze_html("<html><head><title>Same Title</title></head></html>", "https://example.com/b")
    result = aggregate([p1, p2])
    assert result["duplicate_titles"]
    assert any("duplicated" in i.message for i in result["issues"])


def test_aggregate_counts():
    p1 = analyze_html(BAD_HTML, "https://example.com/a")
    p2 = analyze_html(BAD_HTML, "https://example.com/b")
    result = aggregate([p1, p2])
    assert result["total_pages"] == 2
    assert result["issue_counts"]["critical"] >= 2
