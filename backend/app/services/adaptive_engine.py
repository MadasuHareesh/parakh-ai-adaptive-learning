"""Rule-based question selector -- paper Sec. III-F.

Order of operations
  1. Verification queued?  -> same topic (prefer subtopic), difficulty nearest b_{t+1}.
  2. Coverage rule         -> unseen topics first; no topic above MAX_TOPIC_SHARE.
  3. Candidate band        -> unanswered items with |b_q - b_{t+1}| <= w (widened if empty).
  4. Preference            -> topic with the lowest (smoothed) accuracy.
  5. Random tie-breaks     -> so different students do not always see the same items.
"""
import random
from collections import Counter

from sqlalchemy.orm import Session

from .. import config
from ..models import Question, Attempt, TopicPerformance
from .learner_model import normalise_difficulty


def _band(pool, b, w=None):
    w = config.BAND_W if w is None else w
    while True:
        cand = [q for q in pool if abs(normalise_difficulty(q.difficulty) - b) <= w + 1e-9]
        if cand or w >= 1.0:
            return cand or list(pool)
        w += 0.10


def _nearest(pool, b, rng):
    best = min(abs(normalise_difficulty(q.difficulty) - b) for q in pool)
    return rng.choice([q for q in pool
                       if abs(abs(normalise_difficulty(q.difficulty) - b) - best) < 1e-9])


def choose_next_question(db: Session, profile, rng: random.Random = None):
    """Return (question | None, is_verification)."""
    rng = rng or random.Random()
    b = profile.target_difficulty

    adaptive_qs = db.query(Question).filter(
        Question.active == True, Question.pre_assessment == False).all()   # noqa: E712
    attempts = db.query(Attempt).filter(
        Attempt.user_id == profile.user_id, Attempt.mode == "adaptive").all()

    seen_ever = {a.question_id for a in attempts}
    seen_session = {a.question_id for a in attempts if a.session_no == profile.session_no}

    pool = [q for q in adaptive_qs if q.id not in seen_ever]
    if not pool:                                    # bank exhausted: recycle within reason
        pool = [q for q in adaptive_qs if q.id not in seen_session]
    if not pool:
        return None, False

    # 1. verification
    if profile.pending_action == "verify" and profile.pending_topic:
        same_topic = [q for q in pool if q.topic == profile.pending_topic]
        same_sub = [q for q in same_topic if q.subtopic == profile.pending_subtopic]
        cand = same_sub or same_topic
        if cand:
            return _nearest(_band(cand, b), b, rng), True
        # nothing left on that topic: fall through to a normal selection

    # 2. coverage rule
    session_attempts = [a for a in attempts if a.session_no == profile.session_no]
    n_sess = len(session_attempts)
    sess_topics = Counter(a.topic for a in session_attempts)
    topics_in_pool = {q.topic for q in pool}

    eligible = {t for t in topics_in_pool
                if n_sess < 5 or sess_topics[t] / n_sess <= config.MAX_TOPIC_SHARE}
    if not eligible:
        eligible = topics_in_pool
    unseen = {t for t in eligible if sess_topics[t] == 0}
    if unseen:
        eligible = unseen
    pool = [q for q in pool if q.topic in eligible]

    # 3. candidate band
    cand = _band(pool, b)

    # 4. topic preference: lowest Laplace-smoothed accuracy
    stats = {r.topic: r for r in db.query(TopicPerformance).filter(
        TopicPerformance.user_id == profile.user_id).all()}

    def acc(topic):
        r = stats.get(topic)
        return ((r.correct_answers if r else 0) + 1) / ((r.questions_attempted if r else 0) + 2)

    topics = {q.topic for q in cand}
    lowest = min(acc(t) for t in topics)
    chosen_topic = rng.choice(sorted(t for t in topics if acc(t) - lowest <= 0.05))

    # 5. closest to target, random among equals
    return _nearest([q for q in cand if q.topic == chosen_topic], b, rng), False
