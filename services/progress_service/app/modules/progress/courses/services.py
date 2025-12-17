from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.progress.courses.models import CourseProgress, CourseProgressStatus
from app.modules.progress.courses.schemas import (
  CourseProgressCreate,
  CourseProgressUpdate,
  CourseStats,
  UserCoursesSummary,
  PaginatedCourseProgress,
  BulkCourseProgressUpdate,
  BulkCourseProgressResponse,
)

if TYPE_CHECKING:
  from collections.abc import Sequence


class CourseProgressService:
  """Сервис для работы с прогрессом курсов"""

  @staticmethod
  async def get_by_id(db: AsyncSession, progress_id: int) -> Optional[CourseProgress]:
    """Получение прогресса по ID"""
    stmt = select(CourseProgress).where(CourseProgress.id == progress_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

  @staticmethod
  async def get_by_user_and_course(
    db: AsyncSession,
    user_id: int,
    course_id: int
  ) -> Optional[CourseProgress]:
    """Получение прогресса пользователя по курсу"""
    stmt = select(CourseProgress).where(
      and_(
        CourseProgress.user_id == user_id,
        CourseProgress.course_id == course_id
      )
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

  @staticmethod
  async def create(
    db: AsyncSession,
    progress_data: CourseProgressCreate
  ) -> CourseProgress:
    """Создание записи о прогрессе курса"""
    # Проверяем существующий прогресс
    existing = await CourseProgressService.get_by_user_and_course(
      db, progress_data.user_id, progress_data.course_id
    )

    if existing:
      return existing

    # Создаем новую запись
    db_progress = CourseProgress(**progress_data.model_dump())
    db.add(db_progress)
    await db.commit()
    await db.refresh(db_progress)
    return db_progress

  @staticmethod
  async def update(
    db: AsyncSession,
    user_id: int,
    course_id: int,
    update_data: CourseProgressUpdate
  ) -> Optional[CourseProgress]:
    """Обновление прогресса курса"""
    progress = await CourseProgressService.get_by_user_and_course(db, user_id, course_id)
    if not progress:
      return None

    update_dict = update_data.model_dump(exclude_unset=True)

    # Обновляем поля
    for field, value in update_dict.items():
      setattr(progress, field, value)

    # Обновляем прогресс
    progress.update_progress()

    await db.commit()
    await db.refresh(progress)
    return progress

  @staticmethod
  async def delete(
    db: AsyncSession,
    user_id: int,
    course_id: int
  ) -> bool:
    """Удаление прогресса курса"""
    progress = await CourseProgressService.get_by_user_and_course(db, user_id, course_id)
    if not progress:
      return False

    await db.delete(progress)
    await db.commit()
    return True

  @staticmethod
  async def get_user_courses(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    status: Optional[CourseProgressStatus] = None,
    is_favorite: Optional[bool] = None
  ) -> PaginatedCourseProgress:
    """Получение всех курсов пользователя с пагинацией"""
    stmt = select(CourseProgress).where(CourseProgress.user_id == user_id)

    # Применяем фильтры
    if status:
      stmt = stmt.where(CourseProgress.status == status)

    if is_favorite is not None:
      stmt = stmt.where(CourseProgress.is_favorite == is_favorite)

    # Считаем общее количество
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Получаем данные с пагинацией
    stmt = stmt.order_by(
      desc(CourseProgress.is_favorite),
      desc(CourseProgress.last_accessed_at)
    ).offset(skip).limit(limit)

    result = await db.execute(stmt)
    items = result.scalars().all()

    # Рассчитываем количество страниц
    pages = (total + limit - 1) // limit if limit > 0 else 1

    return PaginatedCourseProgress(
      items=items,
      total=total,
      page=skip // limit + 1 if limit > 0 else 1,
      size=limit,
      pages=pages
    )

  @staticmethod
  async def get_course_stats(
    db: AsyncSession,
    course_id: int
  ) -> CourseStats:
    """Получение статистики по курсу"""
    # Все записи прогресса для курса
    stmt = select(CourseProgress).where(CourseProgress.course_id == course_id)
    result = await db.execute(stmt)
    progresses = result.scalars().all()

    if not progresses:
      return CourseStats(course_id=course_id)

    total_users = len(progresses)

    # Считаем статистику
    avg_progress = sum(p.progress_percentage for p in progresses) / total_users

    # Фильтруем оценки и рейтинги
    scores = [p.average_score for p in progresses if p.average_score is not None]
    ratings = [p.user_rating for p in progresses if p.user_rating is not None]

    avg_score = sum(scores) / len(scores) if scores else None
    avg_rating = sum(ratings) / len(ratings) if ratings else None

    # Время
    total_time = sum(p.time_spent_seconds for p in progresses)
    avg_time = total_time // total_users if total_users > 0 else 0

    # Статусы
    completed_users = sum(1 for p in progresses if p.status == CourseProgressStatus.COMPLETED)
    active_users = sum(1 for p in progresses if p.status == CourseProgressStatus.IN_PROGRESS)

    completion_rate = (completed_users / total_users) * 100 if total_users > 0 else 0

    # Распределение по статусам
    status_distribution = {}
    for status in CourseProgressStatus:
      count = sum(1 for p in progresses if p.status == status)
      status_distribution[status.value] = count

    # Статистика по урокам
    lesson_completion = []
    for i in range(1, 11):
      lesson_completed = sum(1 for p in progresses if p.completed_lessons >= i)
      completion_rate = (lesson_completed / total_users) * 100 if total_users > 0 else 0
      lesson_completion.append({
        "lesson_number": i,
        "completed_users": lesson_completed,
        "completion_rate": completion_rate
      })

    return CourseStats(
      course_id=course_id,
      total_users=total_users,
      active_users=active_users,
      completed_users=completed_users,
      avg_progress=avg_progress,
      avg_score=avg_score,
      avg_rating=avg_rating,
      avg_time_spent=avg_time,
      completion_rate=completion_rate,
      status_distribution=status_distribution,
      lesson_completion=lesson_completion
    )

  @staticmethod
  async def get_user_summary(
    db: AsyncSession,
    user_id: int
  ) -> UserCoursesSummary:
    """Получение сводки по курсам пользователя"""
    # Все курсы пользователя
    stmt = select(CourseProgress).where(CourseProgress.user_id == user_id)
    result = await db.execute(stmt)
    courses = result.scalars().all()

    if not courses:
      return UserCoursesSummary(user_id=user_id)

    # Основная статистика
    total_courses = len(courses)
    in_progress_courses = sum(1 for c in courses if c.status == CourseProgressStatus.IN_PROGRESS)
    completed_courses = sum(1 for c in courses if c.status == CourseProgressStatus.COMPLETED)
    archived_courses = sum(1 for c in courses if c.status == CourseProgressStatus.ARCHIVED)

    # Время и прогресс
    total_time = sum(c.time_spent_seconds for c in courses)
    avg_progress = sum(c.progress_percentage for c in courses) / total_courses

    # Избранные курсы
    favorite_courses = [c.course_id for c in courses if c.is_favorite]

    # Последняя активность
    last_activity = max(c.last_accessed_at for c in courses if c.last_accessed_at) if courses else None

    # Недавние курсы (последние 5)
    recent_courses = []
    for course in sorted(courses, key=lambda x: x.last_accessed_at or datetime.min, reverse=True)[:5]:
      recent_courses.append({
        "course_id": course.course_id,
        "progress_percentage": course.progress_percentage,
        "status": course.status.value,
        "last_accessed": course.last_accessed_at,
        "updated_at": course.updated_at
      })

    return UserCoursesSummary(
      user_id=user_id,
      total_courses=total_courses,
      in_progress_courses=in_progress_courses,
      completed_courses=completed_courses,
      archived_courses=archived_courses,
      total_time_spent=total_time,
      average_progress=avg_progress,
      favorite_courses=favorite_courses,
      last_activity=last_activity,
      recent_courses=recent_courses
    )

  @staticmethod
  async def bulk_update(
    db: AsyncSession,
    user_id: int,
    updates: list[BulkCourseProgressUpdate]
  ) -> BulkCourseProgressResponse:
    """Массовое обновление прогресса курсов"""
    successful = []
    failed = []

    for update in updates:
      try:
        # Обновляем существующую запись
        progress = await CourseProgressService.update(
          db, user_id, update.course_id, update.data
        )

        if progress:
          successful.append(update.course_id)
        else:
          # Пробуем создать новую запись
          create_data = CourseProgressCreate(
            user_id=user_id,
            course_id=update.course_id,
            **update.data.model_dump(exclude_unset=True)
          )
          created = await CourseProgressService.create(db, create_data)

          if created:
            successful.append(update.course_id)
          else:
            failed.append({
              "course_id": update.course_id,
              "error": "Failed to create"
            })

      except Exception as e:
        failed.append({
          "course_id": update.course_id,
          "error": str(e)
        })

    await db.commit()
    return BulkCourseProgressResponse(
      successful=successful,
      failed=failed
    )

  @staticmethod
  async def archive(
    db: AsyncSession,
    user_id: int,
    course_id: int
  ) -> Optional[CourseProgress]:
    """Архивация прогресса курса"""
    progress = await CourseProgressService.get_by_user_and_course(db, user_id, course_id)
    if not progress:
      return None

    progress.archive()
    await db.commit()
    await db.refresh(progress)
    return progress

  @staticmethod
  async def toggle_favorite(
    db: AsyncSession,
    user_id: int,
    course_id: int
  ) -> Optional[CourseProgress]:
    """Переключение избранного статуса"""
    progress = await CourseProgressService.get_by_user_and_course(db, user_id, course_id)
    if not progress:
      return None

    progress.toggle_favorite()
    await db.commit()
    await db.refresh(progress)
    return progress

  @staticmethod
  async def record_time_spent(
    db: AsyncSession,
    user_id: int,
    course_id: int,
    seconds: int
  ) -> Optional[CourseProgress]:
    """Запись времени, проведенного на курсе"""
    progress = await CourseProgressService.get_by_user_and_course(db, user_id, course_id)
    if not progress:
      return None

    progress.update_time_spent(seconds)
    await db.commit()
    await db.refresh(progress)
    return progress
