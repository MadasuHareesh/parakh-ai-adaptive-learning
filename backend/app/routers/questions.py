from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies import require_admin
from ..models import Question
from ..schemas import AddQuestion

router = APIRouter(tags=["Questions"])


@router.get("")
def list_questions(admin=Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.query(Question).order_by(Question.id.desc()).all()
    return [
        {"id": q.id, "question_text": q.question_text, "topic": q.topic, "subtopic": q.subtopic,
         "difficulty": q.difficulty, "pre_assessment": q.pre_assessment, "active": q.active}
        for q in rows
    ]


@router.post("")
def add_question(data: AddQuestion, admin=Depends(require_admin), db: Session = Depends(get_db)):
    q = Question(**data.model_dump())
    db.add(q)
    db.commit()
    db.refresh(q)
    return {"message": "Question created", "id": q.id}


@router.delete("/{question_id}")
def delete_question(question_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    q.active = False
    db.commit()
    return {"message": "Question disabled"}
