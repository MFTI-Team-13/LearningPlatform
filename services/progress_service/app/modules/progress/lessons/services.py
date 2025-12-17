from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.progress.courses.services import CourseProgressService
from app.modules.progress.lessons.models import LessonProgress
from app.modules.progress.lessons.schemas import (
  LessonProgressCreate,
  LessonProgressUpdate,
  LessonStats,
  UserLessonsSummary,
  PaginatedLessonProgress,
  LessonAnswerSubmit,
  LessonContentProgress,
)

if TYPE_CHECKING:
  from collections.abc import Sequence


class LessonProgressService:
  """Сервис для работы с прогрессом уроков"""

  @staticmethod
  async def get_by_id(db: AsyncSession, progress_id: int) -> Optional[LessonProgress]:
    """Получение прогресса по ID"""
    stmt = select(LessonProgress).where(LessonProgress.id == progress_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

  @staticmethod
  async def get_by_user_and_lesson(
    db: AsyncSession,
    user_id: int,
    course_id: int,
    lesson_id: int
  ) -> Optional[LessonProgress]:
    """Получение прогресса пользователя по уроку"""
    stmt = select(LessonProgress).where(
      and_(
        LessonProgress.user_id == user_id,
        LessonProgress.course_id == course_id,
        LessonProgress.lesson_id == lesson_id
      )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

  @staticmethod
  async def create(
    db: AsyncSession,
    lesson_data: LessonProgressCreate
  ) -> LessonProgress:
    """Создание записи о прогрессе урока"""
    # Если не указан course_progress_id, находим или создаем прогресс курса
    if not lesson_data.course_progress_id:
      course_progress = await CourseProgressService.get_by_user_and_course(
        db, lesson_data.user_id, lesson_data.course_id
      )

      if not course_progress:
        from app.modules.progress.courses.schemas import CourseProgressCreate
        course_progress_data = CourseProgressCreate(
          user_id=lesson_data.user_id,
          course_id=lesson_data.course_id
        )
        course_progress = await CourseProgressService.create(db, course_progress_data)

      lesson_data.course_progress_id = course_progress.id

    # Проверяем существующий прогресс
    existing = await LessonProgressService.get_by_user_and_lesson(
      db, lesson_data.user_id, lesson_data.course_id, lesson_data.lesson_id
    )

    if existing:
      return existing

    # Создаем новую запись
    db_lesson = LessonProgress(**lesson_data.model_dump())
    db.add(db_lesson)
    await db.commit()
    await db.refresh(db_lesson)

    # Обновляем статистику курса
    await LessonProgressService._update_course_stats(db, lesson_data.course_progress_id)

    return db_lesson

  @staticmethod
  async def _update_course_stats(db: AsyncSession, course_progress_id: int) -> None:
    """Обновление статистики курса после изменений в уроках"""
    try:
      # Получаем прогресс курса
      from app.modules.progress.courses.models import CourseProgress

      stmt = select(CourseProgress).where(CourseProgress.id == course_progress_id)
      result = await db.execute(stmt)
      course_progress = result.scalar_one_or_none()

      if not course_progress:
        return

      # Получаем все уроки этого курса
      stmt = select(LessonProgress).where(
        LessonProgress.course_progress_id == course_progress_id
      )
      result = await db.execute(stmt)
      lessons = result.scalars().all()

      if not lessons:
        return

      # Подсчитываем статистику
      completed_lessons = sum(1 for l in lessons if l.is_completed)
      total_lessons = len(lessons)
      total_score = sum(l.score for l in lessons if l.score is not None)
      total_time = sum(l.time_spent_seconds for l in lessons)

      # Обновляем поля курса
      course_progress.completed_lessons = completed_lessons
      course_progress.time_spent_seconds = total_time
      course_progress.total_score = total_score

      # Пересчитываем средний балл
      if completed_lessons > 0:
        course_progress.average_score = total_score / completed_lessons

      # Пересчитываем процент выполнения
      course_progress.update_progress()

      await db.commit()

    except Exception:
      await db.rollback()
      raise

  @staticmethod
  async def update(
    db: AsyncSession,
    user_id: int,
    course_id: int,
    lesson_id: int,
    update_data: LessonProgressUpdate
  ) -> Optional[LessonProgress]:
    """Обновление прогресса урока"""
    lesson = await LessonProgressService.get_by_user_and_lesson(
      db, user_id, course_id, lesson_id
    )

    if not lesson:
      return None

    update_dict = update_data.model_dump(exclude_unset=True)

    # Обновляем поля
    for field, value in update_dict.items():
      setattr(lesson, field, value)

    # Обновляем время последнего доступа
    lesson.last_accessed_at = datetime.utcnow()

    # Проверяем, пройден ли урок
    if lesson.score is not None and lesson.passing_score is not None:
      lesson.is_passed = lesson.score >= lesson.passing_score

    await db.commit()
    await db.refresh(lesson)

    # Обновляем статистику курса
    await LessonProgressService._update_course_stats(db, lesson.course_progress_id)

    return lesson

  @staticmethod
  async def delete(
    db: AsyncSession,
    user_id: int,
    course_id: int,
    lesson_id: int
  ) -> bool:
    """Удаление прогресса урока"""
    lesson = await LessonProgressService.get_by_user_and_lesson(
      db, user_id, course_id, lesson_id
    )

    if not lesson:
      return False

    course_progress_id = lesson.course_progress_id

    await db.delete(lesson)
    await db.commit()

    # Обновляем статистику курса
    await LessonProgressService._update_course_stats(db, course_progress_id)

    return True

  @staticmethod
  async def get_user_lessons(
    db: AsyncSession,
    user_id: int,
    course_id: Optional[int] = None,
    is_completed: Optional[bool] = None,
    is_passed: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100
  ) -> PaginatedLessonProgress:
    """Получение всех уроков пользователя с фильтрацией"""
    stmt = select(LessonProgress).where(LessonProgress.user_id == user_id)

    # Применяем фильтры
    if course_id:
      stmt = stmt.where(LessonProgress.course_id == course_id)

    if is_completed is not None:
      stmt = stmt.where(LessonProgress.is_completed == is_completed)

    if is_passed is not None:
      stmt = stmt.where(LessonProgress.is_passed == is_passed)

    # Считаем общее количество
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Получаем данные с пагинацией
    stmt = stmt.order_by(
      LessonProgress.lesson_number,
      desc(LessonProgress.updated_at)
    ).offset(skip).limit(limit)

    result = await db.execute(stmt)
    items = result.scalars().all()

    # Рассчитываем количество страниц
    pages = (total + limit - 1) // limit if limit > 0 else 1

    return PaginatedLessonProgress(
      items=items,
      total=total,
      page=skip // limit + 1 if limit > 0 else 1,
      size=limit,
      pages=pages
    )

  @staticmethod
  async def get_lesson_stats(
    db: AsyncSession,
    lesson_id: int
  ) -> LessonStats:
    """Получение статистики по уроку"""
    # Все записи прогресса для урока
    stmt = select(LessonProgress).where(LessonProgress.lesson_id == lesson_id)
    result = await db.execute(stmt)
    progresses = result.scalars().all()

    if not progresses:
      # Получаем номер урока из первой записи (если есть)
      lesson_number = progresses[0].lesson_number if progresses else 0
      return LessonStats(lesson_id=lesson_id, lesson_number=lesson_number)

    total_users = len(progresses)
    lesson_number = progresses[0].lesson_number

    # Считаем статистику
    started_users = sum(1 for p in progresses if p.is_started)
    completed_users = sum(1 for p in progresses if p.is_completed)
    passed_users = sum(1 for p in progresses if p.is_passed)

    avg_progress = sum(p.progress_percentage for p in progresses) / total_users

    # Фильтруем оценки
    scores = [p.score for p in progresses if p.score is not None]
    avg_score = sum(scores) / len(scores) if scores else None

    # Время и попытки
    total_time = sum(p.time_spent_seconds for p in progresses)
    avg_time = total_time // total_users if total_users > 0 else 0

    total_attempts = sum(p.attempts for p in progresses)
    avg_attempts = total_attempts / total_users if total_users > 0 else 0

    # Проценты
    completion_rate = (completed_users / total_users) * 100 if total_users > 0 else 0
    pass_rate = (passed_users / completed_users) * 100 if completed_users > 0 else 0

    # Индекс сложности
    difficulty_index = None
    if completed_users > 0:
      difficulty_index = 1 - (passed_users / completed_users)

    # Анализ частых ошибок (упрощенная версия)
    common_mistakes = []

    return LessonStats(
      lesson_id=lesson_id,
      lesson_number=lesson_number,
      total_users=total_users,
      started_users=started_users,
      completed_users=completed_users,
      passed_users=passed_users,
      avg_progress=avg_progress,
      avg_score=avg_score,
      avg_time_spent=avg_time,
      avg_attempts=avg_attempts,
      completion_rate=completion_rate,
      pass_rate=pass_rate,
      difficulty_index=difficulty_index,
      common_mistakes=common_mistakes
    )

  @staticmethod
  async def get_user_summary(
    db: AsyncSession,
    user_id: int,
    course_id: Optional[int] = None
  ) -> UserLessonsSummary:
    """Получение сводки по урокам пользователя"""
    stmt = select(LessonProgress).where(LessonProgress.user_id == user_id)

    if course_id:
      stmt = stmt.where(LessonProgress.course_id == course_id)

    result = await db.execute(stmt)
    lessons = result.scalars().all()

    if not lessons:
      return UserLessonsSummary(user_id=user_id)

    # Основная статистика
    total_lessons = len(lessons)
    started_lessons = sum(1 for l in lessons if l.is_started)
    completed_lessons = sum(1 for l in lessons if l.is_completed)
    passed_lessons = sum(1 for l in lessons if l.is_passed)

    # Время и оценки
    total_time = sum(l.time_spent_seconds for l in lessons)
    avg_progress = sum(l.progress_percentage for l in lessons) / total_lessons
    total_attempts = sum(l.attempts for l in lessons)

    # Средняя оценка
    scores = [l.score for l in lessons if l.score is not None]
    avg_score = sum(scores) / len(scores) if scores else None

    # Последняя активность
    last_activity = max(l.updated_at for l in lessons) if lessons else None

    # Текущий урок
    current_lesson = None
    for lesson in sorted(lessons, key=lambda x: x.updated_at, reverse=True):
      if lesson.is_started and not lesson.is_completed:
        current_lesson = {
          "lesson_id": lesson.lesson_id,
          "course_id": lesson.course_id,
          "lesson_number": lesson.lesson_number,
          "progress_percentage": lesson.progress_percentage,
          "last_accessed": lesson.last_accessed_at
        }
        break

    # Недавние уроки
    recent_lessons = []
    for lesson in sorted(lessons, key=lambda x: x.updated_at, reverse=True)[:5]:
      recent_lessons.append({
        "lesson_id": lesson.lesson_id,
        "course_id": lesson.course_id,
        "lesson_number": lesson.lesson_number,
        "is_completed": lesson.is_completed,
        "is_passed": lesson.is_passed,
        "score": lesson.score,
        "updated_at": lesson.updated_at
      })

    return UserLessonsSummary(
      user_id=user_id,
      total_lessons=total_lessons,
      started_lessons=started_lessons,
      completed_lessons=completed_lessons,
      passed_lessons=passed_lessons,
      total_time_spent=total_time,
      average_progress=avg_progress,
      average_score=avg_score,
      total_attempts=total_attempts,
      last_activity=last_activity,
      current_lesson=current_lesson,
      recent_lessons=recent_lessons
    )

  @staticmethod
  async def submit_answers(
    db: AsyncSession,
    user_id: int,
    course_id: int,
    lesson_id: int,
    answer_data: LessonAnswerSubmit
  ) -> Optional[LessonProgress]:
    """Отправка ответов на урок"""
    lesson = await LessonProgressService.get_by_user_and_lesson(
      db, user_id, course_id, lesson_id
    )

    if not lesson:
      return None

    # Обновляем ответы
    lesson.answers = answer_data.answers
    lesson.attempts += 1

    # Добавляем время, если указано
    if answer_data.time_spent:
      lesson.time_spent_seconds += answer_data.time_spent

    lesson.last_accessed_at = datetime.utcnow()

    # TODO: Здесь должна быть логика оценки ответов
    # Пока устанавливаем фиктивную оценку
    lesson.score = 85.0
    lesson.is_passed = lesson.score >= lesson.passing_score

    await db.commit()
    await db.refresh(lesson)

    # Обновляем статистику курса
    await LessonProgressService._update_course_stats(db, lesson.course_progress_id)

    return lesson

  @staticmethod
  async def update_content_progress(
    db: AsyncSession,
    user_id: int,
    course_id: int,
    lesson_id: int,
    content_progress: list[LessonContentProgress]
  ) -> Optional[LessonProgress]:
    """Обновление прогресса по контенту урока"""
    lesson = await LessonProgressService.get_by_user_and_lesson(
      db, user_id, course_id, lesson_id
    )

    if not lesson:
      return None

    # Инициализируем content_progress, если его нет
    if lesson.content_progress is None:
      lesson.content_progress = {}

    # Обновляем прогресс по разделам
    for item in content_progress:
      lesson.content_progress[item.section_id] = {
        "progress": item.progress,
        "completed": item.completed,
        "updated_at": datetime.utcnow().isoformat()
      }

    # Пересчитываем общий прогресс урока
    if lesson.content_progress:
      total_progress = sum(
        section["progress"] for section in lesson.content_progress.values()
      )
      lesson.progress_percentage = total_progress / len(lesson.content_progress)

      # Если все разделы завершены, отмечаем урок как завершенный
      all_completed = all(
        section.get("completed", False)
        for section in lesson.content_progress.values()
      )
      if all_completed and not lesson.is_completed:
        lesson.is_completed = True
        lesson.completed_at = datetime.utcnow()

    lesson.last_accessed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(lesson)

    # Обновляем статистику курса
    await LessonProgressService._update_course_stats(db, lesson.course_progress_id)

    return lesson
