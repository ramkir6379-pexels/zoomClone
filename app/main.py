from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import (
    ALLOWED_ROLES,
    Role,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    require_role,
)
from app.database import Base, engine, get_db
from app.models import (
    AcademicYear,
    CaptionSegment,
    Department,
    Quiz,
    QuizQuestion,
    QuizSubmission,
    Section,
    StudentEnrollment,
    Subject,
    TeacherSubjectAssignment,
    User,
)
from app.schemas import (
    AcademicYearCreate,
    AcademicYearOut,
    AdminDashboardOut,
    CaptionFinalizeOut,
    CaptionSegmentCreate,
    CaptionSegmentOut,
    ChatMessageCreate,
    QuizOut,
    QuizQuestionCreate,
    QuizQuestionOut,
    QuizSubmissionOut,
    QuizSubmitRequest,
    ChatMessageOut,
    DepartmentCreate,
    DepartmentOut,
    LoginRequest,
    MeetingCreate,
    MeetingJoinResponse,
    MeetingOut,
    MeetingParticipantOut,
    SectionCreate,
    SectionOut,
    StudentDashboardOut,
    StudentEnrollmentCreate,
    StudentEnrollmentOut,
    SubjectCreate,
    SubjectOut,
    TeacherAssignmentCreate,
    TeacherAssignmentOut,
    TeacherDashboardOut,
    TokenResponse,
    UserCreate,
    UserOut,
)

app = FastAPI(title="ZoomClone Foundation + Phase 1/2/3/4/5 API")

meetings: dict[str, dict] = {}


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/register", response_model=UserOut)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> User:
    if user_in.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")

    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")

    user = User(
        username=user_in.username,
        full_name=user_in.full_name,
        password_hash=get_password_hash(user_in.password),
        role=user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenResponse(access_token=token)


@app.post("/departments", response_model=DepartmentOut)
def create_department(
    body: DepartmentCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(Role.ADMIN)),
) -> Department:
    item = Department(name=body.name)
    db.add(item)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Department already exists") from exc
    db.refresh(item)
    return item


@app.post("/academic-years", response_model=AcademicYearOut)
def create_academic_year(
    body: AcademicYearCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(Role.ADMIN)),
) -> AcademicYear:
    item = AcademicYear(name=body.name)
    db.add(item)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Academic year already exists") from exc
    db.refresh(item)
    return item


