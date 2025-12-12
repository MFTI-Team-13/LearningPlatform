from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime, timezone

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    course_progresses = relationship("CourseProgress", back_populates="user")
    lesson_progresses = relationship("LessonProgress", back_populates="user")


class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    lessons = relationship("Lesson", back_populates="course")
    progresses = relationship("CourseProgress", back_populates="course")


class Lesson(Base):
    __tablename__ = 'lessons'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    title = Column(String(100), nullable=False)
    content = Column(Text)
    order = Column(Integer, default=0)

    course = relationship("Course", back_populates="lessons")
    progresses = relationship("LessonProgress", back_populates="lesson")


class CourseProgress(Base):
    __tablename__ = 'course_progress'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    progress_percentage = Column(Integer, default=0)

    user = relationship("User", back_populates="course_progresses")
    course = relationship("Course", back_populates="progresses")
    lesson_progresses = relationship("LessonProgress", back_populates="course_progress")


class LessonProgress(Base):
    __tablename__ = 'lesson_progress'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    lesson_id = Column(Integer, ForeignKey('lessons.id'), nullable=False)
    course_progress_id = Column(Integer, ForeignKey('course_progress.id'), nullable=False)
    completed = Column(Boolean, default=False)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="lesson_progresses")
    lesson = relationship("Lesson", back_populates="progresses")
    course_progress = relationship("CourseProgress", back_populates="lesson_progresses")


engine = create_engine('sqlite:///education_platform.db')
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)

print("База данных инициализирована.")
print("Созданы таблицы:")
for table in Base.metadata.tables:
    print(f"  {table}")