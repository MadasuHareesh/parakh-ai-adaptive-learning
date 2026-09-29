from fastapi import APIRouter, Depends
from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import get_current_user, require_admin
from ..models import User, Attempt, LearnerProfile, Question
from ..services.analytics_engine import student_summary

router = APIRouter(tags=["Analytics"])


@router.get("/student")
def student_analytics(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return student_summary(db, user.id)


@router.get("/recent")
def recent_attempts(user=Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Attempt).filter(Attempt.user_id == user.id).order_by(desc(Attempt.timestamp)).limit(20).all()
    return [
        {
            "id": r.id, "question_id": r.question_id, "mode": r.mode,
            "is_verification": r.is_verification, "correct": r.correct,
            "confidence": r.confidence, "response_time": r.response_time,
            "difficulty": r.difficulty, "topic": r.topic, "subtopic": r.subtopic,
            "evaluation": r.evaluation, "timestamp": r.timestamp.isoformat(),
        }
        for r in rows
    ]


@router.get("/admin")
def admin_analytics(admin=Depends(require_admin), db: Session = Depends(get_db)):
    students = db.query(User).filter(User.role == "student").count()
    questions = db.query(Question).filter(Question.active == True).count()  # noqa: E712
    attempts = db.query(Attempt).count()
    correct = db.query(Attempt).filter(Attempt.correct == True).count()  # noqa: E712
    not_started = db.query(LearnerProfile).join(User, User.id == LearnerProfile.user_id).filter(
        User.role == "student", LearnerProfile.assessment_mode == "pre_assessment").count()

    return {
        "students": students,
        "questions": questions,
        "attempts": attempts,
        "accuracy": round(correct / attempts * 100, 2) if attempts else 0,
        "students_not_started": not_started,
        "students_started": max(students - not_started, 0),
    }
