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


def test_phase5_record_and_summarize_engagement() -> None:
    reset_db()
    register("teacherg", "teacher")
    student1 = register("studentg1", "student")
    student2 = register("studentg2", "student")

    teacher_headers = {"Authorization": f"Bearer {login('teacherg')}"}
    student1_headers = {"Authorization": f"Bearer {login('studentg1')}"}

    meeting = client.post("/meetings", headers=teacher_headers, json={"title": "Math"})
    assert meeting.status_code == 200
    meeting_id = meeting.json()["id"]

    samples = [
        {"student_id": student1["id"], "captured_second": 10, "engagement_score": 78},
        {"student_id": student1["id"], "captured_second": 20, "engagement_score": 82},
        {"student_id": student2["id"], "captured_second": 10, "engagement_score": 64},
    ]

    for payload in samples:
        resp = client.post(
            f"/meetings/{meeting_id}/engagement-samples",
            headers=teacher_headers,
            json=payload,
        )
        assert resp.status_code == 200

    summary = client.get(f"/meetings/{meeting_id}/engagement-summary", headers=teacher_headers)
    assert summary.status_code == 200
    data = summary.json()
    assert len(data["students"]) == 2
    assert data["class_average_score"] > 0

    personal = client.get(
        f"/students/{student1['id']}/engagement/overall",
        headers=student1_headers,
    )
    assert personal.status_code == 200
    assert personal.json()["samples"] == 2


def test_student_cannot_view_other_student_engagement() -> None:
    reset_db()
    s1 = register("studenth1", "student")
    s2 = register("studenth2", "student")

    s1_headers = {"Authorization": f"Bearer {login('studenth1')}"}
    denied = client.get(f"/students/{s2['id']}/engagement/overall", headers=s1_headers)
    assert denied.status_code == 403
