from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_lessons():
    return {"message": "Lessons module inside progress is working"}

__all__ = ["router"]
