from dotenv import load_dotenv
load_dotenv()  # Load .env before anything else reads os.getenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from . import models
from .routers import auth_router, documents
from .routers.collaboration import router as collab_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="DevNote API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router.router)
app.include_router(documents.router)
app.include_router(collab_router)


@app.get("/")
def serve_index():
    return FileResponse("static/index.html")


@app.get("/dashboard")
def serve_dashboard():
    return FileResponse("static/dashboard.html")
