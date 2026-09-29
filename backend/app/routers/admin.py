"""Student-account management for the administrator dashboard (paper Sec. III-G)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_admin
from ..models import User, LearnerProfile, Attempt, TopicPerformance
from ..schemas import CreateStudent
from ..security import hash_password

router = APIRouter(tags=["Admin"])


@router.get("/students")
def list_students(admin=Depends(require_admin), db: Session = Depends(get_db)):
    students = db.query(User).filter(User.role == "student").order_by(User.name).all()
    out = []
    for s in students:
        profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == s.id).first()
        attempts = db.query(Attempt).filter(Attempt.user_id == s.id).count()
        correct = db.query(Attempt).filter(Attempt.user_id == s.id, Attempt.correct == True).count()  # noqa: E712
        out.append({
            "id": s.id, "name": s.name, "email": s.email,
            "attempts": attempts,
            "accuracy": round(correct / attempts * 100, 1) if attempts else 0,
            "ability": round((profile.overall_ability if profile else 0.5) * 100, 1),
            "status": "Not Started" if not profile or profile.assessment_mode == "pre_assessment" and attempts == 0
                      else "Assessment Started",
        })
    return out


@router.post("/students")
def create_student(data: CreateStudent, admin=Depends(require_admin), db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="A user with this email already exists")
    user = User(name=data.name, email=data.email, password_hash=hash_password(data.password), role="student")
    db.add(user)
    db.commit()
    db.refresh(user)
    db.add(LearnerProfile(user_id=user.id))
    db.commit()
    return {"message": "Student created", "id": user.id}


@router.post("/students/{student_id}/reset")
def reset_student(student_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")

    db.query(Attempt).filter(Attempt.user_id == student_id).delete()
    db.query(TopicPerformance).filter(TopicPerformance.user_id == student_id).delete()
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == student_id).first()
    if profile:
        db.delete(profile)
        db.flush()  # unique constraint on user_id: the delete must land before the insert below
    db.add(LearnerProfile(user_id=student_id))
    db.commit()
    return {"message": "Student assessment reset"}


@router.delete("/students/{student_id}")
def delete_student(student_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == student_id, User.role == "student").first()
    if not user:
        raise HTTPException(status_code=404, detail="Student not found")

    db.query(Attempt).filter(Attempt.user_id == student_id).delete()
    db.query(TopicPerformance).filter(TopicPerformance.user_id == student_id).delete()
    db.query(LearnerProfile).filter(LearnerProfile.user_id == student_id).delete()
    db.delete(user)
    db.commit()
    return {"message": "Student deleted"}
