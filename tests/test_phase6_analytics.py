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


def test_phase6_student_teacher_admin_analytics() -> None:
    reset_db()
    admin = register("admin6", "admin")
    teacher = register("teacher6", "teacher")
    student = register("student6", "student")

    admin_headers = {"Authorization": f"Bearer {login('admin6')}"}
    teacher_headers = {"Authorization": f"Bearer {login('teacher6')}"}
    student_headers = {"Authorization": f"Bearer {login('student6')}"}

    meeting = client.post("/meetings", headers=teacher_headers, json={"title": "Physics"})
    assert meeting.status_code == 200
    meeting_id = meeting.json()["id"]

    assert client.post(f"/meetings/{meeting_id}/join", headers=teacher_headers).status_code == 200
    assert client.post(f"/meetings/{meeting_id}/join", headers=student_headers).status_code == 200

    assert client.post(
        f"/meetings/{meeting_id}/captions",
        headers=teacher_headers,
        json={"start_second": 0, "end_second": 4, "text": "Force equals mass into acceleration."},
    ).status_code == 200

    generated = client.post(f"/meetings/{meeting_id}/quizzes/generate", headers=teacher_headers)
    assert generated.status_code == 200
    quiz_id = generated.json()["id"]

    questions = client.get(f"/quizzes/{quiz_id}/questions", headers=teacher_headers)
    qid = questions.json()[0]["id"]
    assert client.post(f"/quizzes/{quiz_id}/publish", headers=teacher_headers).status_code == 200

    submitted = client.post(
        f"/quizzes/{quiz_id}/submit",
        headers=student_headers,
        json={"answers": [{"question_id": qid, "selected_option": "A"}]},
    )
    assert submitted.status_code == 200

    assert client.post(
        f"/meetings/{meeting_id}/engagement-samples",
        headers=teacher_headers,
        json={"student_id": student["id"], "captured_second": 10, "engagement_score": 88},
    ).status_code == 200

    stu_analytics = client.get(
        f"/analytics/students/{student['id']}/performance",
        headers=student_headers,
    )
    assert stu_analytics.status_code == 200
    assert stu_analytics.json()["composite_score"] >= 0

    teacher_analytics = client.get(
        f"/analytics/teachers/{teacher['id']}/performance",
        headers=teacher_headers,
    )
    assert teacher_analytics.status_code == 200
    assert teacher_analytics.json()["quizzes_published"] >= 1

    admin_analytics = client.get("/analytics/admin/institution", headers=admin_headers)
    assert admin_analytics.status_code == 200
    assert admin_analytics.json()["total_students"] >= 1


def test_student_cannot_access_another_student_analytics() -> None:
    reset_db()
    s1 = register("s61", "student")
    s2 = register("s62", "student")
    s1_headers = {"Authorization": f"Bearer {login('s61')}"}

    denied = client.get(f"/analytics/students/{s2['id']}/performance", headers=s1_headers)
    assert denied.status_code == 403
