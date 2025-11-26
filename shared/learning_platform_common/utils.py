from typing import Any


class ResponseUtils:
    @staticmethod
    def success(message: str | None = None, **kwargs: Any) -> dict[str, Any]:
        response: dict[str, Any] = {"result": True}
        if message:
            response["message"] = message
        if kwargs:
            response.update(kwargs)
        return response

    @staticmethod
    def error(message: str = "Произошла ошибка") -> dict[str, Any]:
        return {"result": False, "message": message}
