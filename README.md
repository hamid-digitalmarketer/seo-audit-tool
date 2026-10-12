# SEO Audit and Website Health Checker

An ethical, configurable on-page SEO audit application built with Python and Streamlit. Enter a website URL, and the tool crawls internal pages, checks key on-page signals, and produces a prioritized list of issues with recommendations, a summary dashboard, and CSV export.

## Problem it solves

SEO audits are usually manual, slow, and expensive. This tool automates the first-pass technical audit: it catches missing titles and meta descriptions, duplicate titles, weak heading structure, missing canonical tags, images without alt text, broken fetches, and missing `robots.txt` / `sitemap.xml` — then presents everything in a recruiter-friendly, actionable dashboard.

## Key features

- Crawl accessible internal pages within a configurable limit (BFS with polite delays)
- Analyze page titles, meta descriptions, H1/H2 headings, canonical URLs, and indexability signals
- Detect images missing alt attributes
- Detect duplicate titles and duplicate meta descriptions across pages
- Report fetch failures and HTTP status issues
- Check `robots.txt` and `sitemap.xml` availability
- Prioritized issue list (critical / warning / info) with explanations and recommended fixes
- Summary dashboard with counts by issue type and category chart
- Export issues to CSV

## Safety and ethics

- Respects `robots.txt`, site terms, crawl limits, and server capacity
- Conservative timeouts, delays, and concurrency (single-threaded polite crawl by default)
- Never bypasses CAPTCHAs, authentication, anti-bot controls, or access restrictions
- Does not claim to measure actual Google rankings — findings are directly observed from the page HTML, and recommendations are clearly marked as recommendations

## Technology stack

- Python 3.11
- Standard library `html.parser` (portable, dependency-light core)
- Requests (HTTP fetching)
- Pandas (reporting/CSV)
- Plotly (charts)
- Streamlit (web UI)

## Folder structure

```
seo-audit-tool/
├── app.py                  # Streamlit application
├── seo_audit/
│   ├── __init__.py
│   ├── analyzer.py         # HTML parsing and issue detection engine
│   └── fetcher.py          # Polite HTTP fetching and crawling
├── tests/
│   └── test_analyzer.py    # Unit tests for the analyzer
├── sample.html             # Sample page for offline experimentation
├── requirements.txt
└── .gitignore
```

## Installation

```bash
python -m venv venv
# Windows: venv\Scripts\activate  |  macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

Open the local URL shown by Streamlit, enter a website URL, choose the crawl limit, and click **Run Audit**.

### Offline / sample input

To try the analyzer without a network, run the unit tests (see below) or point the tool at any site you are authorized to audit.

## Testing

```bash
pytest -q
```

Tests cover: missing title (critical), noindex detection, missing alt text, multiple H1 headings, duplicate titles across pages, and aggregate counts.

## Limitations and known issues

- Crawling depends on site availability; heavily JS-rendered pages may yield incomplete HTML
- Redirect chains are reported only as fetch failures in this version (full chain tracing is a future improvement)
- Findings reflect the fetched HTML snapshot, not Google's index or ranking position

## Future improvements

- Redirect-chain tracing
- Word-count and keyword-density heuristics
- Mobile vs desktop viewport checks
- Scheduled audits with historical comparison
- CI via GitHub Actions

## License

MIT (add a `LICENSE` file before commercial use if required by your use case).

---

**Developed by Muhammad Hamid**

Digital Marketing | SEO | Performance Marketing | E-commerce | Web Development

- Portfolio: [https://abouthamid.web.app/](https://abouthamid.web.app/)
- LinkedIn: [https://www.linkedin.com/in/muhammad-hamid-digital-marketing/](https://www.linkedin.com/in/muhammad-hamid-digital-marketing/)
- WhatsApp: [https://wa.me/923167417135](https://wa.me/923167417135)

Have a project, job opportunity, or collaboration in mind? [Contact Muhammad Hamid on WhatsApp](https://wa.me/923167417135).
