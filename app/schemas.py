from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    username: str
    full_name: str
    password: str
    role: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class DepartmentCreate(BaseModel):
    name: str


class DepartmentOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class AcademicYearCreate(BaseModel):
    name: str


class AcademicYearOut(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class SectionCreate(BaseModel):
    name: str
    department_id: int


class SectionOut(BaseModel):
    id: int
    name: str
    department_id: int

    model_config = ConfigDict(from_attributes=True)


class SubjectCreate(BaseModel):
    name: str
    department_id: int


class SubjectOut(BaseModel):
    id: int
    name: str
    department_id: int

    model_config = ConfigDict(from_attributes=True)


class TeacherAssignmentCreate(BaseModel):
    teacher_id: int
    subject_id: int


class TeacherAssignmentOut(BaseModel):
    id: int
    teacher_id: int
    subject_id: int

    model_config = ConfigDict(from_attributes=True)


class StudentEnrollmentCreate(BaseModel):
    student_id: int
    department_id: int
    section_id: int
    academic_year_id: int


class StudentEnrollmentOut(BaseModel):
    id: int
    student_id: int
    department_id: int
    section_id: int
    academic_year_id: int

    model_config = ConfigDict(from_attributes=True)


class StudentDashboardOut(BaseModel):
    student_id: int
    attendance_percentage: float
    overall_performance_score: float
    engagement_trend: list[float]
    quiz_marks: list[int]


class TeacherDashboardOut(BaseModel):
    teacher_id: int
    sessions_conducted: int
    average_class_engagement: float
    average_quiz_score: float
    performance_score: float


class AdminDashboardOut(BaseModel):
    departments: int
    sections: int
    teachers: int
    students: int
    institution_performance_score: float


class MeetingCreate(BaseModel):
    title: str
    duration_limit_minutes: int = 120


class MeetingOut(BaseModel):
    id: str
    title: str
    host_id: int
    duration_limit_minutes: int
    is_active: bool


class MeetingJoinResponse(BaseModel):
    meeting_id: str
    participant_id: int
    joined: bool


class MeetingParticipantOut(BaseModel):
    user_id: int
    role: str
    joined_at: str


class ChatMessageCreate(BaseModel):
    message: str


class ChatMessageOut(BaseModel):
    user_id: int
    message: str
    timestamp: str


class CaptionSegmentCreate(BaseModel):
    start_second: int
    end_second: int
    text: str


class CaptionSegmentOut(BaseModel):
    id: int
    meeting_id: str
    teacher_id: int
    start_second: int
    end_second: int
    text: str

    model_config = ConfigDict(from_attributes=True)


class CaptionFinalizeOut(BaseModel):
    meeting_id: str
    segments: int
    transcript: str


class QuizOut(BaseModel):
    id: int
    meeting_id: str
    teacher_id: int
    title: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class QuizQuestionOut(BaseModel):
    id: int
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str

    model_config = ConfigDict(from_attributes=True)


class QuizQuestionCreate(BaseModel):
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str


class QuizSubmitItem(BaseModel):
    question_id: int
    selected_option: str


class QuizSubmitRequest(BaseModel):
    answers: list[QuizSubmitItem]


class QuizSubmissionOut(BaseModel):
    quiz_id: int
    student_id: int
    score: int
    total: int


class EngagementSampleCreate(BaseModel):
    student_id: int
    captured_second: int
    engagement_score: int


class EngagementSampleOut(BaseModel):
    id: int
    meeting_id: str
    student_id: int
    captured_second: int
    engagement_score: int

    model_config = ConfigDict(from_attributes=True)


class EngagementStudentSummaryOut(BaseModel):
    student_id: int
    samples: int
    average_score: float


class EngagementMeetingSummaryOut(BaseModel):
    meeting_id: str
    students: list[EngagementStudentSummaryOut]
    class_average_score: float


class StudentEngagementOverallOut(BaseModel):
    student_id: int
    samples: int
    overall_average_score: float


class StudentPerformanceOut(BaseModel):
    student_id: int
    quiz_average_percent: float
    engagement_average: float
    composite_score: float


class TeacherPerformanceOut(BaseModel):
    teacher_id: int
    quizzes_published: int
    student_submissions: int
    avg_student_quiz_percent: float
    avg_student_engagement: float
    performance_score: float


class InstitutionAnalyticsOut(BaseModel):
    total_students: int
    total_teachers: int
    total_meetings: int
    total_quizzes_published: int
    avg_quiz_percent: float
    avg_engagement: float
    institution_score: float
