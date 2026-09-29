from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .database import Base, engine
from .routers import auth, assessment, analytics, questions, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PARAKH AI Adaptive MCQ API",
    version="2.0.0",
    description="Confidence-aware adaptive MCQ selection (paper: PARAKH AI).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth")
app.include_router(assessment.router, prefix="/api/assessment")
app.include_router(analytics.router, prefix="/api/analytics")
app.include_router(questions.router, prefix="/api/questions")
app.include_router(admin.router, prefix="/api/admin")


@app.get("/")
def root():
    return {
        "name": "PARAKH AI Adaptive MCQ API",
        "status": "running",
        "docs": "/docs",
    }
