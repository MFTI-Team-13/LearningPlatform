from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Dict, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import CourseProgress, LessonProgress, Course, Lesson, User, SessionLocal


class ProgressService:
    def __init__(self, db_session: Session = None):
        if db_session is None:
            self.db_session = SessionLocal()
        else:
            self.db_session = db_session

    def start_course(self, user_id: int, course_id: int) -> CourseProgress:
        try:
            existing = self.db_session.query(CourseProgress).filter_by(
                user_id=user_id,
                course_id=course_id
            ).first()

            if existing:
                return existing

            course_progress = CourseProgress(
                user_id=user_id,
                course_id=course_id,
                progress_percentage=0
            )

            self.db_session.add(course_progress)
            self.db_session.commit()

            # Получаем ВСЕ уроки курса из таблицы lessons
            lessons = self.db_session.query(Lesson).filter_by(course_id=course_id).all()

            # Создаем записи прогресса для каждого урока
            for lesson in lessons:
                lesson_progress = LessonProgress(
                    user_id=user_id,
                    lesson_id=lesson.id,
                    course_progress_id=course_progress.id
                )
                self.db_session.add(lesson_progress)

            self.db_session.commit()
            return course_progress

        except Exception as e:
            self.db_session.rollback()
            raise Exception(f"Ошибка при начале курса: {str(e)}")

    def complete_course(self, user_id: int, course_id: int) -> CourseProgress:
        try:
            course_progress = self.db_session.query(CourseProgress).filter_by(
                user_id=user_id,
                course_id=course_id
            ).first()

            if not course_progress:
                raise ValueError(f"Пользователь {user_id} не начал курс {course_id}")

            # Отмечаем все уроки курса как завершенные
            lessons = self.db_session.query(Lesson).filter_by(course_id=course_id).all()
            for lesson in lessons:
                # Находим или создаем прогресс для каждого урока
                lesson_progress = self.db_session.query(LessonProgress).filter_by(
                    user_id=user_id,
                    lesson_id=lesson.id,
                    course_progress_id=course_progress.id
                ).first()

                if not lesson_progress:
                    lesson_progress = LessonProgress(
                        user_id=user_id,
                        lesson_id=lesson.id,
                        course_progress_id=course_progress.id
                    )
                    self.db_session.add(lesson_progress)

                lesson_progress.completed = True
                lesson_progress.completed_at = datetime.now(timezone.utc)

            # Обновляем прогресс курса
            course_progress.progress_percentage = 100
            course_progress.completed_at = datetime.now(timezone.utc)

            self.db_session.commit()
            return course_progress

        except Exception as e:
            self.db_session.rollback()
            raise Exception(f"Ошибка при завершении курса: {str(e)}")

    def get_course_progress(self, user_id: int, course_id: int) -> Dict[str, Any]:
        course_progress = self.db_session.query(CourseProgress).filter_by(
            user_id=user_id,
            course_id=course_id
        ).first()

        if not course_progress:
            return None

        # Получаем ВСЕ уроки курса из таблицы lessons
        all_lessons = self.db_session.query(Lesson).filter_by(course_id=course_id).all()
        total_lessons = len(all_lessons)

        # Получаем завершенные уроки для этого пользователя
        completed_lessons_query = self.db_session.query(LessonProgress).filter_by(
            user_id=user_id,
            course_progress_id=course_progress.id,
            completed=True
        )
        completed_lessons = completed_lessons_query.count()

        # Рассчитываем процент прогресса
        if total_lessons > 0:
            new_percentage = int((completed_lessons / total_lessons) * 100)
        else:
            new_percentage = 0

        # Обновляем процент прогресса если изменился
        if new_percentage != course_progress.progress_percentage:
            course_progress.progress_percentage = new_percentage
            # Если прогресс 100%, отмечаем курс как завершенный
            if new_percentage == 100 and not course_progress.completed_at:
                course_progress.completed_at = datetime.now(timezone.utc)
            self.db_session.commit()

        course = self.db_session.get(Course, course_id)  # ИСПРАВЛЕНО

        return {
            'course_id': course_id,
            'course_title': course.title if course else 'Неизвестный курс',
            'started_at': course_progress.started_at,
            'completed_at': course_progress.completed_at,
            'progress_percentage': course_progress.progress_percentage,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'is_completed': course_progress.completed_at is not None
        }

    def get_user_courses_progress(self, user_id: int) -> List[Dict[str, Any]]:
        results = []

        course_progresses = self.db_session.query(CourseProgress).filter_by(
            user_id=user_id
        ).all()

        for cp in course_progresses:
            course_info = self.get_course_progress(user_id, cp.course_id)
            if course_info:
                results.append(course_info)

        return results

    def start_lesson(self, user_id: int, lesson_id: int) -> LessonProgress:
        try:
            lesson = self.db_session.get(Lesson, lesson_id)  # ИСПРАВЛЕНО
            if not lesson:
                raise ValueError(f"Урок {lesson_id} не найден")

            course_progress = self.db_session.query(CourseProgress).filter_by(
                user_id=user_id,
                course_id=lesson.course_id
            ).first()

            if not course_progress:
                course_progress = self.start_course(user_id, lesson.course_id)

            lesson_progress = self.db_session.query(LessonProgress).filter_by(
                user_id=user_id,
                lesson_id=lesson_id,
                course_progress_id=course_progress.id
            ).first()

            if not lesson_progress:
                lesson_progress = LessonProgress(
                    user_id=user_id,
                    lesson_id=lesson_id,
                    course_progress_id=course_progress.id
                )
                self.db_session.add(lesson_progress)
                self.db_session.commit()

            return lesson_progress

        except Exception as e:
            self.db_session.rollback()
            raise Exception(f"Ошибка при начале урока: {str(e)}")

    def complete_lesson(self, user_id: int, lesson_id: int) -> LessonProgress:
        try:
            lesson = self.db_session.get(Lesson, lesson_id)  # ИСПРАВЛЕНО
            if not lesson:
                raise ValueError(f"Урок {lesson_id} не найден")

            # Находим прогресс курса
            course_progress = self.db_session.query(CourseProgress).filter_by(
                user_id=user_id,
                course_id=lesson.course_id
            ).first()

            if not course_progress:
                course_progress = self.start_course(user_id, lesson.course_id)

            # Находим или создаем прогресс урока
            lesson_progress = self.db_session.query(LessonProgress).filter_by(
                user_id=user_id,
                lesson_id=lesson_id,
                course_progress_id=course_progress.id
            ).first()

            if not lesson_progress:
                lesson_progress = LessonProgress(
                    user_id=user_id,
                    lesson_id=lesson_id,
                    course_progress_id=course_progress.id
                )
                self.db_session.add(lesson_progress)

            lesson_progress.completed = True
            lesson_progress.completed_at = datetime.now(timezone.utc)

            self.db_session.commit()

            # Обновляем прогресс курса
            self._update_course_progress(course_progress.id)

            return lesson_progress

        except Exception as e:
            self.db_session.rollback()
            raise Exception(f"Ошибка при завершении урока: {str(e)}")

    def get_lesson_progress(self, user_id: int, lesson_id: int) -> Dict[str, Any]:
        lesson_progress = self.db_session.query(LessonProgress).filter_by(
            user_id=user_id,
            lesson_id=lesson_id
        ).first()

        if not lesson_progress:
            return None

        lesson = self.db_session.get(Lesson, lesson_id)  # ИСПРАВЛЕНО
        course = self.db_session.get(Course, lesson.course_id) if lesson else None  # ИСПРАВЛЕНО

        return {
            'lesson_id': lesson_id,
            'lesson_title': lesson.title if lesson else 'Неизвестный урок',
            'started_at': lesson_progress.started_at,
            'completed_at': lesson_progress.completed_at,
            'completed': lesson_progress.completed,
            'course_id': lesson.course_id if lesson else None,
            'course_title': course.title if course else 'Неизвестный курс'
        }

    def get_course_lessons_progress(self, user_id: int, course_id: int) -> List[Dict[str, Any]]:
        results = []

        # Получаем все уроки курса
        lessons = self.db_session.query(Lesson).filter_by(course_id=course_id).order_by(Lesson.order).all()

        # Находим прогресс курса
        course_progress = self.db_session.query(CourseProgress).filter_by(
            user_id=user_id,
            course_id=course_id
        ).first()

        for lesson in lessons:
            lesson_progress = None
            if course_progress:
                lesson_progress = self.db_session.query(LessonProgress).filter_by(
                    user_id=user_id,
                    lesson_id=lesson.id,
                    course_progress_id=course_progress.id
                ).first()

            if lesson_progress:
                results.append({
                    'lesson_id': lesson.id,
                    'lesson_title': lesson.title,
                    'started_at': lesson_progress.started_at,
                    'completed_at': lesson_progress.completed_at,
                    'completed': lesson_progress.completed,
                    'course_id': course_id
                })
            else:
                results.append({
                    'lesson_id': lesson.id,
                    'lesson_title': lesson.title,
                    'started_at': None,
                    'completed_at': None,
                    'completed': False,
                    'course_id': course_id
                })

        return results

    def _update_course_progress(self, course_progress_id: int):
        """Обновляет процент прогресса курса"""
        course_progress = self.db_session.get(CourseProgress, course_progress_id)  # ИСПРАВЛЕНО

        if not course_progress:
            return

        # Получаем все уроки курса
        total_lessons = self.db_session.query(Lesson).filter_by(course_id=course_progress.course_id).count()

        if total_lessons == 0:
            course_progress.progress_percentage = 0
            self.db_session.commit()
            return

        # Получаем завершенные уроки
        completed_lessons = self.db_session.query(LessonProgress).filter_by(
            course_progress_id=course_progress_id,
            completed=True
        ).count()

        # Рассчитываем процент
        new_percentage = int((completed_lessons / total_lessons) * 100)

        # Обновляем если изменилось
        if new_percentage != course_progress.progress_percentage:
            course_progress.progress_percentage = new_percentage

            # Если прогресс 100%, отмечаем курс как завершенный
            if new_percentage == 100 and not course_progress.completed_at:
                course_progress.completed_at = datetime.now(timezone.utc)

            self.db_session.commit()

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получает статистику пользователя"""
        # Получаем все курсы пользователя
        course_progresses = self.db_session.query(CourseProgress).filter_by(
            user_id=user_id
        ).all()

        total_courses = len(course_progresses)
        completed_courses = sum(1 for cp in course_progresses if cp.completed_at is not None)

        # Подсчитываем уроки
        total_lessons_completed = 0
        total_lessons_in_progress = 0

        for cp in course_progresses:
            # Завершенные уроки для этого курса
            completed = self.db_session.query(LessonProgress).filter_by(
                course_progress_id=cp.id,
                completed=True
            ).count()
            total_lessons_completed += completed

            # Всего уроков в курсе
            total_in_course = self.db_session.query(Lesson).filter_by(course_id=cp.course_id).count()
            total_lessons_in_progress += total_in_course

        # Рассчитываем средний прогресс
        avg_progress = 0
        if total_courses > 0:
            total_progress = sum(cp.progress_percentage for cp in course_progresses)
            avg_progress = total_progress / total_courses

        # Процент завершения
        completion_rate = 0
        if total_courses > 0:
            completion_rate = (completed_courses / total_courses) * 100

        return {
            'total_courses_started': total_courses,
            'total_courses_completed': completed_courses,
            'total_lessons_completed': total_lessons_completed,
            'total_lessons': total_lessons_in_progress,
            'average_progress': round(avg_progress, 1),
            'completion_rate': round(completion_rate, 1)
        }

    def reset_progress(self, user_id: int, course_id: int = None):
        try:
            if course_id:
                course_progress = self.db_session.query(CourseProgress).filter_by(
                    user_id=user_id,
                    course_id=course_id
                ).first()

                if course_progress:
                    # Удаляем прогрессы уроков
                    self.db_session.query(LessonProgress).filter_by(
                        course_progress_id=course_progress.id
                    ).delete()

                    # Удаляем прогресс курса
                    self.db_session.delete(course_progress)
            else:
                # Находим все прогрессы пользователя
                course_progresses = self.db_session.query(CourseProgress).filter_by(
                    user_id=user_id
                ).all()

                for cp in course_progresses:
                    # Удаляем прогрессы уроков
                    self.db_session.query(LessonProgress).filter_by(
                        course_progress_id=cp.id
                    ).delete()

                    # Удаляем прогресс курса
                    self.db_session.delete(cp)

            self.db_session.commit()

        except Exception as e:
            self.db_session.rollback()
            raise Exception(f"Ошибка при сбросе прогресса: {str(e)}")

    def close(self):
        self.db_session.close()