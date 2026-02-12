from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    full_name = Column(String(120), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, index=True)  # admin, teacher, student
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), unique=True, nullable=False)


class AcademicYear(Base):
    __tablename__ = "academic_years"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)


class Section(Base):
    __tablename__ = "sections"
    __table_args__ = (UniqueConstraint("department_id", "name", name="uq_department_section"),)

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

    department = relationship("Department")


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("department_id", "name", name="uq_department_subject"),)

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)

    department = relationship("Department")


class TeacherSubjectAssignment(Base):
    __tablename__ = "teacher_subject_assignments"
    __table_args__ = (UniqueConstraint("teacher_id", "subject_id", name="uq_teacher_subject"),)

    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)

    teacher = relationship("User")
    subject = relationship("Subject")


class StudentEnrollment(Base):
    __tablename__ = "student_enrollments"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "department_id",
            "section_id",
            "academic_year_id",
            name="uq_student_enrollment",
        ),
    )

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=False)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False)

    student = relationship("User")
    department = relationship("Department")
    section = relationship("Section")
    academic_year = relationship("AcademicYear")


class CaptionSegment(Base):
    __tablename__ = "caption_segments"

    id = Column(Integer, primary_key=True)
    meeting_id = Column(String(64), index=True, nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_second = Column(Integer, nullable=False)
    end_second = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    teacher = relationship("User")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True)
    meeting_id = Column(String(64), index=True, nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    status = Column(String(20), default="draft", nullable=False)  # draft/published
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    teacher = relationship("User")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    option_a = Column(String(255), nullable=False)
    option_b = Column(String(255), nullable=False)
    option_c = Column(String(255), nullable=False)
    option_d = Column(String(255), nullable=False)
    correct_option = Column(String(1), nullable=False)


class QuizSubmission(Base):
    __tablename__ = "quiz_submissions"
    __table_args__ = (UniqueConstraint("quiz_id", "student_id", name="uq_quiz_student_submission"),)

    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())


class EngagementSample(Base):
    __tablename__ = "engagement_samples"

    id = Column(Integer, primary_key=True)
    meeting_id = Column(String(64), index=True, nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    captured_second = Column(Integer, nullable=False)
    engagement_score = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("User")
