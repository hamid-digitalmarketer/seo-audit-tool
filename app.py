"""SEO Audit and Website Health Checker - Streamlit application.

Run with: streamlit run app.py
"""
from __future__ import annotations

import io

import pandas as pd
import plotly.express as px
import streamlit as st

from seo_audit.analyzer import aggregate
from seo_audit.fetcher import crawl, fetch_robots, fetch_sitemap

st.set_page_config(page_title="SEO Audit Tool", page_icon="🔍", layout="wide")

st.title("SEO Audit and Website Health Checker")
st.caption(
    "Ethical on-page SEO audit: crawl internal pages, check metadata, headings, "
    "canonicals, indexability, image alt text, robots.txt and sitemap.xml."
)

with st.form("audit_form"):
    url = st.text_input("Website URL", placeholder="https://example.com")
    max_pages = st.slider("Maximum pages to crawl", min_value=1, max_value=100, value=25)
    include_robots = st.checkbox("Check robots.txt and sitemap.xml", value=True)
    submitted = st.form_submit_button("Run Audit", type="primary")

if submitted:
    if not url.startswith(("http://", "https://")):
        st.error("Please enter a valid URL starting with http:// or https://")
        st.stop()

    with st.spinner(f"Crawling up to {max_pages} pages (this can take a while)..."):
        documents, fetch_errors = crawl(url, max_pages=max_pages, delay=0.5)

    if not documents:
        st.error("No pages could be fetched. Check the URL, or the site may block automated requests.")
        if fetch_errors:
            st.info("Fetch errors:\n" + "\n".join(f"- {e}" for e in fetch_errors[:20]))
        st.stop()

    result = aggregate([analyze_doc(u, h) for u, h in documents])

    st.success(f"Audited {result['total_pages']} page(s)")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pages audited", result["total_pages"])
    c2.metric("Critical", result["issue_counts"]["critical"])
    c3.metric("Warnings", result["issue_counts"]["warning"])
    c4.metric("Info", result["issue_counts"]["info"])

    if include_robots:
        robots_text, robots_ok = fetch_robots(url)
        sitemap_text, sitemap_ok = fetch_sitemap(url)
        r1, r2 = st.columns(2)
        r1.metric("robots.txt", "Found" if robots_ok else "Missing/Blocked")
        r2.metric("sitemap.xml", "Found" if sitemap_ok else "Missing/Blocked")

    st.subheader("Issues by category")
    cat_df = pd.DataFrame(
        [{"category": cat, "count": n} for cat, n in sorted(result["categories"].items(), key=lambda kv: -kv[1])]
    )
    if not cat_df.empty:
        fig = px.bar(cat_df, x="category", y="count", title="Issue counts by category")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Prioritized issues")
    rows = [i.as_row() + [p.url] for p in result["pages"] for i in p.issues]
    issues_df = pd.DataFrame(rows, columns=["Severity", "Category", "Message", "Recommendation", "URL"])
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    issues_df["_order"] = issues_df["Severity"].map(severity_order).fillna(3)
    issues_df = issues_df.sort_values("_order").drop(columns="_order")

    severity_filter = st.multiselect("Filter by severity", ["critical", "warning", "info"], default=["critical", "warning", "info"])
    filtered = issues_df[issues_df["Severity"].isin(severity_filter)]
    st.dataframe(filtered, use_container_width=True, hide_index=True)

    csv_buffer = io.StringIO()
    filtered.to_csv(csv_buffer, index=False)
    st.download_button(
        "Download issues as CSV",
        data=csv_buffer.getvalue(),
        file_name="seo_audit_issues.csv",
        mime="text/csv",
    )

    if fetch_errors:
        with st.expander(f"Fetch errors ({len(fetch_errors)})"):
            st.write("\n".join(f"- {e}" for e in fetch_errors[:50]))


def analyze_doc(u: str, h: str):
    """Small helper so aggregate() receives PageData objects."""
    from seo_audit.analyzer import analyze_html

    return analyze_html(h, u)
