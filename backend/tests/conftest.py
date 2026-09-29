import os
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import User, LearnerProfile
from app.security import hash_password
from app.question_bank import import_question_bank, CSV_PATH

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    student = User(name="Demo Student", email="student@parakh.local",
                    password_hash=hash_password("student123"), role="student")
    admin = User(name="Admin", email="admin@parakh.local",
                 password_hash=hash_password("admin123"), role="admin")
    db.add_all([student, admin])
    db.commit()
    db.refresh(student)
    db.add(LearnerProfile(user_id=student.id))
    db.commit()
    import_question_bank(db, CSV_PATH)
    db.close()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def student_token(client):
    r = client.post("/api/auth/login", json={"email": "student@parakh.local", "password": "student123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def admin_token(client):
    r = client.post("/api/auth/login", json={"email": "admin@parakh.local", "password": "admin123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]
