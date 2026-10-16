import web.app as web_app

def test_health(client):
    r = client.get("/health")

    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_pipeline_hides_contact_email(client):
    r = client.get("/pipeline")

    assert r.status_code == 200
    assert r.json()["count"] > 0

    for row in r.json()["applications"]:
        assert "contact_email" not in row


def test_oversized_body_rejected(client):
    r = client.post(
        "/chat",
        json={"message": "x" * 30000}
    )

    assert r.status_code == 413


def test_close_unknown_session(client):
    r = client.post(
        "/session/close",
        json={"session_id": "nope"}
    )

    assert r.status_code == 200
    assert r.json() == {"closed": False}


def test_chat_streams_events(client, fake_session, monkeypatch):

    async def fake_get_or_open(settings, sessions, session_id):
        return fake_session

    async def fake_run_turn(
        agent,
        chat,
        text,
        ask_approval,
        max_turns=8,
        emit=None
    ):
        await emit(
            "tool_call",
            {
                "name": "list_applications",
                "arguments": "{}"
            }
        )

        return "hello from stub"

    monkeypatch.setattr(
        web_app,
        "get_or_open_session",
        fake_get_or_open
    )

    monkeypatch.setattr(
        web_app,
        "run_turn",
        fake_run_turn
    )

    r = client.post(
        "/chat",
        json={"message": "hi"}
    )

    body = r.text

    assert r.status_code == 200

    assert "event: session" in body
    assert "event: tool_call" in body
    assert "event: final" in body
    assert "hello from stub" in body

    assert (
        body.index("event: session")
        < body.index("event: tool_call")
        < body.index("event: final")
    )
