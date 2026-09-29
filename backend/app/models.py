from datetime import datetime

from sqlalchemy import (Column, Integer, String, Float, Boolean, DateTime,
                        ForeignKey, Text, UniqueConstraint)

from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="student", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_answer = Column(String(1), nullable=False)
    topic = Column(String(100), nullable=False)
    subtopic = Column(String(100), nullable=False)
    difficulty = Column(Integer, nullable=False)  # instructor level 1-5
    explanation = Column(Text, default="")
    pre_assessment = Column(Boolean, default=False)
    active = Column(Boolean, default=True)


class LearnerProfile(Base):
    """Running state of one student. Everything else is derived from Attempt rows."""
    __tablename__ = "learner_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    overall_ability = Column(Float, default=0.5)      # theta_t on [0, 1]
    target_difficulty = Column(Float, default=0.5)    # b_{t+1} on [0, 1]
    assessment_mode = Column(String(30), default="pre_assessment")
    session_no = Column(Integer, default=0)           # 0 = still in Level 0
    session_answered = Column(Integer, default=0)
    # question currently served (integrity + stable reload)
    served_question_id = Column(Integer, nullable=True)
    served_mode = Column(String(30), nullable=True)
    served_is_verification = Column(Boolean, default=False)
    # queued verification
    pending_action = Column(String(30), default="normal")
    pending_topic = Column(String(100), nullable=True)
    pending_subtopic = Column(String(100), nullable=True)
    pending_reason = Column(String(120), nullable=True)


class TopicPerformance(Base):
    __tablename__ = "topic_performance"
    __table_args__ = (UniqueConstraint("user_id", "topic", name="uq_user_topic"),)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic = Column(String(100), nullable=False)
    questions_attempted = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    flagged = Column(Boolean, default=False)          # possible misconception


class Attempt(Base):
    """Response record r_t = (q_t, k_t, b_t, x_t, kappa_t, tau_t) plus trace fields."""
    __tablename__ = "attempts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question_id = Column(Integer, nullable=False)
    mode = Column(String(30), nullable=False)          # pre_assessment | adaptive
    session_no = Column(Integer, default=0)
    is_verification = Column(Boolean, default=False)
    selected_answer = Column(String(1), nullable=False)
    correct = Column(Boolean, nullable=False)           # x_t
    response_time = Column(Float, nullable=False)       # tau_t (s)
    confidence = Column(Integer, nullable=False)        # kappa_t
    difficulty = Column(Integer, nullable=False)        # level 1-5 (b_t = (d-1)/4)
    topic = Column(String(100), nullable=False)         # k_t
    subtopic = Column(String(100), nullable=False)
    evaluation = Column(String(50), nullable=False)
    p_correct = Column(Float, nullable=True)            # P_t from Eq. (1)
    ability_after = Column(Float, nullable=True)        # theta_{t+1} from Eq. (2)
    target_after = Column(Float, nullable=True)         # b_{t+1} from Eq. (3)
    timestamp = Column(DateTime, default=datetime.utcnow)
