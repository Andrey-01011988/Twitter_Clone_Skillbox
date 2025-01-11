Проект, соответствующий требованиям с использованием FastAPI и разделенный на две составляющие (бэкенд и клиентская часть), может быть организован следующим образом:

## Структура проекта

```
/my_microblog_service
│
├── server/                     # Директория для бэкенда
│   ├── app/
│   │   ├── main.py             # Основной файл приложения FastAPI
│   │   ├── models.py           # Определение моделей базы данных
│   │   ├── schemas.py          # Схемы для валидации данных
│   │   ├── crud.py             # CRUD операции для работы с базой данных
│   │   ├── api/
│   │   │   ├── endpoints.py     # Определение эндпоинтов API
│   │   │   └── dependencies.py   # Зависимости для эндпоинтов
│   │   └── database.py         # Настройки подключения к базе данных
│   ├── Dockerfile               # Dockerfile для бэкенда
│   └── requirements.txt         # Зависимости Python для бэкенда
│
├── client/                     # Директория для клиентской части
│   ├── static/                 # Статические файлы (HTML, CSS, JS)
│   ├── index.html              # Главная страница приложения
│   └── nginx.conf              # Конфигурация Nginx
│
└── docker-compose.yml          # Конфигурация Docker Compose для всего проекта
```

## Описание компонентов

### 1. Бэкенд (server)

#### Основной файл приложения (`main.py`)

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from . import models, schemas, crud
from .database import SessionLocal, engine

# Создание базы данных при старте приложения
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/tweets", response_model=schemas.TweetResponse)
def create_tweet(tweet: schemas.TweetCreate, api_key: str, db: Session = Depends(get_db)):
    return crud.create_tweet(db=db, tweet=tweet, api_key=api_key)

@app.delete("/api/tweets/{tweet_id}", response_model=schemas.ResponseMessage)
def delete_tweet(tweet_id: int, api_key: str, db: Session = Depends(get_db)):
    return crud.delete_tweet(db=db, tweet_id=tweet_id, api_key=api_key)

# Другие эндпоинты...
```

#### Dockerfile для бэкенда

```dockerfile
FROM python:3.9

WORKDIR /app

COPY ./app /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
```

#### requirements.txt

```plaintext
fastapi[all]
sqlalchemy
psycopg2-binary
uvicorn
```

### 2. Клиентская часть (client)

#### Статические файлы

- **`index.html`**: HTML-страница с формами для взаимодействия с API.
- **`static/`**: Директория для CSS и JavaScript файлов.

#### Конфигурация Nginx (`nginx.conf`)

```nginx
server {
    listen 80;

    location / {
        root /usr/share/nginx/html;  # Путь к статическим файлам клиента
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://server:80;  # Прокси на бэкенд-сервис
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 3. Docker Compose (`docker-compose.yml`)

```yaml
version: '3.4'

services:
  server:
    build:
      context: ./server
      dockerfile: Dockerfile
    ports:
      - "8000:80"
    depends_on:
      - db

  client:
    image: nginx:latest
    volumes:
      - ./client/static:/usr/share/nginx/html  # Монтирование статических файлов клиента
      - ./client/nginx.conf:/etc/nginx/conf.d/default.conf  # Конфигурация Nginx
    ports:
      - "80:80"

  db:
    image: postgres:latest
    environment:
      POSTGRES_DB: twitter
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: admin
    ports:
      - "5432:5432"
```

## Запуск проекта

Для запуска всего проекта достаточно выполнить команду:

```bash
docker-compose up --build -d
```

## Заключение

Такой подход позволяет разделить проект на две основные составляющие — бэкенд на FastAPI и клиентскую часть с использованием Nginx для обслуживания статических файлов и проксирования запросов к API. Это обеспечивает четкую архитектуру и позволяет легко управлять компонентами приложения. Автоматическая документация API через Swagger будет доступна по адресу `/docs`, что упрощает тестирование и взаимодействие с API.

Citations:
[1] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/32437936/6856d14f-f198-40b0-b34a-2dddc83b3d81/Itogovyi-proekt-Python-Advanced.pdf
[2] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/32437936/d6c184a2-5a5f-4ecf-8f96-bd4312233320/docker-compose.yaml