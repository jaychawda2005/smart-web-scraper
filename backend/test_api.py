"""
test_api.py
-----------
Automated test suite for SmartScrape API.
Run with: .venv/Scripts/python test_api.py
"""

import sys
import requests

BASE = "http://127.0.0.1:8000"
passed = 0
failed = 0


def post_scrape(url_val, opts=None):
    body = {"url": url_val}
    if opts is not None:
        body["options"] = opts
    return requests.post(f"{BASE}/api/scrape", json=body, timeout=30)


def check(label, ok, info=""):
    global passed, failed
    mark = "PASS" if ok else "FAIL"
    print(f"{mark}: {label}  {info}")
    if ok:
        passed += 1
    else:
        failed += 1


print("=" * 60)
print("SmartScrape API Test Suite")
print("=" * 60)

# ---------------------------------------------------------------
# 1. Health check
# ---------------------------------------------------------------
r = requests.get(f"{BASE}/", timeout=5)
check("Health check -> 200", r.status_code == 200, f"body={r.json()}")

# ---------------------------------------------------------------
# 2. Valid URL — full extraction
# ---------------------------------------------------------------
ALL_OPTS = {
    "page_info": True, "headings": True, "text": True,
    "links": True, "images": True, "tables": True, "lists": True,
}
r = post_scrape("https://example.com", ALL_OPTS)
check("Valid URL (example.com) -> 200", r.status_code == 200)
if r.status_code == 200:
    d = r.json()
    pi = d["page_info"]
    print(f"  title={pi['title']}  status={pi['status_code']}  "
          f"headings={pi['headings_count']}  links={pi['links_count']}  "
          f"text_blocks={len(d['text'])}")
    check("  page_info present", d.get("page_info") is not None)
    check("  headings list present", isinstance(d.get("headings"), list))
    check("  links list present", isinstance(d.get("links"), list))
    check("  text list present", isinstance(d.get("text"), list))
    check("  text blocks > 0", len(d["text"]) > 0, f"count={len(d['text'])}")

# ---------------------------------------------------------------
# 3. Empty URL -> 422 (Pydantic validation)
# ---------------------------------------------------------------
r = post_scrape("")
check("Empty URL -> 422", r.status_code == 422, f"status={r.status_code}")

# ---------------------------------------------------------------
# 4. Invalid URL -> 400
# ---------------------------------------------------------------
r = post_scrape("not-a-url")
detail = r.json().get("detail", "")
check("Invalid URL -> 400", r.status_code == 400,
      f"status={r.status_code} detail={detail!r}")

# ---------------------------------------------------------------
# 5. Unsupported scheme: ftp://
# ---------------------------------------------------------------
r = post_scrape("ftp://example.com/file")
detail = r.json().get("detail", "")
check("ftp:// scheme -> 400", r.status_code == 400,
      f"detail={detail!r}")

# ---------------------------------------------------------------
# 6. Unsupported scheme: file://
# ---------------------------------------------------------------
r = post_scrape("file:///etc/passwd")
detail = r.json().get("detail", "")
check("file:// scheme -> 400", r.status_code == 400,
      f"detail={detail!r}")

# ---------------------------------------------------------------
# 7. SSRF: localhost
# ---------------------------------------------------------------
r = post_scrape("http://localhost:8000/")
detail = r.json().get("detail", "")
check("SSRF: localhost -> 400", r.status_code == 400,
      f"detail={detail!r}")

# ---------------------------------------------------------------
# 8. SSRF: 127.0.0.1
# ---------------------------------------------------------------
r = post_scrape("http://127.0.0.1/")
detail = r.json().get("detail", "")
check("SSRF: 127.0.0.1 -> 400", r.status_code == 400,
      f"detail={detail!r}")

# ---------------------------------------------------------------
# 9. SSRF: 10.x private IP
# ---------------------------------------------------------------
r = post_scrape("http://10.0.0.1/")
detail = r.json().get("detail", "")
check("SSRF: 10.0.0.1 -> 400", r.status_code == 400,
      f"detail={detail!r}")

# ---------------------------------------------------------------
# 10. SSRF: 192.168.x private IP
# ---------------------------------------------------------------
r = post_scrape("http://192.168.1.1/")
detail = r.json().get("detail", "")
check("SSRF: 192.168.1.1 -> 400", r.status_code == 400,
      f"detail={detail!r}")

# ---------------------------------------------------------------
# 11. SSRF: Cloud metadata IP
# ---------------------------------------------------------------
r = post_scrape("http://169.254.169.254/")
detail = r.json().get("detail", "")
check("SSRF: 169.254.169.254 -> 400", r.status_code == 400,
      f"detail={detail!r}")

