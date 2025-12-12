"""
main.py - Демонстрация работы ProgressService (исправленная)
"""

from models import SessionLocal, User, Course, Lesson, CourseProgress, LessonProgress
from services.progress_service import ProgressService

def check_database_state():
    """Проверяет состояние базы данных перед началом"""
    session = SessionLocal()
    try:
        print("ТЕКУЩЕЕ СОСТОЯНИЕ БАЗЫ ДАННЫХ:")
        print(f"  Пользователей: {session.query(User).count()}")
        print(f"  Курсов: {session.query(Course).count()}")
        print(f"  Уроков: {session.query(Lesson).count()}")
        print(f"  Записей прогресса курсов: {session.query(CourseProgress).count()}")
        print(f"  Записей прогресса уроков: {session.query(LessonProgress).count()}")

        # Выводим детали
        if session.query(LessonProgress).count() > 0:
            print("\n  ЗАПИСИ PROGRESS В БАЗЕ:")
            records = session.query(LessonProgress).all()
            for r in records:
                print(f"    ID: {r.id}, User: {r.user_id}, Lesson: {r.lesson_id}, Completed: {r.completed}")

    finally:
        session.close()

def create_test_data():
    """Создает чистые тестовые данные"""
    print("\nСОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ")

    session = SessionLocal()

    try:
        # Убедимся, что база чистая
        session.query(LessonProgress).delete()
        session.query(CourseProgress).delete()
        session.query(Lesson).delete()
        session.query(Course).delete()
        session.query(User).delete()
        session.commit()

        # Создаем пользователя
        user = User(username="student1", email="student1@example.com")
        session.add(user)

        # Создаем курс Python
        python_course = Course(
            title="Python для начинающих",
            description="Изучение основ языка Python"
        )
        session.add(python_course)
        session.commit()

        # Создаем ровно 3 урока для курса Python
        python_lesson1 = Lesson(
            course_id=python_course.id,
            title="Введение в Python",
            content="Основы синтаксиса",
            order=1
        )
        session.add(python_lesson1)

        python_lesson2 = Lesson(
            course_id=python_course.id,
            title="Переменные и типы данных",
            content="Работа с переменными",
            order=2
        )
        session.add(python_lesson2)

        python_lesson3 = Lesson(
            course_id=python_course.id,
            title="Условные операторы",
            content="If/else конструкции",
            order=3
        )
        session.add(python_lesson3)

        session.commit()

        print(f"Пользователь создан: {user.username} (ID: {user.id})")
        print(f"Курс создан: {python_course.title} (ID: {python_course.id})")
        print(f"Уроков создано: 3 (ID: {python_lesson1.id}, {python_lesson2.id}, {python_lesson3.id})")

        # Проверяем, сколько уроков в базе для этого курса
        lesson_count = session.query(Lesson).filter_by(course_id=python_course.id).count()
        print(f"Проверка: в базе {lesson_count} уроков для курса {python_course.title}")

        return user.id, python_course.id

    except Exception as e:
        session.rollback()
        print(f"Ошибка при создании данных: {e}")
        raise
    finally:
        session.close()

