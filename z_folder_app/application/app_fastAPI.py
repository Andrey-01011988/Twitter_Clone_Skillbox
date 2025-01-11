import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

# Определяем корневую директорию и папки для шаблонов и статических файлов
root_dir = os.path.dirname(os.path.abspath(__file__))
template_folder = os.path.join(root_dir, "templates")
static_folder = os.path.join(root_dir, "static")

app = FastAPI()

# Настройка Jinja2 для работы с шаблонами
templates = Jinja2Templates(directory=template_folder)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory=static_folder), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index_fastAPI.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)