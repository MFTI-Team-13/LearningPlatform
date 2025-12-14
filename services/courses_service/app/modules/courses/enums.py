import enum


class ContentType(enum.Enum):
  TEXT = "text"
  VIDEO = "video"

class CourseLevel(enum.Enum):
  BEGINNER = "beginner"
  INTERMEDIATE = "intermediate"
  ADVANCED = "advanced"

class QuestionType(enum.Enum):
  SINGLE_CHOICE = "single_choice"
  MULTIPLE_CHOICE = "multiple_choice"
  OPEN = "open"

class UserRole(enum.Enum):
  STUDENT = "student"
  TEACHER = "teacher"
  ADMIN = "admin"
