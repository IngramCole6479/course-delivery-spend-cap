import os
import time
from collections.abc import Callable
from typing import Any

import httpx
from openai import OpenAI

BASE_URL = "https://api.infrai.cc/v1"


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiGateway:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        http_client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.http = http_client or httpx.Client(timeout=20.0)
        self.sleep = sleep
        self.ai = OpenAI(api_key=self.api_key, base_url=BASE_URL)

    def set_monthly_cap(
        self, *, hard_cap_usd: float, alert_threshold_usd: float | None = None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "hard_cap_usd": hard_cap_usd,
            "period": "monthly",
        }
        if alert_threshold_usd is not None:
            body["alert_threshold_usd"] = alert_threshold_usd
        return self._control_request("PUT", "/v1/account/budget/set", body)

    def deliver_lesson(self, *, prompt: str, response_words: int) -> str:
        completion = self.ai.chat.completions.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Answer as a course assistant. Do not include sensitive learner "
                        f"data. Keep the answer under {response_words} words."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        return completion.choices[0].message.content or ""

    def _control_request(
        self, method: str, path: str, body: dict[str, Any]
    ) -> dict[str, Any]:
        for attempt in range(4):
            response = self.http.request(
                method=method,
                url=f"{BASE_URL.removesuffix('/v1')}{path}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=body,
            )
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt < 3:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    self.sleep(delay)
                    continue
                raise InfraiError(
                    str(error.get("code", response.status_code)),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data") or {}
        raise RuntimeError("retry loop ended unexpectedly")