@app.post("/sections", response_model=SectionOut)
def create_section(
    body: SectionCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(Role.ADMIN)),
) -> Section:
    department = db.query(Department).filter(Department.id == body.department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    item = Section(name=body.name, department_id=body.department_id)
    db.add(item)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Section already exists in department") from exc
    db.refresh(item)
    return item


@app.post("/subjects", response_model=SubjectOut)
def create_subject(
    body: SubjectCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(Role.ADMIN)),
) -> Subject:
    department = db.query(Department).filter(Department.id == body.department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    item = Subject(name=body.name, department_id=body.department_id)
    db.add(item)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Subject already exists in department") from exc
    db.refresh(item)
    return item


@app.post("/assignments/teacher-subject", response_model=TeacherAssignmentOut)
def assign_teacher_subject(
    body: TeacherAssignmentCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(Role.ADMIN)),
) -> TeacherSubjectAssignment:
    teacher = db.query(User).filter(User.id == body.teacher_id, User.role == Role.TEACHER).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    subject = db.query(Subject).filter(Subject.id == body.subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    item = TeacherSubjectAssignment(teacher_id=body.teacher_id, subject_id=body.subject_id)
    db.add(item)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Assignment already exists") from exc
    db.refresh(item)
    return item


@app.post("/assignments/student-enrollments", response_model=StudentEnrollmentOut)
def enroll_student(
    body: StudentEnrollmentCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(Role.ADMIN)),
) -> StudentEnrollment:
    student = db.query(User).filter(User.id == body.student_id, User.role == Role.STUDENT).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    department = db.query(Department).filter(Department.id == body.department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    section = db.query(Section).filter(Section.id == body.section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    year = db.query(AcademicYear).filter(AcademicYear.id == body.academic_year_id).first()
    if not year:
        raise HTTPException(status_code=404, detail="Academic year not found")

    item = StudentEnrollment(
        student_id=body.student_id,
        department_id=body.department_id,
        section_id=body.section_id,
        academic_year_id=body.academic_year_id,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Enrollment already exists") from exc
    db.refresh(item)
    return item


@app.get("/dashboards/student/{student_id}", response_model=StudentDashboardOut)
def student_dashboard(
    student_id: int,
    _student: User = Depends(require_role(Role.STUDENT, Role.ADMIN)),
) -> StudentDashboardOut:
    return StudentDashboardOut(
        student_id=student_id,
        attendance_percentage=92.5,
        overall_performance_score=84.3,
        engagement_trend=[72.0, 75.5, 81.0, 79.3, 86.1],
        quiz_marks=[15, 14, 18, 16, 19],
    )


@app.get("/dashboards/teacher/{teacher_id}", response_model=TeacherDashboardOut)
def teacher_dashboard(
    teacher_id: int,
    _teacher: User = Depends(require_role(Role.TEACHER, Role.ADMIN)),
) -> TeacherDashboardOut:
    return TeacherDashboardOut(
        teacher_id=teacher_id,
        sessions_conducted=28,
        average_class_engagement=77.4,
        average_quiz_score=71.8,
        performance_score=80.2,
    )


@app.get("/dashboards/admin/overview", response_model=AdminDashboardOut)
def admin_dashboard_overview(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(Role.ADMIN)),
) -> AdminDashboardOut:
    return AdminDashboardOut(
        departments=db.query(Department).count(),
        sections=db.query(Section).count(),
        teachers=db.query(User).filter(User.role == Role.TEACHER).count(),
        students=db.query(User).filter(User.role == Role.STUDENT).count(),
        institution_performance_score=78.9,
    )


@app.post("/meetings", response_model=MeetingOut)
def create_meeting(
    body: MeetingCreate,
    current_user: User = Depends(require_role(Role.TEACHER, Role.ADMIN)),
) -> MeetingOut:
    meeting_id = str(uuid4())[:8]
    meetings[meeting_id] = {
        "id": meeting_id,
        "title": body.title,
        "host_id": current_user.id,
        "duration_limit_minutes": min(max(body.duration_limit_minutes, 30), 120),
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "participants": {},
        "chat": [],
        "attendance": set(),
    }
    return MeetingOut(
        **{
            key: meetings[meeting_id][key]
            for key in ["id", "title", "host_id", "duration_limit_minutes", "is_active"]
        }
    )


@app.post("/meetings/{meeting_id}/join", response_model=MeetingJoinResponse)
def join_meeting(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
) -> MeetingJoinResponse:
    meeting = meetings.get(meeting_id)
    if not meeting or not meeting["is_active"]:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if len(meeting["participants"]) >= 2 and current_user.id not in meeting["participants"]:
        raise HTTPException(
            status_code=409,
            detail="This Phase 2 meeting supports only 2 concurrent users",
        )

    now = datetime.now(timezone.utc).isoformat()
    meeting["participants"][current_user.id] = {
        "user_id": current_user.id,
        "role": current_user.role,
        "joined_at": now,
    }
    meeting["attendance"].add(current_user.id)
    return MeetingJoinResponse(meeting_id=meeting_id, participant_id=current_user.id, joined=True)


@app.post("/meetings/{meeting_id}/leave")
def leave_meeting(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, bool]:
    meeting = meetings.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    meeting["participants"].pop(current_user.id, None)
    return {"left": True}


@app.post("/meetings/{meeting_id}/end")
def end_meeting(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, bool]:
    meeting = meetings.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if current_user.id != meeting["host_id"] and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Only host or admin can end the meeting")
    meeting["is_active"] = False
    return {"ended": True}


@app.get("/meetings/{meeting_id}/participants", response_model=list[MeetingParticipantOut])
def list_participants(
    meeting_id: str,
    _user: User = Depends(get_current_user),
) -> list[MeetingParticipantOut]:
    meeting = meetings.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return [MeetingParticipantOut(**item) for item in meeting["participants"].values()]


@app.post("/meetings/{meeting_id}/chat", response_model=ChatMessageOut)
def send_chat_message(
    meeting_id: str,
    body: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
) -> ChatMessageOut:
    meeting = meetings.get(meeting_id)
    if not meeting or not meeting["is_active"]:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if current_user.id not in meeting["participants"]:
        raise HTTPException(status_code=403, detail="Join meeting first")

    message = {
        "user_id": current_user.id,
        "message": body.message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    meeting["chat"].append(message)
    return ChatMessageOut(**message)


@app.get("/meetings/{meeting_id}/chat", response_model=list[ChatMessageOut])
def list_chat_messages(
    meeting_id: str,
    _user: User = Depends(get_current_user),
) -> list[ChatMessageOut]:
    meeting = meetings.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return [ChatMessageOut(**msg) for msg in meeting["chat"]]


@app.post("/meetings/{meeting_id}/captions", response_model=CaptionSegmentOut)
def add_caption_segment(
    meeting_id: str,
    body: CaptionSegmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.TEACHER, Role.ADMIN)),
) -> CaptionSegment:
    meeting = meetings.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if current_user.id != meeting["host_id"] and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Only host or admin can push captions")

    if body.end_second < body.start_second:
        raise HTTPException(status_code=400, detail="end_second must be >= start_second")

    caption = CaptionSegment(
        meeting_id=meeting_id,
        teacher_id=current_user.id,
        start_second=body.start_second,
        end_second=body.end_second,
        text=body.text.strip(),
    )
    db.add(caption)
    db.commit()
    db.refresh(caption)
    return caption


@app.get("/meetings/{meeting_id}/captions", response_model=list[CaptionSegmentOut])
def list_captions(
    meeting_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[CaptionSegment]:
    meeting = meetings.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    return (
        db.query(CaptionSegment)
        .filter(CaptionSegment.meeting_id == meeting_id)
        .order_by(CaptionSegment.start_second.asc())
        .all()
    )


@app.post("/meetings/{meeting_id}/captions/finalize", response_model=CaptionFinalizeOut)
def finalize_captions(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.TEACHER, Role.ADMIN)),
) -> CaptionFinalizeOut:
    meeting = meetings.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if current_user.id != meeting["host_id"] and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Only host or admin can finalize captions")

    segments = (
        db.query(CaptionSegment)
        .filter(CaptionSegment.meeting_id == meeting_id)
        .order_by(CaptionSegment.start_second.asc())
        .all()
    )
    transcript = " ".join(item.text for item in segments)
    return CaptionFinalizeOut(meeting_id=meeting_id, segments=len(segments), transcript=transcript)



