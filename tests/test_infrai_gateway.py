import httpx

from course_guard.infrai_gateway import InfraiGateway


def test_budget_request_retries_429_and_keeps_exact_fields() -> None:
    requests: list[httpx.Request] = []
    responses = iter(
        [
            httpx.Response(
                429,
                headers={"Retry-After": "0"},
                json={"ok": False, "data": None, "error": {}, "metadata": {}},
            ),
            httpx.Response(
                200,
                json={"ok": True, "data": {"period": "monthly"}, "error": None, "metadata": {}},
            ),
        ]
    )

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        response = next(responses)
        response.request = request
        return response

    gateway = InfraiGateway(
        "test-key",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep=lambda _: None,
    )

    result = gateway.set_monthly_cap(hard_cap_usd=125, alert_threshold_usd=100)

    assert result == {"period": "monthly"}
    assert len(requests) == 2
    assert requests[0].method == "PUT"
    assert requests[0].read() == (
        b'{"hard_cap_usd":125,"period":"monthly","alert_threshold_usd":100}'
    )
