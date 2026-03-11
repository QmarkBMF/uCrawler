#!/usr/bin/env python3
"""
uCrawler - Local Googlebot Simulator

A web-based tool for simulating search engine bot crawling behavior.
Helps debug issues where Googlebot encounters errors that don't appear
in regular browser sessions.

Usage:
    python app.py [--port PORT] [--no-open]
"""

import argparse
import json
import os
import sys
import threading
import webbrowser
from pathlib import Path

from flask import Flask, render_template, request, jsonify

from crawler import run_crawl, save_trace
from user_agents import USER_AGENTS

app = Flask(__name__)

CONFIGS_DIR = Path("configs")
TRACES_DIR = Path("traces")
CONFIGS_DIR.mkdir(exist_ok=True)
TRACES_DIR.mkdir(exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/user-agents")
def get_user_agents():
    """Return the list of known user agents."""
    return jsonify(USER_AGENTS)


@app.route("/api/configs", methods=["GET"])
def list_configs():
    """List all saved configurations."""
    configs = []
    for f in sorted(CONFIGS_DIR.glob("*.json"), key=os.path.getmtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            data["_filename"] = f.stem
            configs.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return jsonify(configs)


@app.route("/api/configs", methods=["POST"])
def save_config():
    """Save a configuration."""
    data = request.get_json()
    if not data or "name" not in data:
        return jsonify({"error": "Config must have a name"}), 400

    name = data["name"]
    # Sanitize filename
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name).strip()
    if not safe_name:
        return jsonify({"error": "Invalid config name"}), 400

    filepath = CONFIGS_DIR / f"{safe_name}.json"
    filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return jsonify({"status": "saved", "filename": safe_name})


@app.route("/api/configs/<name>", methods=["DELETE"])
def delete_config(name):
    """Delete a configuration."""
    filepath = CONFIGS_DIR / f"{name}.json"
    if filepath.exists():
        filepath.unlink()
        return jsonify({"status": "deleted"})
    return jsonify({"error": "Config not found"}), 404


@app.route("/api/crawl", methods=["POST"])
def crawl():
    """Run a crawl with the given configuration."""
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "URL is required"}), 400

    url = data["url"]
    user_agent = data.get("user_agent", "")
    extra_headers = data.get("extra_headers", {})
    is_mobile = data.get("is_mobile", False)
    viewport_width = data.get("viewport_width", 1024)
    viewport_height = data.get("viewport_height", 768)
    timeout_seconds = data.get("timeout_seconds", 30)
    render_wait_seconds = data.get("render_wait_seconds", 5)

    if not user_agent:
        # Default to Googlebot Desktop
        user_agent = USER_AGENTS["Googlebot (Desktop - Chrome)"]["user_agent"]

    try:
        trace = run_crawl(
            url=url,
            user_agent=user_agent,
            extra_headers=extra_headers if extra_headers else None,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            is_mobile=is_mobile,
            timeout_seconds=timeout_seconds,
            render_wait_seconds=render_wait_seconds,
        )
        filepath = save_trace(trace, str(TRACES_DIR))
        trace["_trace_file"] = filepath
        return jsonify(trace)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/traces", methods=["GET"])
def list_traces():
    """List all saved traces."""
    traces = []
    for f in sorted(TRACES_DIR.glob("*.json"), key=os.path.getmtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            traces.append({
                "filename": f.name,
                "url": data.get("meta", {}).get("target_url", ""),
                "user_agent_short": data.get("meta", {}).get("user_agent", "")[:60],
                "status": data.get("final_status"),
                "crawled_at": data.get("meta", {}).get("crawl_started_at", ""),
                "errors_count": len(data.get("errors", [])),
                "redirects_count": len(data.get("redirect_chain", [])),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return jsonify(traces)


@app.route("/api/traces/<filename>")
def get_trace(filename):
    """Get a specific trace by filename."""
    filepath = TRACES_DIR / filename
    if not filepath.exists():
        return jsonify({"error": "Trace not found"}), 404
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
        return jsonify(data)
    except (json.JSONDecodeError, OSError) as e:
        return jsonify({"error": str(e)}), 500


def open_browser(port: int):
    """Open browser after a short delay to let the server start."""
    import time
    time.sleep(1.0)
    webbrowser.open(f"http://127.0.0.1:{port}")


def main():
    parser = argparse.ArgumentParser(description="uCrawler - Googlebot Simulator")
    parser.add_argument("--port", type=int, default=8095, help="Port to run on (default: 8095)")
    parser.add_argument("--no-open", action="store_true", help="Don't open browser automatically")
    args = parser.parse_args()

    if not args.no_open:
        threading.Thread(target=open_browser, args=(args.port,), daemon=True).start()

    print(f"\n  uCrawler running at http://127.0.0.1:{args.port}\n")
    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()
