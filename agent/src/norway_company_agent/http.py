from __future__ import annotations

import json
import hashlib
import time
import threading
import urllib.error
import urllib.request
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class FetchResult:
    url: str
    status: int
    elapsed_ms: int
    bytes_received: int
    body: Any = None
    error: str | None = None
    content_sha256: str | None = None
    retrieved_at: str | None = None
    effective_at: str | None = None
    attempted_requests: int = 0
    redirect_count: int = 0


_request_start_lock = threading.Lock()
_last_request_start = 0.0
_request_counts = threading.local()


class OfficialRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme != "https" or parsed.hostname != "data.brreg.no":
            raise ValueError("Official response redirected outside the pinned data.brreg.no origin")
        _request_counts.redirects = getattr(_request_counts, "redirects", 0) + 1
        return super().redirect_request(req, fp, code, msg, headers, newurl)


OFFICIAL_OPENER = urllib.request.build_opener(OfficialRedirectHandler())


def _reserve_request_start(min_interval: float = 0.25) -> None:
    """Bound official-source request starts across all batch workers."""
    global _last_request_start
    with _request_start_lock:
        delay = min_interval - (time.monotonic() - _last_request_start)
        if delay > 0:
            time.sleep(delay)
        _last_request_start = time.monotonic()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch_json(url: str, *, timeout: float = 20.0, attempts: int = 3) -> FetchResult:
    last_error = "request failed"
    last_elapsed = 0
    last_bytes = 0
    total_requests = 0
    total_redirects = 0
    for attempt in range(attempts):
        _request_counts.redirects = 0
        _reserve_request_start()
        total_requests += 1
        started = time.monotonic()
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "builderr-signalpost-poc/0.1 (+https://builderr.ai)"},
        )
        try:
            with OFFICIAL_OPENER.open(request, timeout=timeout) as response:
                raw = response.read()
                elapsed = int((time.monotonic() - started) * 1000)
                redirects = getattr(_request_counts, "redirects", 0)
                return FetchResult(url, response.status, elapsed, len(raw), json.loads(raw), content_sha256=hashlib.sha256(raw).hexdigest(), retrieved_at=_utc_now(), attempted_requests=total_requests + total_redirects + redirects, redirect_count=total_redirects + redirects)
        except urllib.error.HTTPError as exc:
            elapsed = int((time.monotonic() - started) * 1000)
            raw = exc.read()
            last_elapsed = elapsed
            last_bytes = len(raw)
            total_redirects += getattr(_request_counts, "redirects", 0)
            if exc.code in {404, 410}:
                return FetchResult(url, exc.code, elapsed, len(raw), error=f"HTTP {exc.code}", content_sha256=hashlib.sha256(raw).hexdigest(), retrieved_at=_utc_now(), attempted_requests=total_requests + total_redirects, redirect_count=total_redirects)
            last_error = f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
            last_elapsed = int((time.monotonic() - started) * 1000)
            total_redirects += getattr(_request_counts, "redirects", 0)
            last_error = f"{type(exc).__name__}: {str(exc)[:120]}"
        if attempt + 1 < attempts:
            time.sleep(0.4 * (2**attempt))
    return FetchResult(url, 0, last_elapsed, last_bytes, error=last_error, retrieved_at=_utc_now(), attempted_requests=total_requests + total_redirects, redirect_count=total_redirects)
