"""Create the demo accounts and (re)import the question bank. Run with `python -m app.seed`."""
from app.database import Base, engine, SessionLocal
from app.models import User, LearnerProfile
from app.security import hash_password
from app.question_bank import import_question_bank, CSV_PATH


def get_or_create_user(db, name, email, password, role):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(name=name, email=email, password_hash=hash_password(password), role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        student = get_or_create_user(db, "Demo Student", "student@parakh.local", "student123", "student")
        get_or_create_user(db, "PARAKH Admin", "admin@parakh.local", "admin123", "admin")

        if not db.query(LearnerProfile).filter(LearnerProfile.user_id == student.id).first():
            db.add(LearnerProfile(user_id=student.id))
            db.commit()

        n = import_question_bank(db, CSV_PATH)
        print(f"Seed complete. Imported {n} questions from {CSV_PATH}.")
        print("Student: student@parakh.local / student123")
        print("Admin:   admin@parakh.local / admin123")
        print("Change these credentials before any real deployment (paper Sec. V-E).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
