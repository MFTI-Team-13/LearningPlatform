# LearningPlatform (MFTI Team 13)

Учебный проект: микросервисная платформа обучения на FastAPI, запускается через Docker Compose.

## Сервисы

- **Auth Service** — `http://localhost:8001/docs`
- **Courses Service** — `http://localhost:8002/docs`
- **Progress Service** — `http://localhost:8003/docs`

## Требования

- Docker
- Docker Compose (в составе Docker Desktop или docker compose plugin)
- Git

## Быстрый старт

### 1) Клонировать репозиторий

```bash
git clone https://github.com/MFTI-Team-13/LearningPlatform.git
cd LearningPlatform
```
### 2) Подготовка секретов и ключей

В проекте используется папка `infra/secrets`.

#### 2.1) Создать необходимые папки

Из корня проекта выполните:

```bash
mkdir -p infra/secrets/keys
```

#### 2.2) Добавление ключей

Необходимые ключи нужно поместить в директорию:

>infra/secrets/keys/

#### 2.3) Создание .env файлов

В папке infra/secrets находятся примеры файлов окружения с суффиксом
*.example.env.

Необходимо переименовать их, удалив .example из названия.

Пример:
>auth_service.example.env → auth_service.env

В результате в папке должны находиться реальные env-файлы:
>infra/secrets/*.env

### 3) Запуск проекта в dev-режиме
Из корня проекта выполните команды:
```bash
docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.dev.yml up -d
```

## Swagger документация

После успешного запуска сервисы будут доступны по адресам:

- Auth Service — http://localhost:8001/docs

- Courses Service — http://localhost:8002/docs

- Progress Service — http://localhost:8003/docs

## Тестовый пользователь

В Auth Service уже создан пользователь для тестирования:

>username: admin
> 
>password: Admin123!

## Остановка проекта

```bash
docker compose -f docker-compose.dev.yml down
```
