"""
reset_db.py - Полная очистка базы данных
"""

from models import engine, Base, SessionLocal
import os


def reset_database():
    """Полностью удаляет и создает заново базу данных"""
    print("ПОЛНАЯ ОЧИСТКА БАЗЫ ДАННЫХ")

    # Закрываем все соединения
    if os.path.exists("education_platform.db"):
        os.remove("education_platform.db")
        print("Старая база данных удалена")

    # Создаем новую базу
    Base.metadata.create_all(engine)

    session = SessionLocal()
    try:
        # Проверяем, что таблицы пустые
        from models import User, Course, Lesson, CourseProgress, LessonProgress

        user_count = session.query(User).count()
        course_count = session.query(Course).count()
        lesson_count = session.query(Lesson).count()
        course_progress_count = session.query(CourseProgress).count()
        lesson_progress_count = session.query(LessonProgress).count()

        print(f"База данных создана заново")
        print(f"Таблицы: 5 шт (users, courses, lessons, course_progress, lesson_progress)")
        print(f"Записей: users={user_count}, courses={course_count}, lessons={lesson_count}")
        print(f"         course_progress={course_progress_count}, lesson_progress={lesson_progress_count}")

    finally:
        session.close()


if __name__ == "__main__":
    reset_database()