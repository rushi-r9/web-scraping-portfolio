# Reproducible scraping demonstration kit

This kit demonstrates HTML parsing and a basic extraction pipeline against **local authored HTML fixtures**. It does not scrape live retailer, property, job-board, or business-directory websites. All records and historical price observations are synthetic.

## Run it

```bash
cd demo_kit
python scraper.py --dataset all --verbose
python price_monitor.py
python -m unittest discover -s tests -v
```

The scraper follows local `rel="next"` links, normalizes text, checks required fields, removes duplicate IDs, logs issues, and exports CSV, JSON, SQLite, plus XLSX when `openpyxl` is installed. Output goes to `demo_kit/output/`.

To use the XLSX export, install the optional dependency with `python -m pip install -r requirements.txt`. The core parser itself uses only the standard library.

## Safety and adaptation

Before adapting this pattern to a third-party source, check the site's terms, robots guidance, applicable law, privacy requirements, and any client authorization. Add conservative rate limits, request identification where appropriate, retry/backoff controls, and source-specific tests. Do not bypass login requirements, paywalls, CAPTCHAs, access controls, or technical restrictions. The demo intentionally makes no external network requests.
