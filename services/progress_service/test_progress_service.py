import unittest
from sqlalchemy import create_engine
from models import Base, User, Course, Lesson, SessionLocal
from services.progress_service import ProgressService


class TestProgressService(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)

        Session = SessionLocal
        self.session = Session(bind=self.engine)

        self.create_test_data()

        self.progress_service = ProgressService(self.session)

    def create_test_data(self):
        user = User(username="test_user", email="test@example.com")
        self.session.add(user)

        course = Course(title="Тестовый курс", description="Описание курса")
        self.session.add(course)
        self.session.flush()

        # Создаем 3 урока
        for i in range(1, 4):
            lesson = Lesson(
                course_id=course.id,
                title=f"Урок {i}",
                content=f"Содержание урока {i}",
                order=i
            )
            self.session.add(lesson)

        self.session.commit()
        self.user_id = user.id
        self.course_id = course.id

    def test_start_course(self):
        print("Тест: начало курса")
        progress = self.progress_service.start_course(self.user_id, self.course_id)
        self.assertIsNotNone(progress)
        self.assertEqual(progress.user_id, self.user_id)
        self.assertEqual(progress.course_id, self.course_id)
        self.assertEqual(progress.progress_percentage, 0)
        print("Тест пройден")

    def test_complete_lesson(self):
        print("Тест: завершение урока")
        self.progress_service.start_course(self.user_id, self.course_id)

        lesson_progress = self.progress_service.complete_lesson(self.user_id, 1)
        self.assertTrue(lesson_progress.completed)
        self.assertIsNotNone(lesson_progress.completed_at)
        print("Тест пройден")

    def test_get_course_progress(self):
        print("Тест: получение прогресса курса")
        self.progress_service.start_course(self.user_id, self.course_id)
        self.progress_service.complete_lesson(self.user_id, 1)

        progress = self.progress_service.get_course_progress(self.user_id, self.course_id)
        self.assertIsNotNone(progress)
        self.assertEqual(progress['progress_percentage'], 33)
        print("Тест пройден")

    def test_get_user_stats(self):
        print("Тест: статистика пользователя")
        self.progress_service.start_course(self.user_id, self.course_id)
        self.progress_service.complete_lesson(self.user_id, 1)
        self.progress_service.complete_lesson(self.user_id, 2)

        stats = self.progress_service.get_user_stats(self.user_id)
        self.assertIsNotNone(stats)
        self.assertEqual(stats['total_courses_started'], 1)
        self.assertEqual(stats['total_lessons_completed'], 2)
        print("Тест пройден")

    def tearDown(self):
        self.session.close()
        self.progress_service.close()


def run_tests():
    print("Запуск тестов ProgressService...")
    print("=" * 50)

    suite = unittest.TestLoader().loadTestsFromTestCase(TestProgressService)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("=" * 50)
    if result.wasSuccessful():
        print("Все тесты пройдены успешно!")
    else:
        print(f"Тестов провалено: {len(result.failures) + len(result.errors)}")

    return result


if __name__ == "__main__":
    run_tests()