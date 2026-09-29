import math
from app.services.learner_model import prob_correct, update_ability, clip, calibration_gap, normalise_difficulty
from app.config import SLOPE_A, STEP_ETA


def test_normalise_difficulty_endpoints():
    assert normalise_difficulty(1) == 0.0
    assert normalise_difficulty(5) == 1.0
    assert normalise_difficulty(3) == 0.5


def test_prob_correct_at_ability_equals_difficulty():
    assert math.isclose(prob_correct(0.5, 0.5), 0.5, abs_tol=1e-9)


def test_prob_correct_monotonic_in_ability():
    assert prob_correct(0.8, 0.5) > prob_correct(0.5, 0.5) > prob_correct(0.2, 0.5)


def test_update_ability_correct_on_hard_item_raises_more_than_easy():
    theta = 0.5
    hard_next, _ = update_ability(theta, b=0.9, correct=True)
    easy_next, _ = update_ability(theta, b=0.1, correct=True)
    assert hard_next - theta > easy_next - theta


def test_update_ability_wrong_on_easy_item_lowers_more_than_hard():
    theta = 0.5
    easy_next, _ = update_ability(theta, b=0.1, correct=False)
    hard_next, _ = update_ability(theta, b=0.9, correct=False)
    assert theta - easy_next > theta - hard_next


def test_update_ability_stays_in_bounds():
    theta = 0.99
    for _ in range(50):
        theta, _ = update_ability(theta, b=0.0, correct=True)
    assert 0.0 <= theta <= 1.0


def test_clip():
    assert clip(1.5) == 1.0
    assert clip(-0.2) == 0.0
    assert clip(0.4) == 0.4


class FakeAttempt:
    def __init__(self, confidence, correct):
        self.confidence, self.correct = confidence, correct


def test_calibration_gap_overconfident():
    attempts = [FakeAttempt(5, False), FakeAttempt(5, False)]
    assert calibration_gap(attempts) > 0


def test_calibration_gap_empty():
    assert calibration_gap([]) == 0.0
