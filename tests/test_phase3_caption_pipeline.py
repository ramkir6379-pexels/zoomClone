from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


client = TestClient(app)


def reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def register(username: str, role: str, password: str = "pass1234") -> dict:
    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "full_name": username.title(),
            "password": password,
            "role": role,
        },
    )
    assert response.status_code == 200
    return response.json()


def login(username: str, password: str = "pass1234") -> str:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_phase3_caption_collection_and_finalize() -> None:
    reset_db()
    register("teacherc", "teacher")
    register("studentc", "student")

    teacher_headers = {"Authorization": f"Bearer {login('teacherc')}"}
    student_headers = {"Authorization": f"Bearer {login('studentc')}"}

    create_meeting = client.post("/meetings", headers=teacher_headers, json={"title": "Networks"})
    assert create_meeting.status_code == 200
    meeting_id = create_meeting.json()["id"]

    assert client.post(f"/meetings/{meeting_id}/join", headers=teacher_headers).status_code == 200
    assert client.post(f"/meetings/{meeting_id}/join", headers=student_headers).status_code == 200

    c1 = client.post(
        f"/meetings/{meeting_id}/captions",
        headers=teacher_headers,
        json={"start_second": 0, "end_second": 7, "text": "Today we study routing protocols."},
    )
    assert c1.status_code == 200

    c2 = client.post(
        f"/meetings/{meeting_id}/captions",
        headers=teacher_headers,
        json={"start_second": 8, "end_second": 15, "text": "Distance vector and link state are key."},
    )
    assert c2.status_code == 200

    listed = client.get(f"/meetings/{meeting_id}/captions", headers=student_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 2

    finalized = client.post(f"/meetings/{meeting_id}/captions/finalize", headers=teacher_headers)
    assert finalized.status_code == 200
    data = finalized.json()
    assert data["segments"] == 2
    assert "routing protocols" in data["transcript"]


def test_student_cannot_push_captions() -> None:
    reset_db()
    register("teacherd", "teacher")
    register("studentd", "student")

    teacher_headers = {"Authorization": f"Bearer {login('teacherd')}"}
    student_headers = {"Authorization": f"Bearer {login('studentd')}"}

    create_meeting = client.post("/meetings", headers=teacher_headers, json={"title": "OS"})
    meeting_id = create_meeting.json()["id"]

    denied = client.post(
        f"/meetings/{meeting_id}/captions",
        headers=student_headers,
        json={"start_second": 0, "end_second": 1, "text": "I should not add this."},
    )
    assert denied.status_code == 403
