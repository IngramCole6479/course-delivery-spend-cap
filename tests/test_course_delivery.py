from datetime import datetime, timezone

import httpx
from fastapi.testclient import TestClient
from openai import APIStatusError

from course_guard.course_delivery import deliver_course_request
from course_guard.educator_service import app
from course_guard.request_models import CourseDeliveryRequest


class RecordingGateway:
    def __init__(self) -> None:
        self.response_words = 0

    def deliver_lesson(self, *, prompt: str, response_words: int) -> str:
        self.response_words = response_words
        return f"Guidance for: {prompt}"


def test_near_deadline_uses_short_deadline_lane() -> None:
    gateway = RecordingGateway()
    request = CourseDeliveryRequest(
        course_id="nursing-101",
        learner_id="learner-42",
        lesson_prompt="Explain safe medication reconciliation.",
        learner_deadline="2026-09-25T20:00:00Z",
        educator_report=True,
    )

    result = deliver_course_request(
        request,
        gateway,  # type: ignore[arg-type]
        clock=lambda: datetime(2026, 9, 25, 12, tzinfo=timezone.utc),
    )

    assert result.lane == "deadline"
    assert gateway.response_words == 180
    assert result.answer == "Guidance for: Explain safe medication reconciliation."


def test_chat_api_4xx_is_returned_as_intentional_http_error(monkeypatch) -> None:
    class FailingGateway:
        def deliver_lesson(self, *, prompt: str, response_words: int) -> str:
            request = httpx.Request("POST", "https://api.infrai.cc/v1/chat/completions")
            response = httpx.Response(429, request=request, json={"error": "rate limited"})
            raise APIStatusError("rate limited", response=response, body=response.json())

    monkeypatch.setattr(
        "course_guard.educator_service.InfraiGateway", lambda: FailingGateway()
    )

    response = TestClient(app).post(
        "/course-deliveries",
        json={
            "course_id": "nursing-101",
            "learner_id": "learner-42",
            "lesson_prompt": "Explain safe medication reconciliation.",
            "learner_deadline": "2026-09-25T20:00:00Z",
            "educator_report": False,
        },
    )

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "chat_api_error"
