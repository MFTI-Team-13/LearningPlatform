from fastapi import HTTPException, status
import logging
from sqlalchemy.exc import IntegrityError
import asyncpg

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    def __init__(self, status_code: int, detail: str):
      self.detail = detail
      self.status_code = status_code
      super().__init__(detail)

class NotFoundError(HTTPException):
    def __init__(self, detail="Ресурс не найден"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class AlreadyExistsError(HTTPException):
    def __init__(self, detail="Запись уже существует"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ConflictError(HTTPException):
    def __init__(self, detail="Конфликт данных"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ForbiddenError(HTTPException):
    def __init__(self, detail="Доступ запрещён"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


async def handle_errors(func):
    try:
        return await func()

    except (NotFoundError, AlreadyExistsError, ConflictError, ForbiddenError) as e:
        logger.warning(f"[{e.__class__.__name__.upper()}] {e.detail}")
        raise e
    except IntegrityError as e:
        if isinstance(e.orig, asyncpg.exceptions.UniqueViolationError):
            logger.warning("[UNIQUE VIOLATION] Нарушение уникальности")
            raise ConflictError("Нарушение уникальности данных")
        raise HTTPException(400, "Ошибка целостности данных")
    except HTTPException as e:
        logger.warning(f"[HTTP ERROR] {e.detail}")
        raise e

    except Exception as e:
        logger.error(f"[UNEXPECTED] {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Произошла непредвиденная ошибка сервера."
        )
