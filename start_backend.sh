#!/bin/bash
set -e
cd "$(dirname "$0")/backend"

if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  # Generate a real random secret instead of the placeholder.
  python3 - <<'PY'
import re, secrets
p = ".env"
s = open(p).read()
s = re.sub(r"^SECRET_KEY=.*$", f"SECRET_KEY={secrets.token_urlsafe(48)}", s, flags=re.M)
open(p, "w").write(s)
PY
fi

python -m app.seed
uvicorn app.main:app --reload
