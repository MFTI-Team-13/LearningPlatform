from fastapi import HTTPException, status
import logging


class NotFoundError(HTTPException):
    def __init__(self, detail="Ресурс не найден"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class AlreadyExistsError(HTTPException):
    def __init__(self, detail="Запись уже существует"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ConflictError(HTTPException):
    def __init__(self, detail="Конфликт данных"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class ForbiddenError(HTTPException):
    def __init__(self, detail="Доступ запрещён"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


logger = logging.getLogger(__name__)


async def handle_errors(func):
    try:
        return await func()

    except NotFoundError as e:
        logger.warning(f"[NOT FOUND] {e.detail}")
        raise e

    except AlreadyExistsError as e:
        logger.warning(f"[ALREADY EXISTS] {e.detail}")
        raise e

    except ConflictError as e:
        logger.warning(f"[CONFLICT] {e.detail}")
        raise e

    except ForbiddenError as e:
        logger.warning(f"[FORBIDDEN] {e.detail}")
        raise e

    except HTTPException as e:
        logger.warning(f"[HTTP ERROR] {e.detail}")
        raise e

    except Exception as e:
        logger.error(f"[UNEXPECTED] {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Произошла непредвиденная ошибка сервера."
        )

