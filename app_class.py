version: '3'

services:

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

  report:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    volumes:
      - .:/usr/src/app
    command: bash -c "wait-for-it 64.226.65.160:5432 -- uvicorn report_fastapi:app --host 0.0.0.0 --port 8000"

  app:
    build:
      context: .
      dockerfile: Dockerfile
    env_file:
      - .env.docker
    depends_on:
      - postgres
      - redis
    volumes:
      - .:/usr/src/app
    command: bash -c "wait-for-it 64.226.65.160:5432 -- python app.py"

  postgres:
    image: postgres:latest
    environment:
      POSTGRES_DB: financial_records
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - app_db:/var/lib/postgresql/data

volumes:
  app_db:
