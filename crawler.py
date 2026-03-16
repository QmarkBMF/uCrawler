"""
Crawler engine that uses Playwright to simulate Googlebot / search engine bot behavior.

Key Googlebot behaviors simulated:
- Correct user agent string
- Custom request headers matching Googlebot
- Stateless crawling (no cookies persisted between pages)
- Redirect chain tracking (HTTP redirects + meta refresh + JS redirects)
- Full network activity logging (all requests/responses, not just navigation)
- Request timing and size tracking for fingerprint analysis
- Failed request tracking to detect blocked resources
- 5-second rendering timeout (matching Google's WRS)
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
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


def _monotonic_ms():
    """Return monotonic time in milliseconds for precise timing."""
    return time.monotonic_ns() // 1_000_000


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

    crawl_start_mono = _monotonic_ms()

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
        "failed_requests": [],
        "console_messages": [],
        "errors": [],
        "final_url": None,
        "final_status": None,
        "page_title": None,
        "meta_robots": None,
        "canonical_url": None,
        "crawl_finished_at": None,
        "network_summary": None,
    }

    # Map request objects by internal Playwright URL for correlation
    # Use list to handle multiple requests to same URL
    request_entries = {}
    request_order = 0

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

        # Track ALL requests for full network visibility
        def on_request(request):
            nonlocal request_order
            request_order += 1
            now = datetime.now(timezone.utc).isoformat()
            elapsed = _monotonic_ms() - crawl_start_mono

            # Determine what frame initiated this request
            frame_url = None
            try:
                frame_url = request.frame.url if request.frame else None
            except Exception:
                pass

            # Build post data summary (truncated for large payloads)
            post_data = None
            try:
                raw = request.post_data
                if raw:
                    post_data = raw[:2048] if len(raw) > 2048 else raw
            except Exception:
                pass

            entry = {
                "order": request_order,
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "resource_type": request.resource_type,
                "is_navigation": request.is_navigation_request(),
                "post_data": post_data,
                "frame_url": frame_url,
                "timestamp": now,
                "elapsed_ms": elapsed,
            }
            # Use id() of the request object as key for precise correlation
            request_entries[id(request)] = entry
            # Store ref so we can look up by response later
            request._trace_entry = entry
            trace["requests"].append(entry)

        def on_response(response):
            now = datetime.now(timezone.utc).isoformat()
            elapsed = _monotonic_ms() - crawl_start_mono

            # Find the matching request entry
            req_entry = getattr(response.request, '_trace_entry', None)
            if not req_entry:
                return

            resp_headers = dict(response.headers)

            # Try to get response body size from headers
            content_length = resp_headers.get("content-length")
            content_type = resp_headers.get("content-type", "")
            content_encoding = resp_headers.get("content-encoding", "")

            # Detect server-side bot detection signals in response headers
            security_headers = {}
            for h in resp_headers:
                hl = h.lower()
                if any(k in hl for k in [
                    "x-bot", "x-crawl", "x-robot", "x-detect",
                    "x-firewall", "x-waf", "x-cdn", "x-cache",
                    "cf-ray", "cf-cache-status", "x-served-by",
                    "server", "x-powered-by", "via",
                    "x-request-id", "x-trace", "x-correlation",
                    "set-cookie",
                ]):
                    security_headers[h] = resp_headers[h]

            req_entry["response"] = {
                "status": response.status,
                "status_text": response.status_text,
                "headers": resp_headers,
                "url": response.url,
                "content_type": content_type,
                "content_encoding": content_encoding,
                "content_length": int(content_length) if content_length else None,
                "security_headers": security_headers if security_headers else None,
                "timestamp": now,
                "elapsed_ms": elapsed,
                "latency_ms": elapsed - req_entry["elapsed_ms"],
            }

            # Track redirect chain for navigation requests
            status = response.status
            if 300 <= status < 400 and req_entry.get("is_navigation"):
                location = resp_headers.get("location", "")
                trace["redirect_chain"].append({
                    "from_url": response.url,
                    "to_url": location,
                    "status": status,
                    "headers": resp_headers,
                })

        def on_request_failed(request):
            now = datetime.now(timezone.utc).isoformat()
            elapsed = _monotonic_ms() - crawl_start_mono

            failure_text = None
            try:
                failure_text = request.failure
            except Exception:
                pass

            entry = {
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type,
                "failure": failure_text,
                "timestamp": now,
                "elapsed_ms": elapsed,
            }
            trace["failed_requests"].append(entry)

            # Also mark it in the request list
            req_entry = getattr(request, '_trace_entry', None)
            if req_entry:
                req_entry["failed"] = True
                req_entry["failure_reason"] = failure_text

        def on_console(msg):
            trace["console_messages"].append({
                "type": msg.type,
                "text": msg.text,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "elapsed_ms": _monotonic_ms() - crawl_start_mono,
            })

        def on_page_error(error):
            trace["errors"].append({
                "type": "page_error",
                "message": str(error),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "elapsed_ms": _monotonic_ms() - crawl_start_mono,
            })

        page.on("request", on_request)
        page.on("response", on_response)
        page.on("requestfailed", on_request_failed)
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
                "elapsed_ms": _monotonic_ms() - crawl_start_mono,
            })

        browser.close()

    trace["crawl_finished_at"] = datetime.now(timezone.utc).isoformat()

    # Build network summary for quick analysis
    trace["network_summary"] = _build_network_summary(trace)

    return trace


def _build_network_summary(trace: dict) -> dict:
    """Build a summary of network activity for quick analysis."""
    requests = trace.get("requests", [])
    failed = trace.get("failed_requests", [])

    # Count by resource type
    by_type = {}
    for r in requests:
        rt = r.get("resource_type", "other")
        by_type[rt] = by_type.get(rt, 0) + 1

    # Count by status code
    by_status = {}
    for r in requests:
        resp = r.get("response")
        if resp:
            status = resp.get("status", 0)
            by_status[status] = by_status.get(status, 0) + 1

    # Count by domain
    by_domain = {}
    for r in requests:
        try:
            domain = urlparse(r["url"]).netloc
            by_domain[domain] = by_domain.get(domain, 0) + 1
        except Exception:
            pass

    # Find XHR/fetch requests (these are the ones most likely to hit /web/1/features)
    api_requests = []
    for r in requests:
        if r.get("resource_type") in ("xhr", "fetch"):
            resp = r.get("response")
            api_requests.append({
                "order": r.get("order"),
                "url": r["url"],
                "method": r["method"],
                "status": resp.get("status") if resp else None,
                "content_type": resp.get("content_type", "") if resp else None,
                "latency_ms": resp.get("latency_ms") if resp else None,
                "security_headers": resp.get("security_headers") if resp else None,
                "elapsed_ms": r.get("elapsed_ms"),
            })

    # Find requests that got non-2xx responses (potential detection)
    blocked_or_error = []
    for r in requests:
        resp = r.get("response")
        if resp and (resp["status"] >= 400 or resp["status"] in (301, 302, 303, 307, 308)):
            blocked_or_error.append({
                "order": r.get("order"),
                "url": r["url"],
                "method": r["method"],
                "status": resp["status"],
                "status_text": resp.get("status_text", ""),
                "content_type": resp.get("content_type", ""),
                "security_headers": resp.get("security_headers"),
            })

    # Find set-cookie headers (server trying to set tracking cookies)
    cookies_set = []
    for r in requests:
        resp = r.get("response")
        if resp:
            sc = resp.get("headers", {}).get("set-cookie")
            if sc:
                cookies_set.append({
                    "url": r["url"],
                    "set_cookie": sc,
                })

    return {
        "total_requests": len(requests),
        "failed_requests": len(failed),
        "by_resource_type": by_type,
        "by_status_code": by_status,
        "by_domain": by_domain,
        "api_requests": api_requests,
        "blocked_or_error_requests": blocked_or_error,
        "cookies_attempted": cookies_set,
    }


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
