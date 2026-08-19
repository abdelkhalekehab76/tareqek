"""
Quran Memorization Center - FastAPI Application
Arabic-first, RTL, role-based (ADMIN / STUDENT)
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base, SessionLocal
from app.seed import run_seed
from app.routers import auth, students, exams, progress, content, dashboard, quran
from app.config import APP_NAME, DEBUG

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = SessionLocal()
    try:
        run_seed(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=APP_NAME,
    description="نظام إدارة مركز تحفيظ القرآن الكريم",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if DEBUG else None,
    redoc_url="/api/redoc" if DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# API routers
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(exams.router)
app.include_router(progress.router)
app.include_router(content.router)
app.include_router(dashboard.router)
app.include_router(quran.router)


def get_token_from_request(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    return request.cookies.get("access_token")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request, 
        name="login.html", 
        context={"app_name": APP_NAME}
    )


@app.get("/admin", response_class=HTMLResponse)
@app.get("/admin/{path:path}", response_class=HTMLResponse)
async def admin_pages(request: Request, path: str = ""):
    return templates.TemplateResponse(
        request=request, 
        name="admin.html", 
        context={"app_name": APP_NAME}
    )


@app.get("/student", response_class=HTMLResponse)
@app.get("/student/{path:path}", response_class=HTMLResponse)
async def student_pages(request: Request, path: str = ""):
    return templates.TemplateResponse(
        request=request, 
        name="student.html", 
        context={"app_name": APP_NAME}
    )


@app.get("/health")
async def health():
    return {"status": "ok", "app": APP_NAME}
