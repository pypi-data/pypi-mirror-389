from __future__ import annotations

from typing import Any, Dict, List

from .http import HttpClient


class LlmsClient:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def list(self) -> List[Dict[str, Any]]:
        return self._http.get_json("/llms", prefix="LLMs request failed")

    def get(self, llm_id: int | str) -> Dict[str, Any]:
        if llm_id is None:
            raise ValueError("id is required")
        return self._http.get_json(f"/llms/{llm_id}", prefix="LLM fetch failed")

