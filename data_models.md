# Модель данных для учебной платформы (3 микросервиса)

Документ содержит полностью структурированное текстовое описание всех сущностей и полей для трёх микросервисов: **auth-service**, **courses-service**, **progress-service**. Формат удобен для передачи команде, дизайна БД, написания ORM-моделей и enum’ов.

---

# 1. Микросервис **auth-service**

**Назначение:** регистрация, авторизация, хранение пользователей и ролей.

## 1.1. Таблица `users`

**Описание:** данные пользователя системы.

**Поля:**

* **id** — UUID, PK.
* **first_name** — строка, имя, not null.
* **last_name** — строка, фамилия, not null.
* **login** — строка, логин (email/username), **уникальный**, not null.
* **password_hash** — строка, захэшированный пароль, not null.
* **role** — enum/string, not null. Возможные значения:

  * `student`
  * `teacher`
  * `admin`
* **is_active** — bool, default `true`.
* **created_at** — datetime, not null.
* **updated_at** — datetime, not null.

**Ограничения:**

* `UNIQUE(login)`
* индексы на `login`, `role`.

---

# 2. Микросервис **courses-service**

**Назначение:** хранение образовательного контента: курсы, уроки, тесты, вопросы, варианты ответов, отзывы.

## 2.1. Таблица `courses`

**Назначение:** каталог доступных курсов.

**Поля:**

* **id** — UUID, PK.
* **title** — строка, название курса, not null.
* **description** — текст, nullable.
* **author_id** — UUID пользователя из auth-service, nullable.
* **level** — enum/string, уровень сложности. Возможные значения:

  * `beginner`
  * `intermediate`
  * `advanced`
* **is_published** — bool, default `false`.
* **created_at**, **updated_at** — datetime.

## 2.2. Таблица `lessons`

**Назначение:** уроки внутри курса.

**Поля:**

* **id** — UUID, PK.
* **course_id** — UUID курса, not null.
* **title** — строка, not null.
* **short_description** — строка, nullable.
* **content_type** — enum/string, not null:

  * `text`
  * `video`
* **text_content** — текст, nullable (для текстовых уроков).
* **video_url** — строка, nullable (для видеоуроков).
* **order_index** — int, порядок в курсе, not null.
* **created_at**, **updated_at** — datetime.

## 2.3. Таблица `tests`

**Назначение:** тест, привязанный к уроку.

**Поля:**

* **id** — UUID, PK.
* **lesson_id** — UUID урока, not null, **уникальный**.
* **title** — строка, not null.
* **description** — текст, nullable.
* **is_active** — bool, default `true`.
* **created_at** — datetime.

**Ограничения:**

* `UNIQUE(lesson_id)` — один тест на урок.

## 2.4. Таблица `questions`

**Назначение:** вопросы в тесте.

**Поля:**

* **id** — UUID, PK.
* **test_id** — UUID теста, not null.
* **text** — текст вопроса, not null.
* **question_type** — enum/string:

  * `single_choice`
  * `multiple_choice`
  * `open`
* **order_index** — int, порядок вопроса, not null.
* **score** — int, баллы за вопрос, not null.

## 2.5. Таблица `answer_options`

**Назначение:** варианты ответов для вопросов с выбором.

**Поля:**

* **id** — UUID, PK.
* **question_id** — UUID вопроса, not null.
* **text** — текст варианта ответа, not null.
* **is_correct** — bool, является ли правильным.
* **order_index** — int, порядок.

## 2.6. Таблица `course_reviews`

**Назначение:** отзывы о курсах.

**Поля:**

* **id** — UUID, PK.
* **course_id** — UUID курса, not null.
* **user_id** — UUID из auth-service, not null.
* **rating** — int (1–5), not null.
* **comment** — текст, nullable.
* **is_published** — bool, default `true`.
* **created_at**, **updated_at** — datetime.

**Ограничения (опционально):**

* `UNIQUE(course_id, user_id)` — один отзыв от пользователя на курс.

---

# 3. Микросервис **progress-service**

**Назначение:** хранение прогресса пользователя по курсам, урокам и тестам.

## 3.1. Таблица `user_courses`

**Назначение:** пользователь проходит конкретный курс.

**Поля:**

* **id** — UUID, PK.
* **user_id** — UUID, not null.
* **course_id** — UUID, not null.
* **progress_percent** — int (0–100), not null.
* **status** — enum/string:

  * `not_started`
  * `in_progress`
  * `completed`
* **started_at** — datetime.
* **completed_at** — datetime.
* **last_accessed_at** — datetime.

**Ограничения:**

* `UNIQUE(user_id, course_id)`

## 3.2. Таблица `lesson_progress`

**Назначение:** прогресс пользователя внутри уроков.

**Поля:**

* **id** — UUID, PK.
* **user_id** — UUID, not null.
* **lesson_id** — UUID, not null.
* **is_completed** — bool, default `false`.
* **completed_at** — datetime.

**Ограничения:**

* `UNIQUE(user_id, lesson_id)`

## 3.3. Таблица `test_attempts`

**Назначение:** попытки тестирования.

**Поля:**

* **id** — UUID, PK.
* **user_id** — UUID, not null.
* **test_id** — UUID, not null.
* **started_at** — datetime, not null.
* **finished_at** — datetime.
* **score** — int, nullable.
* **max_score** — int, nullable.
* **is_passed** — bool, nullable.

## 3.4. Таблица `test_attempt_answers`

**Назначение:** детальные ответы в рамках попытки.

**Поля:**

* **id** — UUID, PK.
* **attempt_id** — UUID, not null.
* **question_id** — UUID, not null.
* **answer_option_id** — UUID, nullable.
* **text_answer** — текстовая строка, nullable.
* **is_correct** — bool, nullable.
* **score_received** — int, nullable.

---

# Итог

Документ описывает:

* структуру всех сущностей для трёх микросервисов;
* требования к полям, enum’ам, связям и ограничениям;
* модель данных, достаточную для реализации: регистрации, курсов, уроков, тестов, отзывов, личного кабинета и прогресса.

Можно использовать как основу для разработки ORM-моделей, миграций и API.