def main():
    print("=" * 60)
    print("ДЕМОНСТРАЦИЯ PROGRESS SERVICE (ЧИСТАЯ БАЗА)")
    print("=" * 60)

    # Проверяем состояние базы
    check_database_state()

    # Создаем чистые тестовые данные
    user_id, course_id = create_test_data()

    # Проверяем состояние после создания данных
    check_database_state()

    # Создаем сервис прогресса
    progress_service = ProgressService()

    try:
        print("\n1. НАЧИНАЕМ КУРС (ПЕРВЫЙ РАЗ)")
        print("-" * 40)

        # Проверяем, нет ли уже прогресса
        session = SessionLocal()
        existing_progress = session.query(CourseProgress).filter_by(
            user_id=user_id,
            course_id=course_id
        ).first()
        session.close()

        if existing_progress:
            print(f"ВНИМАНИЕ: Прогресс курса уже существует (ID: {existing_progress.id})")
            print(f"Начинаем с существующего прогресса...")
            course_progress = existing_progress
        else:
            course_progress = progress_service.start_course(user_id, course_id)
            print(f"Курс начат впервые")

        print(f"ID записи прогресса: {course_progress.id}")
        print(f"Начальный прогресс: {course_progress.progress_percentage}%")

        # Проверяем состояние базы после начала курса
        session = SessionLocal()
        lesson_progress_count = session.query(LessonProgress).filter_by(
            course_progress_id=course_progress.id
        ).count()
        session.close()

        print(f"Создано записей прогресса уроков: {lesson_progress_count}")

        print("\n2. ПРОВЕРКА НАЧАЛЬНОГО ПРОГРЕССА")
        print("-" * 40)

        progress = progress_service.get_course_progress(user_id, course_id)
        print(f"Прогресс курса: {progress['progress_percentage']}%")
        print(f"Уроков завершено: {progress['completed_lessons']}/{progress['total_lessons']}")

        if progress['progress_percentage'] != 0:
            print(f"ВНИМАНИЕ: Начальный прогресс должен быть 0%, а не {progress['progress_percentage']}%")

        print("\n3. ПОЛУЧАЕМ СПИСОК УРОКОВ КУРСА")
        print("-" * 40)

        session = SessionLocal()
        lessons = session.query(Lesson).filter_by(course_id=course_id).order_by(Lesson.order).all()
        session.close()

        print(f"Уроки курса '{progress['course_title']}':")
        for i, lesson in enumerate(lessons, 1):
            print(f"  {i}. {lesson.title} (ID: {lesson.id})")

        lesson_ids = [lesson.id for lesson in lessons]

        print("\n4. ЗАВЕРШАЕМ УРОКИ ПО ОДНОМУ")
        print("-" * 40)

        for i, lesson_id in enumerate(lesson_ids, 1):
            print(f"\nЗавершаем урок {i} (ID: {lesson_id})...")

            # Проверяем состояние перед завершением
            session = SessionLocal()
            before_count = session.query(LessonProgress).filter_by(
                user_id=user_id,
                lesson_id=lesson_id,
                completed=True
            ).count()
            session.close()

            print(f"  До: завершенных записей для этого урока: {before_count}")

            # Завершаем урок
            lesson_progress = progress_service.complete_lesson(user_id, lesson_id)

            # Проверяем состояние после завершения
            session = SessionLocal()
            after_count = session.query(LessonProgress).filter_by(
                user_id=user_id,
                lesson_id=lesson_id,
                completed=True
            ).count()
            session.close()

            print(f"  После: завершенных записей для этого урока: {after_count}")

            current_progress = progress_service.get_course_progress(user_id, course_id)
            expected_percentage = int((i / len(lesson_ids)) * 100)
            print(f"  Прогресс: {current_progress['progress_percentage']}% (ожидается: {expected_percentage}%)")

        print("\n5. ФИНАЛЬНАЯ ПРОВЕРКА КУРСА PYTHON")
        print("-" * 40)

        final = progress_service.get_course_progress(user_id, course_id)
        print(f"Финальный прогресс: {final['progress_percentage']}%")
        print(f"Уроков завершено: {final['completed_lessons']}/{final['total_lessons']}")
        print(f"Курс завершен: {'ДА' if final['is_completed'] else 'НЕТ'}")

        if final['progress_percentage'] > 100:
            print(f"ОШИБКА: Прогресс превышает 100%!")

        print("\n6. СТАТИСТИКА ПОСЛЕ ПЕРВОГО КУРСА")
        print("-" * 40)

        stats = progress_service.get_user_stats(user_id)
        print(f"Курсов начато: {stats['total_courses_started']} (ожидается: 1)")
        print(f"Курсов завершено: {stats['total_courses_completed']} (ожидается: 1)")
        print(f"Уроков завершено: {stats['total_lessons_completed']} (ожидается: {len(lesson_ids)})")
        print(f"Всего уроков: {stats['total_lessons']} (ожидается: {len(lesson_ids)})")
        print(f"Средний прогресс: {stats['average_progress']}% (ожидается: 100%)")
        print(f"Процент завершения: {stats['completion_rate']}% (ожидается: 100%)")

        print("\n7. СОЗДАНИЕ И ЗАВЕРШЕНИЕ ВТОРОГО КУРСА")
        print("-" * 40)

        # Создаем второй курс в отдельной сессии
        session = SessionLocal()
        try:
            sql_course = Course(
                title="Основы SQL",
                description="Изучение баз данных"
            )
            session.add(sql_course)
            session.commit()

            sql_lesson = Lesson(
                course_id=sql_course.id,
                title="Введение в SQL",
                content="Основные команды SQL",
                order=1
            )
            session.add(sql_lesson)
            session.commit()

            sql_course_id = sql_course.id
            sql_course_title = sql_course.title

            print(f"Создан второй курс: {sql_course_title} (ID: {sql_course_id})")
            print(f"Создан урок: Введение в SQL (ID: {sql_lesson.id})")

        finally:
            session.close()

        # Завершаем второй курс через метод complete_course
        progress_service.start_course(user_id, sql_course_id)
        completed = progress_service.complete_course(user_id, sql_course_id)
        print(f"Курс SQL завершен: {completed.completed_at}")

        sql_progress = progress_service.get_course_progress(user_id, sql_course_id)
        print(f"Прогресс курса SQL: {sql_progress['progress_percentage']}%")

        print("\n8. ФИНАЛЬНАЯ СТАТИСТИКА (2 КУРСА)")
        print("-" * 40)

        final_stats = progress_service.get_user_stats(user_id)
        print(f"Курсов начато: {final_stats['total_courses_started']} (ожидается: 2)")
        print(f"Курсов завершено: {final_stats['total_courses_completed']} (ожидается: 2)")
        print(f"Уроков завершено: {final_stats['total_lessons_completed']} (ожидается: {len(lesson_ids) + 1})")
        print(f"Всего уроков: {final_stats['total_lessons']} (ожидается: {len(lesson_ids) + 1})")
        print(f"Средний прогресс: {final_stats['average_progress']}% (ожидается: 100%)")
        print(f"Процент завершения: {final_stats['completion_rate']}% (ожидается: 100%)")

        print("\n9. ПРОВЕРКА ВСЕХ КУРСОВ ПОЛЬЗОВАТЕЛЯ")
        print("-" * 40)

        all_courses = progress_service.get_user_courses_progress(user_id)
        print(f"Всего курсов у пользователя: {len(all_courses)}")

        for course in all_courses:
            status = "Завершен" if course['is_completed'] else "В процессе"
            progress_text = f"{course['progress_percentage']}%"
            if course['progress_percentage'] > 100:
                progress_text = f"{course['progress_percentage']}% (ОШИБКА!)"
            print(f"  Курс: {course['course_title']} - {progress_text} ({status})")

        print("\n" + "=" * 60)
        print("ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
        print("=" * 60)

        # Финальная проверка базы
        check_database_state()

    except Exception as e:
        print(f"\nОШИБКА: {e}")
        import traceback
        traceback.print_exc()

    finally:
        progress_service.close()

if __name__ == "__main__":
    main()