def _sentence_chunks(text: str) -> list[str]:
    parts = [item.strip() for item in text.replace("!", ".").replace("?", ".").split(".")]
    return [item for item in parts if item]


def _build_quiz_questions_from_transcript(transcript: str) -> list[dict]:
    chunks = _sentence_chunks(transcript)
    if not chunks:
        return [
            {
                "question_text": "Which statement best summarizes the class topic?",
                "option_a": "The class had no specific topic.",
                "option_b": "The class discussed core concepts from the lecture.",
                "option_c": "The class was only attendance tracking.",
                "option_d": "The class was about scheduling holidays.",
                "correct_option": "B",
            }
        ]

    questions: list[dict] = []
    for idx, chunk in enumerate(chunks[:5], start=1):
        words = chunk.split()
        key_phrase = " ".join(words[: min(6, len(words))])
        questions.append(
            {
                "question_text": f"What was discussed in point {idx}?",
                "option_a": key_phrase,
                "option_b": "Unrelated administrative notice",
                "option_c": "Sports event planning",
                "option_d": "Campus transport routes",
                "correct_option": "A",
            }
        )
    return questions


@app.post("/meetings/{meeting_id}/quizzes/generate", response_model=QuizOut)
def generate_quiz_from_captions(
    meeting_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.TEACHER, Role.ADMIN)),
) -> Quiz:
    meeting = meetings.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if current_user.id != meeting["host_id"] and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Only host or admin can generate quiz")

    segments = (
        db.query(CaptionSegment)
        .filter(CaptionSegment.meeting_id == meeting_id)
        .order_by(CaptionSegment.start_second.asc())
        .all()
    )
    transcript = " ".join(item.text for item in segments).strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="No captions available for quiz generation")

    quiz = Quiz(meeting_id=meeting_id, teacher_id=current_user.id, title=f"Quiz for {meeting['title']}")
    db.add(quiz)
    db.commit()
    db.refresh(quiz)

    generated = _build_quiz_questions_from_transcript(transcript)
    for item in generated:
        db.add(
            QuizQuestion(
                quiz_id=quiz.id,
                question_text=item["question_text"],
                option_a=item["option_a"],
                option_b=item["option_b"],
                option_c=item["option_c"],
                option_d=item["option_d"],
                correct_option=item["correct_option"],
            )
        )
    db.commit()
    return quiz


