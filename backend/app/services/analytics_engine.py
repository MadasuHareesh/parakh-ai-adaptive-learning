"""Everything the dashboards show is computed from stored response records."""
from collections import defaultdict

from ..models import Attempt, TopicPerformance, LearnerProfile
from .learner_model import calibration_gap


def _acc(rows):
    return sum(1 for a in rows if a.correct) / len(rows) if rows else 0.0


def learning_improvement(attempts) -> float:
    """Accuracy of the latest adaptive session minus the previous one (pct points).
    Needs two sessions with responses, so it stays 0 after a single session."""
    by_session = defaultdict(list)
    for a in attempts:
        if a.mode == "adaptive":
            by_session[a.session_no].append(a)
    sessions = sorted(by_session)
    if len(sessions) < 2:
        return 0.0
    return round((_acc(by_session[sessions[-1]]) - _acc(by_session[sessions[-2]])) * 100, 2)


def retention_score(attempts) -> float:
    """Of the questions answered correctly in an earlier session and re-asked in a
    later one, the share answered correctly again (pct). 0 if nothing was re-asked."""
    history = defaultdict(list)
    for a in sorted(attempts, key=lambda x: (x.timestamp, x.id)):
        if a.mode == "adaptive":
            history[a.question_id].append(a)
    kept = total = 0
    for rows in history.values():
        for i, later in enumerate(rows):
            earlier_correct = any(e.correct and e.session_no < later.session_no for e in rows[:i])
            if earlier_correct:
                total += 1
                kept += 1 if later.correct else 0
    return round(kept / total * 100, 2) if total else 0.0


def student_summary(db, user_id):
    attempts = db.query(Attempt).filter(Attempt.user_id == user_id).order_by(Attempt.id).all()
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    topic_rows = db.query(TopicPerformance).filter(TopicPerformance.user_id == user_id).all()

    n = len(attempts)
    correct = sum(1 for a in attempts if a.correct)
    dist = {str(i): 0 for i in range(1, 6)}
    for a in attempts:
        dist[str(a.confidence)] += 1

    return {
        "total_questions": n,
        "correct_answers": correct,
        "accuracy": round(correct / n * 100, 1) if n else 0,
        "overall_ability": round((profile.overall_ability if profile else 0.5) * 100, 1),
        "average_confidence": round(sum(a.confidence for a in attempts) / n, 2) if n else 0,
        "average_response_time": round(sum(a.response_time for a in attempts) / n, 2) if n else 0,
        "verification_questions": sum(1 for a in attempts if a.is_verification),
        "learning_improvement": learning_improvement(attempts),
        "retention_score": retention_score(attempts),
        "calibration_gap": round(calibration_gap(attempts), 3),
        "confidence_distribution": dist,
        "session": {
            "number": profile.session_no if profile else 0,
            "answered": profile.session_answered if profile else 0,
        },
        "topics": [
            {
                "topic": r.topic,
                "accuracy": round(r.correct_answers / r.questions_attempted * 100, 1)
                if r.questions_attempted else 0,
                "attempted": r.questions_attempted,
                "correct": r.correct_answers,
                "flagged": bool(r.flagged),
            }
            for r in sorted(topic_rows, key=lambda r: r.topic)
        ],
    }