# ---------------------------------------------------------------
# 12. Selective extraction — page_info only
# ---------------------------------------------------------------
r = post_scrape("https://example.com", {
    "page_info": True, "headings": False, "text": False,
    "links": False, "images": False, "tables": False, "lists": False,
})
check("Selective: page_info only -> 200", r.status_code == 200)
if r.status_code == 200:
    d = r.json()
    check("  headings is null (not requested)", d.get("headings") is None)
    check("  text is null (not requested)", d.get("text") is None)
    check("  links is null (not requested)", d.get("links") is None)

# ---------------------------------------------------------------
# 13. Rich page — httpbin/html (headings + text)
# ---------------------------------------------------------------
r = post_scrape("https://httpbin.org/html", ALL_OPTS)
check("httpbin/html -> 200", r.status_code == 200)
if r.status_code == 200:
    d = r.json()
    print(f"  httpbin title={d['page_info']['title']}  "
          f"text_blocks={len(d['text'])}  headings={len(d['headings'])}")

# ---------------------------------------------------------------
# 14. Wikipedia — tables, lists, images
# ---------------------------------------------------------------
r = post_scrape(
    "https://en.wikipedia.org/wiki/Python_(programming_language)",
    ALL_OPTS,
)
check("Wikipedia Python page -> 200", r.status_code == 200)
if r.status_code == 200:
    d = r.json()
    pi = d["page_info"]
    print(f"  tables={pi['tables_count']}  lists={pi['lists_count']}  "
          f"images={pi['images_count']}  links={pi['links_count']}")
    check("  tables extracted", len(d["tables"]) > 0, f"count={len(d['tables'])}")
    check("  lists extracted", len(d["lists"]) > 0, f"count={len(d['lists'])}")
    check("  images extracted", len(d["images"]) > 0, f"count={len(d['images'])}")

# ---------------------------------------------------------------
# 15. Scraping history
# ---------------------------------------------------------------
r = requests.get(f"{BASE}/api/history", timeout=5)
check("GET /api/history -> 200", r.status_code == 200)
if r.status_code == 200:
    hist = r.json()
    check("  history has jobs", hist["total"] > 0, f"total={hist['total']}")
    job0 = hist["jobs"][0]
    check("  job has url field", "url" in job0)
    check("  job has status field", "status" in job0)

# ---------------------------------------------------------------
# 16–18. Export endpoints (need a fresh scrape in cache first)
# ---------------------------------------------------------------
# Fresh scrape to populate cache
r = post_scrape("https://example.com", {
    "page_info": True, "headings": True, "text": True,
    "links": True, "images": False, "tables": False, "lists": False,
})
check("Pre-export scrape -> 200", r.status_code == 200)

# JSON export
r = requests.get(f"{BASE}/api/export/json", timeout=10)
check("GET /api/export/json -> 200", r.status_code == 200)
if r.status_code == 200:
    exp = r.json()
    check("  JSON export has url key", "url" in exp, f"keys={list(exp.keys())}")

# CSV export
r = requests.get(f"{BASE}/api/export/csv", timeout=10)
check("GET /api/export/csv -> 200", r.status_code == 200)
if r.status_code == 200:
    lines = r.text.strip().split("\n")
    check("  CSV has rows", len(lines) > 1, f"rows={len(lines)}")
    print(f"  CSV header: {lines[0]}")

# Excel export
r = requests.get(f"{BASE}/api/export/excel", timeout=10)
check("GET /api/export/excel -> 200", r.status_code == 200)
if r.status_code == 200:
    check("  Excel file is non-empty", len(r.content) > 1000,
          f"bytes={len(r.content)}")
    # Excel files start with PK (zip magic bytes)
    check("  Excel file magic bytes (PK)", r.content[:2] == b"PK")

# ---------------------------------------------------------------
# 19. DELETE history item
# ---------------------------------------------------------------
r = requests.get(f"{BASE}/api/history?limit=1", timeout=5)
if r.status_code == 200 and r.json()["jobs"]:
    job_id = r.json()["jobs"][0]["id"]
    r_del = requests.delete(f"{BASE}/api/history/{job_id}", timeout=5)
    check(f"DELETE /api/history/{job_id} -> 200", r_del.status_code == 200,
          f"body={r_del.json()}")
else:
    print("SKIP: DELETE history (no jobs found)")

# ---------------------------------------------------------------
# 20. DELETE non-existent job -> 404
# ---------------------------------------------------------------
r = requests.delete(f"{BASE}/api/history/999999", timeout=5)
check("DELETE non-existent job -> 404", r.status_code == 404)

# ---------------------------------------------------------------
# Summary
# ---------------------------------------------------------------
print()
print("=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
