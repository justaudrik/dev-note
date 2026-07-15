from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from . import models
from .routers import auth_router, documents

# Auto-create all tables on startup (prototype only — use Alembic migrations in full project)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="DevNote API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve HTML/CSS/JS files from the static/ directory
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router.router)
app.include_router(documents.router)


@app.get("/")
def serve_index():
    return FileResponse("static/index.html")


@app.get("/dashboard")
def serve_dashboard():
    return FileResponse("static/dashboard.html")
