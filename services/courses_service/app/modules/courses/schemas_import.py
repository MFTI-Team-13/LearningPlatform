from .schemas.CourseScheme import *
from .schemas.LessonScheme import *
from .schemas.TestScheme import *
from .schemas.QuestionScheme import *
from .schemas.AnswerScheme import *
from .schemas.CourseReviewScheme import *
from .schemas.CourseUserScheme import *

course_schemas = [
    CourseBase, CourseCreate, CourseUpdate, CourseResponse
]

lesson_schemas = [
    LessonBase, LessonCreate, LessonUpdate, LessonResponse
]

test_schemas = [
    TestBase, TestCreate, TestUpdate, TestResponse
]

question_schemas = [
    QuestionBase, QuestionCreate, QuestionUpdate, QuestionResponse, QuestionWithTest, QuestionWithAnswers
]

answer_schemas = [
    AnswerBase, AnswerCreate, AnswerUpdate, AnswerResponse, AnswerWithQuestion
]

review_schemas = [
    CourseReviewBase, CourseReviewCreate, CourseReviewUpdate, CourseReviewResponse
]

course_user_schemas = [
    CourseUserCreate, CourseUserUpdate, CourseUserResponse, CourseUserWithCourseResponse, CourseUserListResponse
]

all_schemas = (
    course_schemas + lesson_schemas + test_schemas +
    question_schemas + answer_schemas + review_schemas + course_user_schemas
)

__all__ = [schema.__name__ for schema in all_schemas]
