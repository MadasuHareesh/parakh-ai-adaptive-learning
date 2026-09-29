"""Ability estimation and calibration -- paper Sec. III-D, Eqs. (1), (2), (4)."""
import math

from .. import config


def clip(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def normalise_difficulty(level: int) -> float:
    """Instructor level 1..5 -> b on [0, 1]."""
    return (int(level) - 1) / 4.0


def prob_correct(theta: float, b: float, a: float = None) -> float:
    """Eq. (1): P_t = sigmoid(a (theta_t - b_t))."""
    a = config.SLOPE_A if a is None else a
    return 1.0 / (1.0 + math.exp(-a * (theta - b)))


def update_ability(theta: float, b: float, correct: bool, a: float = None, eta: float = None):
    """Eq. (2): theta_{t+1} = clip(theta_t + eta (x_t - P_t), 0, 1). Returns (theta_next, P_t)."""
    eta = config.STEP_ETA if eta is None else eta
    p = prob_correct(theta, b, a)
    return clip(theta + eta * ((1.0 if correct else 0.0) - p)), p


def calibration_gap(attempts) -> float:
    """Eq. (4): G = mean(kappa_t / 5 - x_t). Positive = overconfident."""
    attempts = list(attempts)
    if not attempts:
        return 0.0
    return sum(a.confidence / 5.0 - (1.0 if a.correct else 0.0) for a in attempts) / len(attempts)
