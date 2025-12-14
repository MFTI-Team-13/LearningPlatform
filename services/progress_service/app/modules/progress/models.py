from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.common.db.base import Base


class CoursesProgress(Base):
    __tablename__ = 'courses_progress'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    course_id = Column(Integer, nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    progress_percentage = Column(Integer, default=0)

    #user = relationship("User", back_populates="course_progresses")
    #course = relationship("Course", back_populates="progresses")
    #lesson_progresses = relationship("LessonProgress", back_populates="course_progress")


class LessonsProgress(Base):
    __tablename__ = 'lessons_progress'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    lesson_id = Column(Integer, nullable=False)
    course_progress_id = Column(Integer, ForeignKey('courses_progress.id'), nullable=False)
    completed = Column(Boolean, default=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    #user = relationship("User", back_populates="lesson_progresses")
    #lesson = relationship("Lesson", back_populates="progresses")
    #course_progress = relationship("CourseProgress", back_populates="lesson_progresses")
