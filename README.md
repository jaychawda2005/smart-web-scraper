# SmartScrape

**Universal Web Data Extraction & Analytics Platform**

SmartScrape allows you to enter any publicly accessible webpage URL, select the types of data you want to extract, and instantly receive structured, searchable, and exportable results — right in your browser.

> ⚠️ SmartScrape is designed for publicly accessible webpages where automated access is permitted. It does not bypass CAPTCHA, authentication, paywalls, or other access controls.

---

## Features

- 🔍 **Universal scraping** — extract headings, text blocks, links, images, tables, and lists
- ⚡ **Render JavaScript** — optional headless Chromium mode (Playwright) for JS-heavy SPAs
- 📊 **Interactive dashboard** — tabbed results viewer with search and filtering
- 📈 **Analytics** — Recharts-powered content distribution and heading charts
- 🕓 **History** — persistent SQLite history of all scrape jobs
- ⬇️ **Export** — download results as JSON, CSV, or Excel
- 🔒 **SSRF protection** — blocks private IPs, localhost, and cloud metadata endpoints
- 🎬 **YouTube extraction** — dedicated metadata extractor for YouTube video URLs
- 📱 **Responsive** — works on desktop, tablet, and mobile

---

## Tech Stack

| Layer     | Technology                                                   |
|-----------|--------------------------------------------------------------|
| Frontend  | React 19, Vite 8, Tailwind CSS 4, Axios, Recharts            |
| Backend   | Python 3, FastAPI, Uvicorn                                   |
| Scraping  | Requests + BeautifulSoup4 (fast path), Playwright (JS path)  |
| Database  | SQLAlchemy + SQLite                                          |
| Validation| Pydantic v2, socket-level SSRF checks                        |

---

## Architecture

```
React (Vite)
    ↓
Axios  →  http://127.0.0.1:8001
    ↓
FastAPI  (main.py)
    ↓
Security layer  (security.py — SSRF validation)
    ↓
┌─── render_js=false ─────────────────┐
│  Requests + BeautifulSoup4          │  ← fast path (default, 0.5–2s)
└─────────────────────────────────────┘
┌─── render_js=true ──────────────────┐
│  Playwright headless Chromium       │  ← JS path (optional, 3–10s)
│    → fully rendered HTML            │
│    → same BeautifulSoup4 pipeline   │
└─────────────────────────────────────┘
    ↓
Structured JSON response
    ↓
SQLite history  (database.py + models.py)
```

---

## Folder Structure

```
smart-web-scraper/
├── backend/
│   ├── main.py           # FastAPI routes & export logic
│   ├── scraper.py        # HTML extraction engine
│   ├── security.py       # SSRF + URL validation
│   ├── database.py       # SQLAlchemy engine & session
│   ├── models.py         # ScrapeJob ORM model
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── test_api.py       # 39-test automated suite
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── Navbar.jsx
    │   │   ├── UrlInput.jsx
    │   │   ├── ExtractionOptions.jsx
    │   │   ├── StatsCard.jsx
    │   │   ├── ResultsTabs.jsx      # Overview, Text, Headings, Links, Images, Tables, Lists
    │   │   ├── SearchBar.jsx
    │   │   ├── DataTable.jsx
    │   │   ├── Charts.jsx           # Recharts pie + bar
    │   │   ├── ScrapeHistory.jsx
    │   │   ├── CopyButton.jsx
    │   │   ├── LoadingState.jsx
    │   │   ├── ErrorState.jsx
    │   │   └── EmptyState.jsx
    │   ├── pages/
    │   │   └── Dashboard.jsx        # All four sections: Dashboard, Results, History, Analytics
    │   ├── services/
    │   │   └── api.js               # Centralised Axios API service
    │   ├── App.jsx
    │   ├── main.jsx
    │   └── index.css                # Tailwind v4 + custom component classes
    ├── index.html
    ├── vite.config.js
    └── package.json
```

---

## Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+

### 1 — Clone

```bash
git clone https://github.com/your-username/smartscrape.git
cd smartscrape/smart-web-scraper
```

### 2 — Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# ⚡ IMPORTANT: Install Chromium browser binary for JavaScript rendering
# This downloads ~200 MB of browser binaries (one-time setup)
.venv\Scripts\playwright install chromium      # Windows
# or:
playwright install chromium                    # if venv is active on macOS/Linux
```

> **Why the separate command?** `pip install playwright` only installs the Python library.
> The actual browser binary (Chromium) must be downloaded separately with `playwright install chromium`.
> This is a one-time download (~200 MB) stored in your OS's application data folder.
> **The fast path (requests) works fine without this step.**  The browser is only needed when you enable "Render JavaScript" mode in the UI.

### 3 — Frontend Setup

```bash
cd ../frontend
npm install
```

---

## How to Run

### Start the Backend

```bash
cd backend
.venv\Scripts\activate        # Windows
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

