import csv
from app.question_bank import CSV_PATH


def test_csv_loads_and_is_consistent():
    rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8-sig")))
    assert len(rows) >= 60
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate question ids"

    for r in rows:
        assert 1 <= int(r["difficulty"]) <= 5
        assert r["correct_answer"].upper() in "ABCD"
        opts = {r["option_a"], r["option_b"], r["option_c"], r["option_d"]}
        assert len(opts) == 4, f"duplicate options in id={r['id']}"
        assert r["pre_assessment"] in {"0", "1"}


def test_answer_letters_are_reasonably_balanced():
    rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8-sig")))
    from collections import Counter
    counts = Counter(r["correct_answer"].upper() for r in rows)
    assert max(counts.values()) - min(counts.values()) <= len(rows) * 0.15


def test_every_topic_has_pre_assessment_items():
    rows = list(csv.DictReader(open(CSV_PATH, encoding="utf-8-sig")))
    topics = {r["topic"] for r in rows}
    pre_topics = {r["topic"] for r in rows if r["pre_assessment"] == "1"}
    assert topics == pre_topics
