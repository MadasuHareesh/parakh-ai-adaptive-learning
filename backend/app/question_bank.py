"""Import / validate data/question_bank.csv (shared by seed.py and the tests)."""
import csv
from pathlib import Path

from .models import Question

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "data" / "question_bank.csv"


def import_question_bank(db, path: Path = CSV_PATH) -> int:
    count = 0
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            difficulty = int(row["difficulty"])
            answer = row["correct_answer"].strip().upper()
            if difficulty not in range(1, 6) or answer not in "ABCD" or len(answer) != 1:
                raise ValueError(f"Invalid question row id={row.get('id')}")
            values = dict(
                question_text=row["question_text"],
                option_a=row["option_a"], option_b=row["option_b"],
                option_c=row["option_c"], option_d=row["option_d"],
                correct_answer=answer, topic=row["topic"], subtopic=row["subtopic"],
                difficulty=difficulty, explanation=row.get("explanation", ""),
                pre_assessment=bool(int(row["pre_assessment"])), active=True,
            )
            q = db.query(Question).filter(Question.question_text == values["question_text"]).first()
            if q:
                for k, v in values.items():
                    setattr(q, k, v)
            else:
                db.add(Question(**values))
            count += 1
    db.commit()
    return count
