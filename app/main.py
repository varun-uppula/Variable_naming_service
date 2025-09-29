from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api import routes


app = FastAPI(title="Variable Naming Service")

# Serve static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Landing page
@app.get("/")
def read_index():
    return FileResponse("app/static/index.html")

@app.get("/admin")
def read_admin():
    return FileResponse("app/static/admin.html")


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API routes (no prefix → available directly as /formats, /standards, etc.)
app.include_router(routes.router)
