"""
Crawler engine that uses Playwright to simulate Googlebot / search engine bot behavior.

Key Googlebot behaviors simulated:
- Correct user agent string
- Custom request headers matching Googlebot
- Stateless crawling (no cookies persisted between pages)
- Redirect chain tracking (HTTP redirects + meta refresh + JS redirects)
- Request/response header recording for the main URL and redirects
- 5-second rendering timeout (matching Google's WRS)
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, BrowserContext, Route

# Default headers that Googlebot typically sends.
# Based on research: Googlebot sends Accept: */*, does NOT send Accept-Language
# by default (only when server returns Vary: Accept-Language), uses From header,
# and supports gzip, deflate, and Brotli compression.
GOOGLEBOT_DEFAULT_HEADERS = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "From": "googlebot(at)googlebot.com",
}


def run_crawl(url: str, user_agent: str, extra_headers: dict | None = None,
              viewport_width: int = 1024, viewport_height: int = 768,
              is_mobile: bool = False, timeout_seconds: int = 30,
              render_wait_seconds: int = 5) -> dict:
    """
    Crawl a URL simulating bot behavior and record a trace of all network activity.

    Args:
        url: The URL to crawl.
        user_agent: User agent string to use.
        extra_headers: Additional HTTP headers to send.
        viewport_width: Browser viewport width.
        viewport_height: Browser viewport height.
        is_mobile: Whether to emulate a mobile device.
        timeout_seconds: Max time to wait for page load (navigation timeout).
        render_wait_seconds: Time to wait after load for JS rendering (simulates WRS).

    Returns:
        A dict with the full trace data.
    """
    headers = dict(GOOGLEBOT_DEFAULT_HEADERS)
    if extra_headers:
        headers.update(extra_headers)

    trace = {
        "meta": {
            "crawl_started_at": datetime.now(timezone.utc).isoformat(),
            "target_url": url,
            "user_agent": user_agent,
            "extra_headers": extra_headers or {},
            "viewport": f"{viewport_width}x{viewport_height}",
            "is_mobile": is_mobile,
            "timeout_seconds": timeout_seconds,
            "render_wait_seconds": render_wait_seconds,
        },
        "redirect_chain": [],
        "requests": [],
        "console_messages": [],
        "errors": [],
        "final_url": None,
        "final_status": None,
        "page_title": None,
        "meta_robots": None,
        "canonical_url": None,
        "crawl_finished_at": None,
    }

    request_map = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        context = browser.new_context(
            user_agent=user_agent,
            viewport={"width": viewport_width, "height": viewport_height},
            is_mobile=is_mobile,
            java_script_enabled=True,
            extra_http_headers=headers,
            # Googlebot is stateless - no storage state
            ignore_https_errors=True,
        )
        # Disable cookies to simulate Googlebot's stateless behavior
        context.clear_cookies()

        page = context.new_page()

        # Track requests - only main frame navigation requests and their redirects
        def on_request(request):
            entry = {
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "resource_type": request.resource_type,
                "is_navigation": request.is_navigation_request(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            request_map[request.url] = entry
            if request.is_navigation_request() or request.resource_type == "document":
                trace["requests"].append(entry)

        def on_response(response):
            req_entry = request_map.get(response.url)
            if req_entry and (req_entry.get("is_navigation") or req_entry.get("resource_type") == "document"):
                resp_headers = dict(response.headers)
                req_entry["response"] = {
                    "status": response.status,
                    "status_text": response.status_text,
                    "headers": resp_headers,
                    "url": response.url,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                # Track redirect chain
                status = response.status
                if 300 <= status < 400:
                    location = resp_headers.get("location", "")
                    trace["redirect_chain"].append({
                        "from_url": response.url,
                        "to_url": location,
                        "status": status,
                        "headers": resp_headers,
                    })

        def on_console(msg):
            trace["console_messages"].append({
                "type": msg.type,
                "text": msg.text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        def on_page_error(error):
            trace["errors"].append({
                "type": "page_error",
                "message": str(error),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        page.on("request", on_request)
        page.on("response", on_response)
        page.on("console", on_console)
        page.on("pageerror", on_page_error)

        try:
            # Navigate with timeout matching real Googlebot behavior
            response = page.goto(
                url,
                wait_until="networkidle",
                timeout=timeout_seconds * 1000,
            )

            if response:
                trace["final_status"] = response.status
                trace["final_url"] = page.url

            # Wait for JS rendering (simulating Google's WRS ~5 second window)
            page.wait_for_timeout(render_wait_seconds * 1000)

            # Extract SEO-relevant info from the rendered page
            trace["page_title"] = page.title()

            # Get meta robots
            try:
                meta_robots = page.evaluate("""() => {
                    const meta = document.querySelector('meta[name="robots"]');
                    return meta ? meta.getAttribute('content') : null;
                }""")
                trace["meta_robots"] = meta_robots
            except Exception:
                pass

            # Get canonical URL
            try:
                canonical = page.evaluate("""() => {
                    const link = document.querySelector('link[rel="canonical"]');
                    return link ? link.getAttribute('href') : null;
                }""")
                trace["canonical_url"] = canonical
            except Exception:
                pass

            # Check for meta refresh redirects
            try:
                meta_refresh = page.evaluate("""() => {
                    const meta = document.querySelector('meta[http-equiv="refresh"]');
                    return meta ? meta.getAttribute('content') : null;
                }""")
                if meta_refresh:
                    trace["redirect_chain"].append({
                        "from_url": url,
                        "to_url": meta_refresh,
                        "status": "meta-refresh",
                        "headers": {},
                    })
            except Exception:
                pass

            # Detect if final URL differs from target (JS redirect)
            if page.url != url and not trace["redirect_chain"]:
                trace["redirect_chain"].append({
                    "from_url": url,
                    "to_url": page.url,
                    "status": "js-redirect",
                    "headers": {},
                })

            trace["final_url"] = page.url

        except Exception as e:
            trace["errors"].append({
                "type": "navigation_error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        browser.close()

    trace["crawl_finished_at"] = datetime.now(timezone.utc).isoformat()
    return trace


def save_trace(trace: dict, traces_dir: str = "traces") -> str:
    """Save a trace to a JSON file and return the filename."""
    traces_path = Path(traces_dir)
    traces_path.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Sanitize URL for filename
    url = trace["meta"]["target_url"]
    safe_url = url.replace("://", "_").replace("/", "_").replace("?", "_")[:60]
    filename = f"trace_{timestamp}_{safe_url}.json"
    filepath = traces_path / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(trace, f, indent=2, ensure_ascii=False, default=str)

    return str(filepath)
