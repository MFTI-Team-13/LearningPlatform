# Команды для успешного успеха
## Что делать первый делом:
>git clone https://github.com/MFTI-Team-13/LearningPlatform.git

## Базовые команды с git:
>git init #1 раз
> 
>git pull #кроме первого раза
> 
>git commit -m "feat: commit name на английском"
> 
>git remote add origin https://github.com/MFTI-Team-13/LearningPlatform.git
> 
>git push -u origin main #1-й раз, а дальше просто git push)

## Работа с ветками:

>git checkout main #перейти на главную ветку
> 
>git pull origin main #получить свежий код
> 
>git checkout -b feature/add-chat #создать ветку и перейти
> 
>git add . #добавить изменения из рабочего каталога в индекс
> 
>git commit -m "feat: add chat" #коммит
>
>git push origin feature/add-chat #отправить изменения

### Затем необходимо зайти в репозиторий, нажать на Compare & pull request
P.S. Если нет, то Pull requests → New pull request

### Настрой Pull Request, чтобы тимлид увидел изменения:
- base: main

- compare: feature/add-chat
(то есть куда вливаем → из какой ветки вливаем)

### Заполни заявку
#### Title: feat: добавлен чат для пользователей

#### Description:
##### Что сделано
- Добавлен новый модуль чата
- Подключен сокет для реального времени
- Обновлены стили профиля

##### Проверка
- [x] Код запускается
- [x] Тесты проходят

### Отправь на ревью
- В правом блоке Reviewers → выбери тимлида
- Нажми Create pull request.
#### Победа! Тимлид увидит твой код, если все хорошо зальет в главную ветку и надо будет запуллить :)

### Уронить и поднять Docker контейнер(а) локально(dev) из папки infra
*Если не писать имя контейнера, то все будут исполняться, container - имя контейнера, можно не писать, если все хочется использовать*

>docker compose -f docker-compose.dev.yml down container

>docker compose -f docker-compose.dev.yml build container

>docker compose -f docker-compose.dev.yml up -d container

### Логи Docker контейнера из папки infra
*-f рантайм/без -f на текущий момент без новых логов*

>docker compose -p infra logs -f auth_service

## Перейти в директорию своего микросервиса
>cd services/auth_service

>cd services/courses_service

>cd services/progress_service

## Для минимизирования "плохого" кода
#### Посмотреть все проблемы по стилю/линту
>ruff check .

#### Прогнать все хуки как в коммите (ruff)
>pre-commit run ruff --all-files
