from __future__ import annotations

from typing import Any, Dict, IO, Optional, Tuple

from .http import HttpClient


def _guess_content_type(filename: Optional[str]) -> str:
    fname = (filename or "").lower()
    if fname.endswith(".csv"):
        return "text/csv"
    if fname.endswith(".xls"):
        return "application/vnd.ms-excel"
    if fname.endswith(".xlsx"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "application/octet-stream"


class BatchCallsClient:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def create(
        self,
        *,
        file: IO[bytes] | bytes,
        title: str,
        agent_id: str,
        agent_version_number: int,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not file:
            raise ValueError("file is required")
        if not title:
            raise ValueError("title is required")
        if not agent_id:
            raise ValueError("agent_id is required")
        if agent_version_number is None or agent_version_number < 0:
            raise ValueError("agentVersionNumber must be >= 0")

        content_type = _guess_content_type(filename or getattr(file, "name", ""))

        files: Dict[str, Tuple[str, IO[bytes] | bytes, str]] = {
            "file": (filename or getattr(file, "name", "leads"), file, content_type)
        }
        data = {
            "title": title,
            "agent_id": agent_id,
            "agent_version_number": str(agent_version_number),
        }
        return self._http.post_multipart("/batch-calls", files=files, data=data)
