from app.services.confidence_engine import decide, next_target


def test_table_ii_correct_high():
    d = decide(True, 5)
    assert d.action == "raise" and not d.verify


def test_table_ii_correct_low():
    d = decide(True, 1)
    assert d.action == "hold" and d.verify


def test_table_ii_incorrect_low():
    d = decide(False, 2)
    assert d.action == "lower" and not d.verify


def test_table_ii_incorrect_high():
    d = decide(False, 4)
    assert d.action == "lower" and d.verify and d.flag_topic


def test_neutral_rating_follows_correctness():
    assert decide(True, 3).action == "raise"
    assert decide(False, 3).action == "lower"


def test_verification_never_chains():
    d = decide(True, 1, was_verification=True)
    assert d.verify is False


def test_next_target_moves_by_delta():
    d = decide(True, 5)
    assert next_target(0.5, d) > 0.5
    d2 = decide(False, 5)
    assert next_target(0.5, d2) < 0.5
    d3 = decide(True, 1)
    assert next_target(0.5, d3) == 0.5


def test_next_target_clips():
    d = decide(True, 5)
    assert next_target(0.95, d, delta=0.2) == 1.0
