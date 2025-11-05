from __future__ import annotations

import json
from typing import Any, Dict

import requests


class HttpError(RuntimeError):
    def __init__(self, status_code: int, message: str, *, data: Any | None = None) -> None:
        super().__init__(f"{status_code}: {message}")
        self.status_code = status_code
        self.data = data


class HttpClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        timeout: float | None = None,
    ) -> None:
        self._base = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    def _headers(self, extra: Dict[str, str] | None = None) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        }
        if extra:
            headers.update(extra)
        return headers

    def _handle_json(self, resp: requests.Response, *, prefix: str | None = None) -> Any:
        """Handle standard JSON API responses and print structured JSON."""
        text = resp.text or ""
        if not resp.ok:
            msg = f"{prefix or 'Request failed'} ({resp.status_code}): {text}"
            raise HttpError(resp.status_code, msg, data=_safe_json(text))

        try:
            data = resp.json() if text else None
        except json.JSONDecodeError:
            data = text

        self.print_response(data)
        return data

    def _handle_api(self, resp: requests.Response) -> Any:
        """Handle responses for API-style methods, but keep structure consistent."""
        text = resp.text or ""
        if not resp.ok:
            raise HttpError(resp.status_code, resp.reason, data=_safe_json(text))

        try:
            data = resp.json() if text else None
        except json.JSONDecodeError:
            data = text
        self.print_response(data)
        return data

    def get_json(
        self,
        path: str,
        *,
        params: Dict[str, Any] | None = None,
        prefix: str | None = None,
    ) -> Any:
        url = f"{self._base}{path}"
        resp = requests.get(url, headers=self._headers(), params=params, timeout=self._timeout)
        return self._handle_json(resp, prefix=prefix)

    def post_json(self, path: str, body: Any, *, prefix: str | None = None) -> Any:
        url = f"{self._base}{path}"
        resp = requests.post(
            url,
            headers=self._headers({"Content-Type": "application/json"}),
            data=json.dumps(body),
            timeout=self._timeout,
        )
        return self._handle_json(resp, prefix=prefix)

    def patch_json(self, path: str, body: Any, *, prefix: str | None = None) -> Any:
        url = f"{self._base}{path}"
        resp = requests.patch(
            url,
            headers=self._headers({"Content-Type": "application/json"}),
            data=json.dumps(body),
            timeout=self._timeout,
        )
        return self._handle_json(resp, prefix=prefix)

    def get_api(self, path: str, *, params: Dict[str, Any] | None = None) -> Any:
        url = f"{self._base}{path}"
        resp = requests.get(url, headers=self._headers(), params=params, timeout=self._timeout)
        return self._handle_api(resp)

    def post_api(self, path: str, body: Any) -> Any:
        url = f"{self._base}{path}"
        resp = requests.post(
            url,
            headers=self._headers({"Content-Type": "application/json"}),
            data=json.dumps(body),
            timeout=self._timeout,
        )
        return self._handle_api(resp)

    def patch_api(self, path: str, body: Any) -> Any:
        url = f"{self._base}{path}"
        resp = requests.patch(
            url,
            headers=self._headers({"Content-Type": "application/json"}),
            data=json.dumps(body),
            timeout=self._timeout,
        )
        return self._handle_api(resp)

    def post_multipart(self, path: str, *, files: Dict[str, Any], data: Dict[str, Any]) -> Any:
        url = f"{self._base}{path}"
        resp = requests.post(
            url,
            headers=self._headers(),
            files=files,
            data=data,
            timeout=self._timeout,
        )
        return self._handle_json(resp, prefix="Request failed")

    @staticmethod
    def print_response(data: Any) -> None:
        """Pretty-print clean JSON response."""
        try:
            print(json.dumps(data, indent=2))
        except Exception:
            print(data)


def _safe_json(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return text
