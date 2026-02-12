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


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_role_guard_for_department_creation() -> None:
    reset_db()
    register("alice", "student")
    student_token = login("alice")

    response = client.post(
        "/departments",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"name": "Computer Science"},
    )
    assert response.status_code == 403


def test_admin_foundation_workflow() -> None:
    reset_db()
    admin = register("admin1", "admin")
    teacher = register("teacher1", "teacher")
    student = register("student1", "student")

    assert admin["role"] == "admin"

    admin_token = login("admin1")
    headers = {"Authorization": f"Bearer {admin_token}"}

    dep = client.post("/departments", headers=headers, json={"name": "CSE"})
    assert dep.status_code == 200
    dep_id = dep.json()["id"]

    year = client.post("/academic-years", headers=headers, json={"name": "2026"})
    assert year.status_code == 200
    year_id = year.json()["id"]

    section = client.post(
        "/sections",
        headers=headers,
        json={"name": "A", "department_id": dep_id},
    )
    assert section.status_code == 200
    section_id = section.json()["id"]

    subject = client.post(
        "/subjects",
        headers=headers,
        json={"name": "Operating Systems", "department_id": dep_id},
    )
    assert subject.status_code == 200
    subject_id = subject.json()["id"]

    teacher_assignment = client.post(
        "/assignments/teacher-subject",
        headers=headers,
        json={"teacher_id": teacher["id"], "subject_id": subject_id},
    )
    assert teacher_assignment.status_code == 200

    student_enrollment = client.post(
        "/assignments/student-enrollments",
        headers=headers,
        json={
            "student_id": student["id"],
            "department_id": dep_id,
            "section_id": section_id,
            "academic_year_id": year_id,
        },
    )
    assert student_enrollment.status_code == 200
