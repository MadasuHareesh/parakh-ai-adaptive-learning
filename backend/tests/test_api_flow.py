"""End-to-end: login -> Level 0 -> adaptive loop, exercising the full API surface."""


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_login_rejects_bad_password(client):
    r = client.post("/api/auth/login", json={"email": "student@parakh.local", "password": "wrong"})
    assert r.status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code in (401, 403)


def test_me_with_token(client, student_token):
    r = client.get("/api/auth/me", headers=auth_header(student_token))
    assert r.status_code == 200
    assert r.json()["email"] == "student@parakh.local"


def test_full_pre_assessment_then_adaptive_session(client, student_token):
    h = auth_header(student_token)

    # drain pre-assessment
    seen = set()
    for _ in range(100):
        r = client.get("/api/assessment/next/pre_assessment", headers=h)
        assert r.status_code == 200
        body = r.json()
        if body["completed"]:
            break
        q = body["question"]
        assert q["id"] not in seen
        seen.add(q["id"])
        sub = client.post("/api/assessment/submit", json={
            "question_id": q["id"], "selected_answer": "A",
            "confidence": 3, "response_time": 5.0, "mode": "pre_assessment",
        }, headers=h)
        assert sub.status_code == 200, sub.text
    else:
        raise AssertionError("pre-assessment never completed")

    status = client.get("/api/assessment/status", headers=h).json()
    assert status["pre_assessment_complete"] is True
    assert status["mode"] == "adaptive"

    # run one full adaptive session (paper: 20 questions)
    abilities = []
    for i in range(status["session_length"]):
        r = client.get("/api/assessment/next/adaptive", headers=h)
        assert r.status_code == 200
        body = r.json()
        assert body["completed"] is False, f"session ended early at q{i}"
        q = body["question"]

        sub = client.post("/api/assessment/submit", json={
            "question_id": q["id"], "selected_answer": "A",
            "confidence": 5, "response_time": 4.0, "mode": "adaptive",
        }, headers=h)
        assert sub.status_code == 200, sub.text
        result = sub.json()
        assert 0.0 <= result["overall_ability"] <= 1.0
        assert 0.0 <= result["target_difficulty"] <= 1.0
        abilities.append(result["overall_ability"])

    assert result["session_complete"] is True  # signalled by the last submit in the session

    summary = client.get("/api/analytics/student", headers=h).json()
    assert summary["total_questions"] >= status["session_length"]
    assert 0 <= summary["accuracy"] <= 100


def test_cannot_submit_a_question_that_was_not_served(client, student_token):
    h = auth_header(student_token)
    client.get("/api/assessment/next/adaptive", headers=h)  # serve some question, ignore it
    r = client.post("/api/assessment/submit", json={
        "question_id": 999999, "selected_answer": "A",
        "confidence": 3, "response_time": 5.0, "mode": "adaptive",
    }, headers=h)
    assert r.status_code == 409


def test_verification_question_is_queued_after_confident_wrong_answer(client, admin_token):
    # Fresh student so the topic still has unanswered items left for the verification pool.
    h_admin = auth_header(admin_token)
    r = client.post("/api/admin/students", json={
        "name": "Verify Test", "email": "verify.test@parakh.local", "password": "abcdef"}, headers=h_admin)
    assert r.status_code == 200

    login = client.post("/api/auth/login", json={"email": "verify.test@parakh.local", "password": "abcdef"})
    h = auth_header(login.json()["access_token"])

    for _ in range(100):
        r = client.get("/api/assessment/next/pre_assessment", headers=h).json()
        if r["completed"]:
            break
        q = r["question"]
        client.post("/api/assessment/submit", json={
            "question_id": q["id"], "selected_answer": "A",
            "confidence": 3, "response_time": 5.0, "mode": "pre_assessment",
        }, headers=h)

    found_misconception = False
    for _ in range(15):  # try a handful of questions; guaranteed by pigeonhole given only 4 options
        r = client.get("/api/assessment/next/adaptive", headers=h).json()
        q = r["question"]
        sub = client.post("/api/assessment/submit", json={
            "question_id": q["id"], "selected_answer": "A",
            "confidence": 5, "response_time": 2.0, "mode": "adaptive",
        }, headers=h)
        result = sub.json()
        if not result["correct"]:
            assert result["evaluation"]["type"] == "misconception_detection"
            nxt = client.get("/api/assessment/next/adaptive", headers=h).json()
            assert nxt["question"]["is_verification"] is True
            found_misconception = True
            break

    assert found_misconception, "expected at least one incorrect answer in 15 tries"


def test_admin_endpoints(client, admin_token, student_token):
    h = auth_header(admin_token)
    assert client.get("/api/analytics/admin", headers=h).status_code == 200
    assert client.get("/api/questions", headers=h).status_code == 200
    students = client.get("/api/admin/students", headers=h).json()
    assert any(s["email"] == "student@parakh.local" for s in students)


def test_student_cannot_access_admin_routes(client, student_token):
    h = auth_header(student_token)
    assert client.get("/api/analytics/admin", headers=h).status_code == 403
    assert client.get("/api/admin/students", headers=h).status_code == 403


def test_admin_create_reset_delete_student(client, admin_token):
    h = auth_header(admin_token)
    r = client.post("/api/admin/students", json={
        "name": "New Kid", "email": "newkid@parakh.local", "password": "abcdef"}, headers=h)
    assert r.status_code == 200
    sid = r.json()["id"]

    r2 = client.post("/api/admin/students", json={
        "name": "New Kid", "email": "newkid@parakh.local", "password": "abcdef"}, headers=h)
    assert r2.status_code == 400  # duplicate email

    assert client.post(f"/api/admin/students/{sid}/reset", headers=h).status_code == 200
    assert client.delete(f"/api/admin/students/{sid}", headers=h).status_code == 200
    assert client.delete(f"/api/admin/students/{sid}", headers=h).status_code == 404


def test_password_too_short_rejected(client, admin_token):
    h = auth_header(admin_token)
    r = client.post("/api/admin/students", json={
        "name": "X", "email": "x@parakh.local", "password": "123"}, headers=h)
    assert r.status_code == 422
