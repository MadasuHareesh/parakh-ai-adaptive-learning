import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .config import PASSWORD_MIN_LENGTH

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$|^[^@\s]+@[^@\s]+$")


class LoginRequest(BaseModel):
    email: str
    password: str


class CreateStudent(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(max_length=160)
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=128)

    @field_validator("email")
    @classmethod
    def _email(cls, v):
        v = v.strip().lower()
        if not _EMAIL.match(v):
            raise ValueError("Invalid email address")
        return v

    @field_validator("name")
    @classmethod
    def _name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Name is required")
        return v


class AnswerSubmission(BaseModel):
    question_id: int
    selected_answer: str = Field(pattern="^[A-Da-d]$")
    confidence: int = Field(ge=1, le=5)
    response_time: float = Field(gt=0, le=3600)
    mode: str = Field(pattern="^(pre_assessment|adaptive)$")


class AddQuestion(BaseModel):
    question_text: str = Field(min_length=3)
    option_a: str = Field(min_length=1)
    option_b: str = Field(min_length=1)
    option_c: str = Field(min_length=1)
    option_d: str = Field(min_length=1)
    correct_answer: str = Field(pattern="^[A-Da-d]$")
    topic: str = Field(min_length=1, max_length=100)
    subtopic: str = Field(min_length=1, max_length=100)
    difficulty: int = Field(ge=1, le=5)
    explanation: str = ""
    pre_assessment: bool = False

    @field_validator("correct_answer")
    @classmethod
    def _upper(cls, v):
        return v.upper()
