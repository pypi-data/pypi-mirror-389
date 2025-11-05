from __future__ import annotations

import os
from typing import Optional

from .http import HttpClient
from .languages import LanguagesClient
from .llms import LlmsClient
from .voices import VoicesClient
from .calls import CallsClient
from .batch_calls import BatchCallsClient
from .agents import AgentsClient

DEFAULT_BASE_URL = "https://api.dialnexa.com"


class NexaClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout_ms: Optional[int] = None,
    ) -> None:
        env_api_key = api_key or os.getenv("DIALNEXA_API_KEY") or ""

        if not env_api_key:
            raise ValueError("DIALNEXA_API_KEY is required")

        self._base_url = DEFAULT_BASE_URL
        self._api_key = env_api_key
        self._timeout = (timeout_ms / 1000.0) if timeout_ms else None

        http = HttpClient(
            base_url=self._base_url,
            api_key=self._api_key,
            timeout=self._timeout,
        )

        self.languages = LanguagesClient(http)
        self.llms = LlmsClient(http)
        self.voices = VoicesClient(http)
        self.calls = CallsClient(http)
        self.batch_calls = BatchCallsClient(http)
        self.agents = AgentsClient(http)