@app.get("/quizzes/{quiz_id}", response_model=QuizOut)
def get_quiz(quiz_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> Quiz:
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


@app.get("/quizzes/{quiz_id}/questions", response_model=list[QuizQuestionOut])
def list_quiz_questions(
    quiz_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[QuizQuestion]:
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    return db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).all()


@app.put("/quizzes/{quiz_id}/questions/{question_id}", response_model=QuizQuestionOut)
def update_quiz_question(
    quiz_id: int,
    question_id: int,
    body: QuizQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.TEACHER, Role.ADMIN)),
) -> QuizQuestion:
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if current_user.id != quiz.teacher_id and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Only quiz owner or admin can edit")

    if body.correct_option not in {"A", "B", "C", "D"}:
        raise HTTPException(status_code=400, detail="correct_option must be A/B/C/D")

    question = (
        db.query(QuizQuestion)
        .filter(QuizQuestion.id == question_id, QuizQuestion.quiz_id == quiz_id)
        .first()
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    question.question_text = body.question_text
    question.option_a = body.option_a
    question.option_b = body.option_b
    question.option_c = body.option_c
    question.option_d = body.option_d
    question.correct_option = body.correct_option
    db.commit()
    db.refresh(question)
    return question


@app.post("/quizzes/{quiz_id}/publish", response_model=QuizOut)
def publish_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.TEACHER, Role.ADMIN)),
) -> Quiz:
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if current_user.id != quiz.teacher_id and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Only quiz owner or admin can publish")

    quiz.status = "published"
    db.commit()
    db.refresh(quiz)
    return quiz


@app.post("/quizzes/{quiz_id}/submit", response_model=QuizSubmissionOut)
def submit_quiz(
    quiz_id: int,
    body: QuizSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.STUDENT)),
) -> QuizSubmissionOut:
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz.status != "published":
        raise HTTPException(status_code=400, detail="Quiz is not published")

    existing = (
        db.query(QuizSubmission)
        .filter(QuizSubmission.quiz_id == quiz_id, QuizSubmission.student_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Quiz already submitted")

    questions = db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).all()
    question_map = {item.id: item for item in questions}

    score = 0
    for answer in body.answers:
        q = question_map.get(answer.question_id)
        if q and answer.selected_option.upper() == q.correct_option:
            score += 1

    submission = QuizSubmission(
        quiz_id=quiz_id,
        student_id=current_user.id,
        score=score,
        total=len(questions),
    )
    db.add(submission)
    db.commit()
    return QuizSubmissionOut(quiz_id=quiz_id, student_id=current_user.id, score=score, total=len(questions))


@app.post("/meetings/{meeting_id}/engagement-samples", response_model=EngagementSampleOut)
def record_engagement_sample(
    meeting_id: str,
    body: EngagementSampleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.TEACHER, Role.ADMIN)),
) -> EngagementSample:
    meeting = meetings.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    if current_user.id != meeting["host_id"] and current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Only host or admin can record engagement")

    student = db.query(User).filter(User.id == body.student_id, User.role == Role.STUDENT).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if body.engagement_score < 0 or body.engagement_score > 100:
        raise HTTPException(status_code=400, detail="engagement_score must be between 0 and 100")

    if body.captured_second < 0:
        raise HTTPException(status_code=400, detail="captured_second must be >= 0")

    sample = EngagementSample(
        meeting_id=meeting_id,
        student_id=body.student_id,
        captured_second=body.captured_second,
        engagement_score=body.engagement_score,
    )
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return sample


