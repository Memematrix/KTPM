from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request

app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        request,
        "home.html"
    )


@app.get("/health")
async def health_check():
    return {"status": "ok"}