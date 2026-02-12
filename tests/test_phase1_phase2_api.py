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


def test_dashboard_endpoints_by_role() -> None:
    reset_db()
    register("adminx", "admin")
    register("teacherx", "teacher")
    register("studentx", "student")

    admin_token = login("adminx")
    teacher_token = login("teacherx")
    student_token = login("studentx")

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    assert client.get("/dashboards/admin/overview", headers=admin_headers).status_code == 200
    assert client.get("/dashboards/teacher/2", headers=teacher_headers).status_code == 200
    assert client.get("/dashboards/student/3", headers=student_headers).status_code == 200


def test_phase2_meeting_flow() -> None:
    reset_db()
    register("teacher1", "teacher")
    register("student1", "student")

    teacher_token = login("teacher1")
    student_token = login("student1")
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    student_headers = {"Authorization": f"Bearer {student_token}"}

    created = client.post("/meetings", headers=teacher_headers, json={"title": "OS Class"})
    assert created.status_code == 200
    meeting_id = created.json()["id"]

    join_teacher = client.post(f"/meetings/{meeting_id}/join", headers=teacher_headers)
    assert join_teacher.status_code == 200

    join_student = client.post(f"/meetings/{meeting_id}/join", headers=student_headers)
    assert join_student.status_code == 200

    chat = client.post(
        f"/meetings/{meeting_id}/chat",
        headers=student_headers,
        json={"message": "Hello teacher"},
    )
    assert chat.status_code == 200

    participants = client.get(f"/meetings/{meeting_id}/participants", headers=teacher_headers)
    assert participants.status_code == 200
    assert len(participants.json()) == 2

    ended = client.post(f"/meetings/{meeting_id}/end", headers=teacher_headers)
    assert ended.status_code == 200
