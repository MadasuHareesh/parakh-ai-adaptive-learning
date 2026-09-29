import os
import secrets
import warnings

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = secrets.token_urlsafe(48)
    warnings.warn(
        "SECRET_KEY is not set; using an ephemeral key. Logins are lost on restart. "
        "Copy .env.example to .env for a persistent key."
    )

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./parakh.db")
CORS_ORIGINS = [o.strip() for o in os.getenv(
    "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480
PBKDF2_ITERATIONS = int(os.getenv("PBKDF2_ITERATIONS", "600000"))
PASSWORD_MIN_LENGTH = 6  # paper Sec. III-G

# ---- Adaptive model parameters (paper Sec. III-D to III-F) -------------------
TEST_LENGTH = int(os.getenv("TEST_LENGTH", "20"))    # adaptive questions per session
SLOPE_A = float(os.getenv("SLOPE_A", "4.0"))         # a in Eq. (1)
STEP_ETA = float(os.getenv("STEP_ETA", "0.15"))      # eta in Eq. (2)
DELTA = float(os.getenv("DELTA", "0.20"))            # delta in Eq. (3)
BAND_W = float(os.getenv("BAND_W", "0.15"))          # w, candidate band half-width
INITIAL_ABILITY = 0.5                                # neutral start (50 %)
HIGH_CONFIDENCE = 4                                  # ratings 4-5 are "high"
LOW_CONFIDENCE = 2                                   # ratings 1-2 are "low"
MAX_TOPIC_SHARE = 0.40                               # coverage rule
