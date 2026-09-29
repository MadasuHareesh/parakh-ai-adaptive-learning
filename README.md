# PARAKH AI — Adaptive MCQ Assessment (final build)

Companion implementation for the paper *"Integration of AI for Adaptive
Learning for MCQ Selection in PARAKH."* This build implements the model as
specified in the paper — Eqs. (1)–(4), Table I/II, and the four-layer
architecture of Section III — and fixes the gaps found when the originally
submitted prototype was checked against that specification.

## What changed from the submitted prototype, and why

**Ability model now matches the paper, not an approximation of it.**
The prototype's `overall_ability` was an exponential moving average of raw
correctness (`0.70*theta + 0.30*correct`) with no link to item difficulty —
so a correct answer on an easy question moved ability exactly as much as one
on a hard question, which contradicts the paper's central claim in Sec.
III-D. `services/learner_model.py` now implements the actual Rasch/Elo
update:

```
P_t        = sigmoid(a * (theta_t - b_t))              Eq. (1)
theta_t+1  = clip(theta_t + eta * (x_t - P_t), 0, 1)    Eq. (2)
```

so a correct answer on a hard item now raises ability more than one on an
easy item (this is unit-tested in `tests/test_learner_model.py`).

**The confidence-aware decision policy is Table II, directly.**
`services/confidence_engine.py` replaces the prototype's `confidence_engine.py`
+ ad hoc difficulty math in the assessment router with a single function that
returns exactly the four Table II outcomes (raise / hold+verify / lower /
lower+flag+verify) plus the neutral (rating = 3) case the paper specifies,
and Eq. (3)'s clipped ±δ update. A verification question never itself queues
another verification, which the prototype didn't handle.

**The selector now follows Sec. III-F's five-step description**, not a
five-term linear score with hand-tuned weights (0.38/0.16/0.40/0.08/0.08/0.20)
that didn't correspond to anything in the paper and used a TF-IDF/logistic
"difficulty model" the paper never claims to use for selection (the paper
uses instructor-assigned difficulty; the ML classifier is out of scope for
v1 — see Sec. III-F). `services/adaptive_engine.py` now does: verification →
coverage rule → difficulty band around the target → weakest-topic
preference → random tie-break. The `ml/` folder and `difficulty_model.py`
were removed accordingly.

**Fixed real bugs in the prototype:**
- SHA-256 password hashing (no salt) → salted PBKDF2-HMAC-SHA256, `pbkdf2_sha256`.
- No login rate limiting → a small in-memory throttle (429 after repeated failures).
- No question-serve integrity check → the server now records which question
  it served and rejects a submission for anything else (`409`), closing an
  answer-spoofing/replay gap.
- `SECRET_KEY` defaulted to a fixed dev string → falls back to a random key
  with a warning, and `start_backend.sh` now generates a persistent one in
  `.env` if none exists.
- Admin dashboard had no way to create, reset or delete a student despite
  the paper describing all three (Sec. III-G) — added `POST/DELETE
  /api/admin/students*`.
- "Learning improvement" and "retention" always read 0% because nothing
  computed them across sessions — implemented as session-over-session
  accuracy change and re-asked-question retention respectively.
- Two question-bank items (`#59`, `#60`) were about the system itself
  ("why can an adaptive assessment use a trained difficulty model?") rather
  than course content, and two items had a difficulty label a reviewer would
  likely dispute; these were replaced/relabelled, and 10 genuinely
  difficulty-5/4 items were added so difficulty 4–5 isn't nearly empty
  (`data/question_bank.csv`, was 60 rows with only 1 in level 5, now 70 rows).
- Answer key was skewed B-heavy (33/60 = B) → repositioned so the correct
  option is close to evenly split across A/B/C/D.
- The 20-question adaptive session length from the paper's demonstration
  session (Table III) is now an actual server-side session boundary
  (`TEST_LENGTH`, default 20) rather than "keep serving forever."

**What was already right and is unchanged:** the four-layer separation
(application / AI engine / data / analytics), the React+FastAPI+SQLAlchemy
stack, the response record schema, and the two dashboards' layout.

## Verifying this build

```
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt pytest httpx
pytest -q
```

30 tests cover Eqs. (1)–(4) directly (`test_learner_model.py`), Table II
(`test_confidence_engine.py`), the question bank's internal consistency
(`test_question_bank.py`), and the full login → Level 0 → 20-question
adaptive session → analytics flow against a real FastAPI app
(`test_api_flow.py`), including the answer-integrity check, admin student
CRUD, and role-based access control.

## Running it

```
./start_backend.sh    # creates venv, installs deps, generates .env, seeds, serves on :8000
./start_frontend.sh   # npm install + vite dev server on :5173
```

Demo accounts (paper Sec. V-E: remove before any real deployment):
`student@parakh.local` / `student123`, `admin@parakh.local` / `admin123`.

## Structure

```
backend/app/
  services/
    learner_model.py       Eqs. (1)(2)(4): ability, P_t, calibration gap
    confidence_engine.py   Table II + Eq. (3): decision policy
    adaptive_engine.py     Sec. III-F: five-step selector
    analytics_engine.py    dashboard figures, all derived from Attempt rows
  routers/
    auth.py  assessment.py  analytics.py  questions.py  admin.py
  models.py / schemas.py / question_bank.py / seed.py / security.py / config.py
backend/tests/            30 tests (unit + full API flow)
data/question_bank.csv    70 MCQs, 6 topics, difficulty 1-5, balanced answer keys
frontend/src/              React 19 + Vite, unchanged layout, updated to the new API
```
