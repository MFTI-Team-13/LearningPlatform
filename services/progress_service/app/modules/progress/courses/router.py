from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db.session import get_db
from app.common.deps.auth import CurrentUserDep, require_role
from app.modules.progress.courses import schemas, services

router = APIRouter()


# Основные CRUD операции
@router.post(
  "/",
  response_model=schemas.CourseProgressResponse,
  status_code=status.HTTP_201_CREATED,
  dependencies=[Depends(require_role("student", "teacher"))]
)
async def create_course_progress(
  progress_data: schemas.CourseProgressCreate,
  db: AsyncSession = Depends(get_db),
  current_user: CurrentUserDep = Depends(),
) -> schemas.CourseProgressResponse:
  """Создание записи о прогрессе курса"""
  return await services.CourseProgressService.create(db, progress_data)


@router.get(
  "/{course_id}",
  response_model=schemas.CourseProgressResponse,
  dependencies=[Depends(require_role("student", "teacher"))]
)
async def get_course_progress(
  course_id: int,
  db: AsyncSession = Depends(get_db),
  current_user: CurrentUserDep = Depends(),
) -> schemas.CourseProgressResponse:
  """Получение прогресса по конкретному курсу"""
  progress = await services.CourseProgressService.get_by_user_and_course(
    db, current_user.id, course_id
  )

  if not progress:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Course progress not found"
    )

  return progress


@router.put(
  "/{course_id}",
  response_model=schemas.CourseProgressResponse,
  dependencies=[Depends(require_role("student", "teacher"))]
)
async def update_course_progress(
  course_id: int,
  update_data: schemas.CourseProgressUpdate,
  db: AsyncSession = Depends(get_db),
  current_user: CurrentUserDep = Depends(),
) -> schemas.CourseProgressResponse:
  """Обновление прогресса курса"""
  progress = await services.CourseProgressService.update(
    db, current_user.id, course_id, update_data
  )

  if not progress:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Course progress not found"
    )

  return progress


@router.delete(
  "/{course_id}",
  status_code=status.HTTP_204_NO_CONTENT,
  dependencies=[Depends(require_role("student", "teacher"))]
)
async def delete_course_progress(
  course_id: int,
  db: AsyncSession = Depends(get_db),
  current_user: CurrentUserDep = Depends(),
) -> None:
  """Удаление прогресса курса"""
  success = await services.CourseProgressService.delete(
    db, current_user.id, course_id
  )

  if not success:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Course progress not found"
    )


# Списки и фильтрация
@router.get(
  "/",
  response_model=schemas.PaginatedCourseProgress,
  dependencies=[Depends(require_role("student", "teacher"))]
)
async def list_course_progress(
  skip: int = Query(0, ge=0, description="Смещение"),
  limit: int = Query(100, ge=1, le=500, description="Лимит"),
  status: Optional[schemas.CourseProgressStatus] = Query(None, description="Фильтр по статусу"),
  is_favorite: Optional[bool] = Query(None, description="Фильтр по избранному"),
  db: AsyncSession = Depends(get_db),
  current_user: CurrentUserDep = Depends(),
) -> schemas.PaginatedCourseProgress:
  """Получение списка прогресса по курсам с пагинацией"""
  return await services.CourseProgressService.get_user_courses(
    db=db,
    user_id=current_user.id,
    skip=skip,
    limit=limit,
    status=status,
    is_favorite=is_favorite
  )


# Дополнительные операции
@router.post(
  "/bulk-update/",
  response_model=schemas.BulkCourseProgressResponse,
  dependencies=[Depends(require_role("student", "teacher"))]
)
async def bulk_update_course_progress(
  updates: list[schemas.BulkCourseProgressUpdate],
  db: AsyncSession = Depends(get_db),
  current_user: CurrentUserDep = Depends(),
) -> schemas.BulkCourseProgressResponse:
  """Массовое обновление прогресса курсов"""
  return await services.CourseProgressService.bulk_update(
    db, current_user.id, updates
  )


@router.post(
  "/{course_id}/archive",
  response_model=schemas.CourseProgressResponse,
  dependencies=[Depends(require_role("student", "teacher"))]
)
async def archive_course_progress(
  course_id: int,
  db: AsyncSession = Depends(get_db),
  current_user: CurrentUserDep = Depends(),
) -> schemas.CourseProgressResponse:
  """Архивация прогресса курса"""
  progress = await services.CourseProgressService.archive(
    db, current_user.id, course_id
  )

  if not progress:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Course progress not found"
    )

  return progress


@router.post(
  "/{course_id}/toggle-favorite",
  response_model=schemas.CourseProgressResponse,
  dependencies=[Depends(require_role("student", "teacher"))]
)
async def toggle_course_favorite(
  course_id: int,
  db: AsyncSession = Depends(get_db),
  current_user: CurrentUserDep = Depends(),
) -> schemas.CourseProgressResponse:
  """Переключение избранного статуса курса"""
  progress = await services.CourseProgressService.toggle_favorite(
    db, current_user.id, course_id
  )

  if not progress:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Course progress not found"
    )

  return progress


@router.post(
  "/{course_id}/record-time",
  response_model=schemas.CourseProgressResponse,
  dependencies=[Depends(require_role("student", "teacher"))]
)
async def record_course_time(
  course_id: int,
  seconds: int = Query(..., ge=0, description="Количество секунд"),
  db: AsyncSession = Depends(get_db),
  current_user: CurrentUserDep = Depends(),
) -> schemas.CourseProgressResponse:
  """Запись времени, проведенного на курсе"""
  progress = await services.CourseProgressService.record_time_spent(
    db, current_user.id, course_id, seconds
  )

  if not progress:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail="Course progress not found"
    )

  return progress


# Статистика
@router.get(
  "/user/summary",
  response_model=schemas.UserCoursesSummary,
  dependencies=[Depends(require_role("student", "teacher"))]
)
async def get_user_courses_summary(
  db: AsyncSession = Depends(get_db),
  current_user: CurrentUserDep = Depends(),
) -> schemas.UserCoursesSummary:
  """Получение сводки по курсам пользователя"""
  return await services.CourseProgressService.get_user_summary(
    db, current_user.id
  )


@router.get(
  "/{course_id}/stats",
  response_model=schemas.CourseStats,
  dependencies=[Depends(require_role("teacher", "admin"))]
)
async def get_course_statistics(
  course_id: int,
  db: AsyncSession = Depends(get_db),
  current_user: CurrentUserDep = Depends(),
) -> schemas.CourseStats:
  """Получение статистики по курсу (требуются права преподавателя или администратора)"""
  return await services.CourseProgressService.get_course_stats(db, course_id)