Backend runs at: `http://127.0.0.1:8001`  
API docs at: `http://127.0.0.1:8001/docs`

### Start the Frontend

```bash
cd frontend
npm run dev
```

Frontend runs at: `http://localhost:5173`

> Run both in separate terminals simultaneously.

---

## API Endpoints

| Method | Endpoint              | Description                         |
|--------|-----------------------|-------------------------------------|
| GET    | `/`                   | Health check                        |
| POST   | `/api/scrape`         | Scrape a URL with selected options  |
| GET    | `/api/history`        | List recent scrape jobs             |
| DELETE | `/api/history/{id}`   | Delete a history record             |
| GET    | `/api/export/json`    | Download last result as JSON        |
| GET    | `/api/export/csv`     | Download last result as CSV         |
| GET    | `/api/export/excel`   | Download last result as Excel       |

### Scrape Request Body

```json
{
  "url": "https://example.com",
  "render_js": false,
  "options": {
    "page_info": true,
    "headings": true,
    "text": true,
    "links": true,
    "images": true,
    "tables": true,
    "lists": true
  }
}
```

**`render_js`** (boolean, default `false`):
- `false` — fast path: `requests` + BeautifulSoup4 (0.5–2 s, no browser)
- `true` — browser path: headless Chromium renders the page fully before parsing (3–10 s)

---

## Security

- **SSRF Protection**: All URLs are resolved with `socket.getaddrinfo` and checked against blocked ranges (localhost, RFC-1918, link-local `169.254.x.x`, IPv6 loopback). This validation runs for **both** the fast path and the browser path — no navigation happens before the check passes.
- **Scheme Validation**: Only `http://` and `https://` are allowed.
- **No internal access**: Hostnames like `localhost`, `0.0.0.0`, and `metadata.google.internal` are blocked explicitly.
- **No credentials**: SmartScrape does not handle cookies, sessions, or authentication tokens.

---

## Testing

```bash
cd backend
.venv\Scripts\activate
python test_api.py
```

**39/39 tests pass**, covering:
- Health check
- Valid URL scraping (example.com, Wikipedia, httpbin)
- All extraction options
- Selective extraction
- SSRF rejection (localhost, 127.0.0.1, 10.x, 192.168.x, 169.254.x)
- Invalid/empty URL rejection
- History API
- All export formats (JSON, CSV, Excel)
- History delete

---

## Limitations

### Fast path (`render_js=false`)
- JavaScript-rendered SPAs return minimal content (the server's raw HTML only)
- Rate-limited or bot-protected sites will be rejected by the remote server

### JavaScript rendering path (`render_js=true`)
- Slower: adds 3–10 seconds per scrape (headless browser spin-up + page render time)
- Some sites detect and block headless browsers regardless (Cloudflare, Akamai bot protection, reCAPTCHA walls)
- Reddit example: returns 93 links and 56 images with JS rendering vs 0 for both without
- Still won't bypass login walls, paywalls, or CAPTCHA
- Chromium binary (~200 MB) must be installed separately with `playwright install chromium`

### Both paths
- Very large pages may be slow to parse
- No proxy support in the current version
- SQLite is single-file; not suitable for production multi-user deployment

### Performance trade-off: why JS rendering is opt-in, not automatic
Making browser rendering the default would add 3–10 seconds to every scrape, including simple static pages that never needed it. The person scraping knows whether their target site is a SPA — making this a deliberate checkbox keeps simple scrapes fast and only pays the overhead when truly needed.

---

## Future Improvements

- [ ] Scheduled recurring scrapes
- [ ] User authentication and per-user history
- [ ] PostgreSQL backend for multi-user support
- [ ] CSS selector / XPath targeting
- [ ] Webhook notifications on scrape completion
- [ ] Docker Compose setup for one-command startup
- [ ] Dark/light theme toggle

---

## Resume Description

> Built a full-stack web data extraction platform using **FastAPI** (Python) and **React** (Vite). Implemented a dual-mode scraping engine: a fast **Requests + BeautifulSoup4** path for static sites and an optional **Playwright headless Chromium** path for JavaScript-rendered SPAs. Applied SSRF security controls to both paths. Built persistent **SQLite** job history, multi-format export (JSON, CSV, Excel), and a responsive **Tailwind CSS** dashboard with tabbed results, real-time **Recharts** visualizations, client-side search/filter, and copy-to-clipboard functionality.

---

## License

MIT — for educational use.
