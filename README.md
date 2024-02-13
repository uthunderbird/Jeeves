# Jeeves - Финансовый помощник

Jeeves - финансовый помощник с интегрированным искусственным интеллектом. Взаимодействие с пользователями производится посредством Telegram бота.

## Настройка проекта

### Предварительные требования

- Docker и Docker Compose должны быть установлены на вашей машине.
- Создайте своего Telegram бота и получите его токен.
- Получите API токен чата GPT для работы с LLM GPT.

### Установка и запуск

1. Клонируйте репозиторий проекта:
    ```bash
    git clone git@github.com:jeeves-ai/Jeeves.git
     ```
2. Перейдите в директорию проекта:
    ```bash
    cd Jeeves
    ```
3. Создайте файл `.env.docker` в корне приложения со следующим содержимым:
    ```bash
    TELEGRAM_TOKEN=ваш_токен_телеграм_бота
    OPENAI_API_KEY=ваш_openai_api_ключ
    DATABASE_URL=postgresql://postgres:postgres@postgres/financial_records
    REDIS_HOST=redis://redis:6379
    ```
4. Запустите все сервисы с помощью Docker Compose:
    ```bash
    docker-compose up --build
    ```

После выполнения этих шагов, все сервисы будут запущены, и бот будет готов к использованию.

## Использование бота

Отправьте неформализованное сообщение о финансовой транзакции в Telegram бот, например: "Купил что-то за такую-то сумму".

## Работа с отчетами

Для просмотра отчетов через браузер, перейдите по адресу `http://localhost:8000/record/{user_id}`, где `{user_id}` - это идентификатор пользователя в Telegram.
