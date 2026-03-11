# uCrawler

Local browser-based Googlebot simulator with flexible configuration.

Helps debug issues where Googlebot or other search engine bots encounter errors that don't appear in regular browser sessions. Simulates bot behavior as closely as possible, including correct user agent strings, HTTP headers, stateless crawling (no cookies), and JavaScript rendering with a configurable timeout matching Google's Web Rendering Service (WRS).

## Features

- Web-based interface for configuring and running crawls
- Predefined user agents for Googlebot, Bingbot, YandexBot, Baiduspider, DuckDuckBot, Applebot, GPTBot, ClaudeBot, and regular browsers
- Custom request headers editor
- Redirect chain tracking (HTTP 3xx, meta refresh, JS redirects)
- Request/response header recording for main URL and redirects
- SEO metadata extraction (page title, meta robots, canonical URL)
- Console message and error capture
- Save/load crawl configurations
- Trace history with JSON output for easy analysis

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (one-time)
playwright install chromium

# Run
python app.py
```

The app starts at `http://127.0.0.1:8095` and opens in your browser automatically.

### Options

```
python app.py --port 9000      # custom port
python app.py --no-open        # don't auto-open browser
```

## How It Works

1. **Configure**: Enter a URL, select a bot user agent (or use custom), optionally add extra request headers
2. **Crawl**: Press "Go to Address" — the app launches a headless Chromium browser configured to mimic the selected bot
3. **Review**: See the full trace — status codes, redirect chains, request/response headers, console errors, and SEO metadata
4. **Save**: Configurations are saved as JSON files in `configs/`, traces in `traces/`

## Googlebot Simulation Details

The crawler replicates key Googlebot behaviors:

- **User Agent**: Uses exact Googlebot user agent strings (desktop, mobile, inspection tool)
- **Headers**: Sends headers matching Googlebot (Accept, Accept-Language, Accept-Encoding, Cache-Control, etc.)
- **Stateless**: Clears cookies — Googlebot's WRS is stateless and doesn't persist cookies between page loads
- **Rendering**: Waits for JavaScript rendering (configurable, default 5 seconds) matching Google's WRS behavior
- **Redirects**: Tracks full redirect chains including HTTP redirects, meta refresh, and JS redirects
- **Chromium**: Uses Playwright's Chromium (same engine as Googlebot's evergreen rendering)

## Trace Output Format

Traces are saved as JSON files in `traces/` for easy analysis (by Claude, scripts, or manual review):

```json
{
  "meta": {
    "target_url": "https://example.com",
    "user_agent": "Mozilla/5.0 (compatible; Googlebot/2.1; ...)",
    "crawl_started_at": "2025-01-01T00:00:00Z"
  },
  "redirect_chain": [],
  "requests": [
    {
      "url": "...",
      "method": "GET",
      "headers": {},
      "response": {
        "status": 200,
        "headers": {}
      }
    }
  ],
  "errors": [],
  "console_messages": [],
  "final_url": "...",
  "final_status": 200,
  "page_title": "...",
  "meta_robots": "index, follow",
  "canonical_url": "..."
}
```

## Requirements

- Python 3.10+
- Flask
- Playwright (with Chromium)
