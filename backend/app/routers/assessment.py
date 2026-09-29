"""Assessment loop: pre-assessment (Level 0) then the adaptive loop of paper Fig. 2."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import config
from ..database import get_db
from ..dependencies import get_current_user
from ..models import Question, Attempt, LearnerProfile, TopicPerformance
from ..schemas import AnswerSubmission
from ..services.adaptive_engine import choose_next_question
from ..services.confidence_engine import decide, next_target
from ..services.learner_model import normalise_difficulty, update_ability

router = APIRouter(tags=["Assessment"])


def ensure_profile(db, user_id):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not profile:
        profile = LearnerProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def question_dict(q, is_verification=False):
    return {
        "id": q.id, "question_text": q.question_text,
        "option_a": q.option_a, "option_b": q.option_b,
        "option_c": q.option_c, "option_d": q.option_d,
        "topic": q.topic, "subtopic": q.subtopic, "difficulty": q.difficulty,
        "is_verification": is_verification,
    }


@router.get("/status")
def status(user=Depends(get_current_user), db: Session = Depends(get_db)):
    profile = ensure_profile(db, user.id)
    pre_total = db.query(Question).filter(
        Question.pre_assessment == True, Question.active == True).count()  # noqa: E712
    pre_done = db.query(Attempt).filter(
        Attempt.user_id == user.id, Attempt.mode == "pre_assessment").count()

    return {
        "mode": profile.assessment_mode,
        "pre_assessment_total": pre_total,
        "pre_assessment_completed": min(pre_done, pre_total),
        "pre_assessment_complete": pre_total > 0 and pre_done >= pre_total,
        "session_number": profile.session_no,
        "session_length": config.TEST_LENGTH,
        "session_answered": profile.session_answered,
    }


@router.get("/next/{mode}")
def next_question(mode: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if mode not in {"pre_assessment", "adaptive"}:
        raise HTTPException(status_code=400, detail="Invalid assessment mode")

    profile = ensure_profile(db, user.id)

    if mode == "pre_assessment":
        questions = db.query(Question).filter(
            Question.pre_assessment == True, Question.active == True).order_by(Question.id).all()  # noqa: E712
        attempted = {x.question_id for x in db.query(Attempt.question_id).filter(
            Attempt.user_id == user.id, Attempt.mode == "pre_assessment").all()}
        remaining = [q for q in questions if q.id not in attempted]

        if not remaining:
            profile.assessment_mode = "adaptive"
            db.commit()
            return {"completed": True, "question": None,
                    "progress": {"done": len(questions), "total": len(questions)}}

        q = remaining[0]
        profile.served_question_id, profile.served_mode, profile.served_is_verification = q.id, mode, False
        db.commit()
        return {"completed": False, "question": question_dict(q),
                "progress": {"done": len(attempted), "total": len(questions)}}

    # --- adaptive mode ---
    if profile.session_answered >= config.TEST_LENGTH:
        return {"completed": True, "question": None,
                "progress": {"done": profile.session_answered, "total": config.TEST_LENGTH},
                "session_complete": True}

    q, is_verification = choose_next_question(db, profile)
    if not q:
        return {"completed": True, "question": None, "progress": {"done": 0, "total": 0}}

    profile.served_question_id = q.id
    profile.served_mode = mode
    profile.served_is_verification = is_verification
    db.commit()

    return {
        "completed": False,
        "question": question_dict(q, is_verification),
        "progress": {"done": profile.session_answered, "total": config.TEST_LENGTH},
        "pending_action": profile.pending_action,
        "pending_reason": profile.pending_reason,
        "target_difficulty": round(profile.target_difficulty, 3),
    }


@router.post("/submit")
def submit(data: AnswerSubmission, user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        profile = ensure_profile(db, user.id)

        # The client can only submit the question the server actually served
        # for the declared mode -- prevents answer/ID mismatches and replay.
        if profile.served_question_id != data.question_id or profile.served_mode != data.mode:
            raise HTTPException(status_code=409, detail="This question is no longer active. Request a new one.")

        q = db.query(Question).filter(Question.id == data.question_id, Question.active == True).first()  # noqa: E712
        if not q:
            raise HTTPException(status_code=404, detail="Question not found")
        if data.mode == "pre_assessment" and not q.pre_assessment:
            raise HTTPException(status_code=400, detail="Question is not part of pre-assessment")
        if data.mode == "adaptive" and q.pre_assessment:
            raise HTTPException(status_code=400, detail="Question is not part of the adaptive test")

        selected = data.selected_answer.upper()
        correct = selected == q.correct_answer.upper()
        was_verification = bool(profile.served_is_verification)
        decision = decide(correct, data.confidence, was_verification)

        p_correct = ability_after = target_after = None

        if data.mode == "adaptive":
            b_t = normalise_difficulty(q.difficulty)
            theta_next, p_correct = update_ability(profile.overall_ability, b_t, correct)   # Eq. (2)
            profile.overall_ability = theta_next
            ability_after = theta_next

            target_after = next_target(profile.target_difficulty, decision)                 # Eq. (3)
            profile.target_difficulty = target_after

            if decision.verify:
                profile.pending_action = "verify"
                profile.pending_topic = q.topic
                profile.pending_subtopic = q.subtopic
                profile.pending_reason = decision.label
            else:
                profile.pending_action = "normal"
                profile.pending_topic = None
                profile.pending_subtopic = None
                profile.pending_reason = None

            profile.session_answered += 1

        attempt = Attempt(
            user_id=user.id, question_id=q.id, mode=data.mode,
            session_no=profile.session_no, is_verification=was_verification,
            selected_answer=selected, correct=correct,
            response_time=float(data.response_time), confidence=int(data.confidence),
            difficulty=q.difficulty, topic=q.topic, subtopic=q.subtopic,
            evaluation=decision.type, p_correct=p_correct,
            ability_after=ability_after, target_after=target_after,
        )
        db.add(attempt)

        topic = db.query(TopicPerformance).filter(
            TopicPerformance.user_id == user.id, TopicPerformance.topic == q.topic).first()
        if not topic:
            topic = TopicPerformance(user_id=user.id, topic=q.topic)
            db.add(topic)
            db.flush()
        topic.questions_attempted += 1
        if correct:
            topic.correct_answers += 1
        if decision.flag_topic:
            topic.flagged = True
        elif correct and data.mode == "adaptive":
            topic.flagged = False

        if data.mode == "pre_assessment":
            total_pre = db.query(Question).filter(
                Question.pre_assessment == True, Question.active == True).count()  # noqa: E712
            done_pre = db.query(Attempt).filter(
                Attempt.user_id == user.id, Attempt.mode == "pre_assessment").count() + 1
            if done_pre >= total_pre:
                profile.assessment_mode = "adaptive"

        session_complete = (
            data.mode == "adaptive" and profile.session_answered >= config.TEST_LENGTH
        )
        if session_complete:
            profile.session_no += 1
            profile.session_answered = 0

        profile.served_question_id = None
        profile.served_mode = None
        profile.served_is_verification = False

        db.commit()

        return {
            "correct": correct,
            "selected_answer": selected,
            "correct_answer": q.correct_answer,
            "confidence": data.confidence,
            "response_time": data.response_time,
            "evaluation": decision.as_dict(),
            "overall_ability": round(profile.overall_ability, 3),
            "target_difficulty": round(profile.target_difficulty, 3),
            "p_correct": round(p_correct, 3) if p_correct is not None else None,
            "next_action": decision.action,
            "next_reason": decision.label,
            "explanation": q.explanation,
            "session_complete": session_complete,
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500,
                             detail=f"Assessment submission error: {type(exc).__name__}: {exc}")
