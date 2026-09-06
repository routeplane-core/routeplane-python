"""Legacy feedback wire and pre-dispatch validation on every exposed path."""

import json

import httpx
import pytest
import pytest_asyncio
import respx

from routeplane import AsyncRouteplane, Routeplane
from routeplane.resources import FeedbackResource

BASE = "https://gateway.example.test/v1"


@pytest_asyncio.fixture(params=["resource", "sync_client", "async_client"])
async def feedback(request):
    if request.param == "resource":
        with httpx.Client() as transport:
            yield FeedbackResource(api_key="rp_test", base_url=BASE, http_client=transport)
    elif request.param == "sync_client":
        with Routeplane(api_key="rp_test", base_url=BASE) as client:
            yield client.feedback
    else:
        async with AsyncRouteplane(api_key="rp_test", base_url=BASE) as client:
            # REST helpers on AsyncRouteplane are intentionally synchronous.
            yield client.feedback


@pytest.mark.parametrize("score", [-10, 0, 10, -10.0, -1.0, -0.0, 1.0, 10.0])
@pytest.mark.parametrize("comment", [{}, {"comment": None}, {"comment": ""}])
@pytest.mark.parametrize("status", [200, 204])
@respx.mock
async def test_feedback_legacy_wire(feedback, score, comment, status):
    route = respx.post(f"{BASE}/feedback").mock(return_value=httpx.Response(status))
    assert feedback.create(request_id="req_from_gateway", score=score, **comment) is None
    assert route.call_count == 1
    sent = route.calls.last.request
    body = json.loads(sent.content)
    assert body == {"trace_id": "req_from_gateway", "value": int(score)}
    assert type(body["value"]) is int
    assert sent.headers["x-routeplane-api-key"] == "rp_test"


@pytest.mark.parametrize(
    "score", [-11, 11, -10.1, 10.1, -0.5, 0.5, float("nan"), float("inf"), float("-inf"), 10**1000]
)
@respx.mock
async def test_feedback_invalid_score_value_never_dispatches(feedback, score):
    with pytest.raises(ValueError, match="score.*integer.*-10.*10"):
        feedback.create(request_id="req_1", score=score)
    assert len(respx.calls) == 0


@pytest.mark.parametrize("score", [True, False, None, "1", [], {}, 1 + 0j])
@respx.mock
async def test_feedback_invalid_score_type_never_dispatches(feedback, score):
    with pytest.raises(TypeError, match="score.*number"):
        feedback.create(request_id="req_1", score=score)
    assert len(respx.calls) == 0


@pytest.mark.parametrize("comment", ["note", " ", "\t", "\n", "\u200b"])
@respx.mock
async def test_feedback_unsupported_comment_never_dispatches(feedback, comment):
    with pytest.raises(ValueError, match="comment.*not supported"):
        feedback.create(request_id="req_1", score=0, comment=comment)
    assert len(respx.calls) == 0


@pytest.mark.parametrize("comment", [False, 0, [], {}])
@respx.mock
async def test_feedback_invalid_comment_type_never_dispatches(feedback, comment):
    with pytest.raises(TypeError, match="comment"):
        feedback.create(request_id="req_1", score=0, comment=comment)
    assert len(respx.calls) == 0


@respx.mock
async def test_feedback_preserves_http_error_contract(feedback):
    route = respx.post(f"{BASE}/feedback").mock(return_value=httpx.Response(401))
    with pytest.raises(httpx.HTTPStatusError) as error:
        feedback.create(request_id="req_1", score=0)
    assert error.value.response.status_code == 401
    assert route.call_count == 1
