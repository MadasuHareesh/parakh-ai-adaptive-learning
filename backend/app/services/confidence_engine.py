"""Confidence-aware decision policy -- paper Table II and Eq. (3)."""
from dataclasses import dataclass, asdict

from .. import config
from .learner_model import clip


@dataclass
class Decision:
    type: str            # evaluation code stored with the attempt
    label: str
    message: str
    action: str          # raise | hold | lower
    verify: bool         # queue a verification question
    flag_topic: bool     # possible misconception

    def as_dict(self):
        return asdict(self)


def decide(correct: bool, confidence: int, was_verification: bool = False) -> Decision:
    """Map (correctness, confidence) to a difficulty move.

    Ratings 4-5 are high, 1-2 low; 3 is neutral and follows correctness alone.
    A verification question never queues another verification (no chains).
    """
    high = confidence >= config.HIGH_CONFIDENCE
    low = confidence <= config.LOW_CONFIDENCE

    if correct and high:
        d = Decision("strong_understanding", "Strong Understanding",
                     "Correct and confident. Difficulty will increase.", "raise", False, False)
    elif correct and low:
        d = Decision("fluke_detection", "Possible Fluke",
                     "Correct but unsure - could be a guess or fragile knowledge. "
                     "Difficulty is held and a verification question is queued.", "hold", True, False)
    elif (not correct) and low:
        d = Decision("low_confidence_error", "Known Gap",
                     "Incorrect and unsure. An easier question will follow.", "lower", False, False)
    elif (not correct) and high:
        d = Decision("misconception_detection", "Possible Misconception",
                     "Incorrect but confident. Difficulty is lowered, the topic is flagged "
                     "and a verification question is queued.", "lower", True, True)
    elif correct:  # rating 3
        d = Decision("neutral_correct", "Correct",
                     "Correct with a neutral rating. Difficulty will increase.", "raise", False, False)
    else:
        d = Decision("neutral_incorrect", "Incorrect",
                     "Incorrect with a neutral rating. An easier question will follow.", "lower", False, False)

    if was_verification and d.verify:
        d.verify = False
    return d


def next_target(b_current: float, decision: Decision, delta: float = None) -> float:
    """Eq. (3): b_{t+1} = clip(b_t + Delta_t, 0, 1), Delta_t in {+delta, 0, -delta}."""
    delta = config.DELTA if delta is None else delta
    step = {"raise": delta, "hold": 0.0, "lower": -delta}[decision.action]
    return clip(b_current + step)
