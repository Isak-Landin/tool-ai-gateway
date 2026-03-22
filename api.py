import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from api_routes.project_routes.project import projects_router

LOCAL_SERVER_URL = os.getenv("LOCAL_SERVER_URL")
if LOCAL_SERVER_URL is None:
    exit(1)

app = FastAPI()
app.include_router(projects_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[LOCAL_SERVER_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)










@app.get("/debug")
def debug():
    return FileResponse("index.html")
