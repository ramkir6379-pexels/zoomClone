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


def test_phase4_generate_edit_publish_submit_quiz() -> None:
    reset_db()
    register("teacherq", "teacher")
    register("studentq", "student")

    teacher_headers = {"Authorization": f"Bearer {login('teacherq')}"}
    student_headers = {"Authorization": f"Bearer {login('studentq')}"}

    meeting = client.post("/meetings", headers=teacher_headers, json={"title": "DBMS"})
    assert meeting.status_code == 200
    meeting_id = meeting.json()["id"]

    assert client.post(f"/meetings/{meeting_id}/join", headers=teacher_headers).status_code == 200

    assert client.post(
        f"/meetings/{meeting_id}/captions",
        headers=teacher_headers,
        json={"start_second": 0, "end_second": 5, "text": "Normalization reduces redundancy."},
    ).status_code == 200

    generated = client.post(f"/meetings/{meeting_id}/quizzes/generate", headers=teacher_headers)
    assert generated.status_code == 200
    quiz_id = generated.json()["id"]

    questions = client.get(f"/quizzes/{quiz_id}/questions", headers=teacher_headers)
    assert questions.status_code == 200
    first_question = questions.json()[0]

    updated = client.put(
        f"/quizzes/{quiz_id}/questions/{first_question['id']}",
        headers=teacher_headers,
        json={
            "question_text": "What does normalization help with?",
            "option_a": "Reducing redundancy",
            "option_b": "Increasing duplication",
            "option_c": "Removing indexes",
            "option_d": "Deleting tables",
            "correct_option": "A",
        },
    )
    assert updated.status_code == 200

    published = client.post(f"/quizzes/{quiz_id}/publish", headers=teacher_headers)
    assert published.status_code == 200

    submit = client.post(
        f"/quizzes/{quiz_id}/submit",
        headers=student_headers,
        json={"answers": [{"question_id": first_question["id"], "selected_option": "A"}]},
    )
    assert submit.status_code == 200
    assert submit.json()["score"] >= 0


def test_student_cannot_generate_quiz() -> None:
    reset_db()
    register("teachere", "teacher")
    register("studente", "student")

    teacher_headers = {"Authorization": f"Bearer {login('teachere')}"}
    student_headers = {"Authorization": f"Bearer {login('studente')}"}

    meeting = client.post("/meetings", headers=teacher_headers, json={"title": "AI"})
    meeting_id = meeting.json()["id"]

    denied = client.post(f"/meetings/{meeting_id}/quizzes/generate", headers=student_headers)
    assert denied.status_code == 403