@app.get("/meetings/{meeting_id}/engagement-summary", response_model=EngagementMeetingSummaryOut)
def meeting_engagement_summary(
    meeting_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> EngagementMeetingSummaryOut:
    meeting = meetings.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    samples = db.query(EngagementSample).filter(EngagementSample.meeting_id == meeting_id).all()
    if not samples:
        return EngagementMeetingSummaryOut(meeting_id=meeting_id, students=[], class_average_score=0.0)

    bucket: dict[int, list[int]] = {}
    for item in samples:
        bucket.setdefault(item.student_id, []).append(item.engagement_score)

    students_summary = []
    all_scores: list[int] = []
    for student_id, scores in bucket.items():
        all_scores.extend(scores)
        students_summary.append(
            EngagementStudentSummaryOut(
                student_id=student_id,
                samples=len(scores),
                average_score=round(sum(scores) / len(scores), 2),
            )
        )

    class_avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0
    students_summary.sort(key=lambda item: item.student_id)
    return EngagementMeetingSummaryOut(
        meeting_id=meeting_id,
        students=students_summary,
        class_average_score=class_avg,
    )


@app.get("/students/{student_id}/engagement/overall", response_model=StudentEngagementOverallOut)
def student_engagement_overall(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentEngagementOverallOut:
    if current_user.role == Role.STUDENT and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Students can only access their own engagement data")

    student = db.query(User).filter(User.id == student_id, User.role == Role.STUDENT).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    samples = db.query(EngagementSample).filter(EngagementSample.student_id == student_id).all()
    if not samples:
        return StudentEngagementOverallOut(student_id=student_id, samples=0, overall_average_score=0.0)

    scores = [item.engagement_score for item in samples]
    return StudentEngagementOverallOut(
        student_id=student_id,
        samples=len(scores),
        overall_average_score=round(sum(scores) / len(scores), 2),
    )


@app.get("/analytics/students/{student_id}/performance", response_model=StudentPerformanceOut)
def student_performance_analytics(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StudentPerformanceOut:
    if current_user.role == Role.STUDENT and current_user.id != student_id:
        raise HTTPException(status_code=403, detail="Students can only access their own analytics")

    student = db.query(User).filter(User.id == student_id, User.role == Role.STUDENT).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    submissions = db.query(QuizSubmission).filter(QuizSubmission.student_id == student_id).all()
    quiz_percents = [(item.score / item.total) * 100 for item in submissions if item.total > 0]
    quiz_avg = round(sum(quiz_percents) / len(quiz_percents), 2) if quiz_percents else 0.0

    samples = db.query(EngagementSample).filter(EngagementSample.student_id == student_id).all()
    engagement_scores = [item.engagement_score for item in samples]
    engagement_avg = round(sum(engagement_scores) / len(engagement_scores), 2) if engagement_scores else 0.0

    composite = round((quiz_avg * 0.6) + (engagement_avg * 0.4), 2)
    return StudentPerformanceOut(
        student_id=student_id,
        quiz_average_percent=quiz_avg,
        engagement_average=engagement_avg,
        composite_score=composite,
    )


@app.get("/analytics/teachers/{teacher_id}/performance", response_model=TeacherPerformanceOut)
def teacher_performance_analytics(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(Role.TEACHER, Role.ADMIN)),
) -> TeacherPerformanceOut:
    if current_user.role == Role.TEACHER and current_user.id != teacher_id:
        raise HTTPException(status_code=403, detail="Teachers can only access their own analytics")

    teacher = db.query(User).filter(User.id == teacher_id, User.role == Role.TEACHER).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    quizzes = db.query(Quiz).filter(Quiz.teacher_id == teacher_id, Quiz.status == "published").all()
    quiz_ids = [item.id for item in quizzes]
    submissions = db.query(QuizSubmission).filter(QuizSubmission.quiz_id.in_(quiz_ids)).all() if quiz_ids else []
    submission_count = len(submissions)
    quiz_percents = [(item.score / item.total) * 100 for item in submissions if item.total > 0]
    avg_quiz = round(sum(quiz_percents) / len(quiz_percents), 2) if quiz_percents else 0.0

    meeting_ids = [item.meeting_id for item in quizzes]
    engagement_samples = db.query(EngagementSample).filter(EngagementSample.meeting_id.in_(meeting_ids)).all() if meeting_ids else []
    engagement_vals = [item.engagement_score for item in engagement_samples]
    avg_engagement = round(sum(engagement_vals) / len(engagement_vals), 2) if engagement_vals else 0.0

    performance = round((avg_quiz * 0.7) + (avg_engagement * 0.3), 2)
    return TeacherPerformanceOut(
        teacher_id=teacher_id,
        quizzes_published=len(quizzes),
        student_submissions=submission_count,
        avg_student_quiz_percent=avg_quiz,
        avg_student_engagement=avg_engagement,
        performance_score=performance,
    )


@app.get("/analytics/admin/institution", response_model=InstitutionAnalyticsOut)
def institution_analytics(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(Role.ADMIN)),
) -> InstitutionAnalyticsOut:
    total_students = db.query(User).filter(User.role == Role.STUDENT).count()
    total_teachers = db.query(User).filter(User.role == Role.TEACHER).count()
    total_meetings = len(meetings)
    total_quizzes_published = db.query(Quiz).filter(Quiz.status == "published").count()

    submissions = db.query(QuizSubmission).all()
    quiz_percents = [(item.score / item.total) * 100 for item in submissions if item.total > 0]
    avg_quiz = round(sum(quiz_percents) / len(quiz_percents), 2) if quiz_percents else 0.0

    engagement_samples = db.query(EngagementSample).all()
    engagement_vals = [item.engagement_score for item in engagement_samples]
    avg_engagement = round(sum(engagement_vals) / len(engagement_vals), 2) if engagement_vals else 0.0

    institution_score = round((avg_quiz * 0.65) + (avg_engagement * 0.35), 2)
    return InstitutionAnalyticsOut(
        total_students=total_students,
        total_teachers=total_teachers,
        total_meetings=total_meetings,
        total_quizzes_published=total_quizzes_published,
        avg_quiz_percent=avg_quiz,
        avg_engagement=avg_engagement,
        institution_score=institution_score,
    )
