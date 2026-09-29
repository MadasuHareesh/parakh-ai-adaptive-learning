import { useEffect, useMemo, useState } from "react";

import {
  addQuestion,
  createStudent,
  deleteQuestion,
  deleteStudent,
  getAdminAnalytics,
  getQuestions,
  getStudents,
  resetStudent,
} from "../services/api";

const initialQuestion = {
  question_text: "",
  option_a: "",
  option_b: "",
  option_c: "",
  option_d: "",
  correct_answer: "A",
  topic: "Programming",
  subtopic: "General",
  difficulty: 3,
  explanation: "",
  pre_assessment: false,
};

const initialStudent = {
  name: "",
  email: "",
  password: "",
};

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [students, setStudents] = useState([]);

  const [form, setForm] = useState(initialQuestion);
  const [studentForm, setStudentForm] = useState(initialStudent);

  const [studentError, setStudentError] = useState("");
  const [questionError, setQuestionError] = useState("");

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const [studentSearch, setStudentSearch] = useState("");
  const [studentFilter, setStudentFilter] = useState("all");

  const [questionSearch, setQuestionSearch] = useState("");
  const [questionFilter, setQuestionFilter] = useState("all");

  const [selectedStudent, setSelectedStudent] = useState(null);

  async function load(showRefresh = false) {
    try {
      if (showRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const [s, q, st] = await Promise.all([
        getAdminAnalytics(),
        getQuestions(),
        getStudents(),
      ]);

      setStats(s.data);
      setQuestions(q.data || []);
      setStudents(st.data || []);
    } catch (err) {
      console.error("Admin dashboard loading error:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  // --------------------------------------------------
  // QUESTION FORM
  // --------------------------------------------------

  function changeQuestion(e) {
    const { name, value, type, checked } = e.target;

    setForm((current) => ({
      ...current,
      [name]:
        type === "checkbox"
          ? checked
          : name === "difficulty"
          ? Number(value)
          : name === "correct_answer"
          ? value.toUpperCase()
          : value,
    }));
  }

  async function submitQuestion(e) {
    e.preventDefault();
    setQuestionError("");

    try {
      await addQuestion(form);

      setForm(initialQuestion);

      await load(true);
    } catch (err) {
      console.error(err);

      setQuestionError(
        err?.response?.data?.detail ||
          "Could not create the question. Please check the entered data."
      );
    }
  }

  async function removeQuestion(id) {
    const confirmed = window.confirm(
      "Disable this question? It will no longer be available for assessments."
    );

    if (!confirmed) return;

    try {
      await deleteQuestion(id);
      await load(true);
    } catch (err) {
      alert(
        err?.response?.data?.detail ||
          "Could not disable this question."
      );
    }
  }

  // --------------------------------------------------
  // STUDENT FORM
  // --------------------------------------------------

  function changeStudent(e) {
    setStudentForm((current) => ({
      ...current,
      [e.target.name]: e.target.value,
    }));
  }

  async function submitStudent(e) {
    e.preventDefault();

    setStudentError("");

    try {
      await createStudent(studentForm);

      setStudentForm(initialStudent);

      await load(true);
    } catch (err) {
      console.error(err);

      setStudentError(
        err?.response?.data?.detail ||
          "Could not create student account."
      );
    }
  }

  // --------------------------------------------------
  // STUDENT ACTIONS
  // --------------------------------------------------

  async function handleReset(id) {
    const confirmed = window.confirm(
      "Reset this student's assessment?\n\nAll assessment attempts will be cleared."
    );

    if (!confirmed) return;

    try {
      await resetStudent(id);

      setSelectedStudent(null);

      await load(true);
    } catch (err) {
      alert(
        err?.response?.data?.detail ||
          "Could not reset this student."
      );
    }
  }

  async function handleDelete(id) {
    const confirmed = window.confirm(
      "Delete this student permanently?\n\nThis action cannot be undone."
    );

    if (!confirmed) return;

    try {
      await deleteStudent(id);

      setSelectedStudent(null);

      await load(true);
    } catch (err) {
      alert(
        err?.response?.data?.detail ||
          "Could not delete this student."
      );
    }
  }

  // --------------------------------------------------
  // FILTER STUDENTS
  // --------------------------------------------------

  const filteredStudents = useMemo(() => {
    const search = studentSearch.toLowerCase().trim();

    return students.filter((student) => {
      const matchesSearch =
        !search ||
        student.name?.toLowerCase().includes(search) ||
        student.email?.toLowerCase().includes(search);

      let matchesFilter = true;

      if (studentFilter === "attempted") {
        matchesFilter = Number(student.attempts || 0) > 0;
      }

      if (studentFilter === "not_started") {
        matchesFilter =
          Number(student.attempts || 0) === 0;
      }

      if (studentFilter === "high") {
        matchesFilter = Number(student.accuracy || 0) >= 70;
      }

      if (studentFilter === "needs_attention") {
        matchesFilter = Number(student.accuracy || 0) < 50;
      }

      return matchesSearch && matchesFilter;
    });
  }, [students, studentSearch, studentFilter]);

  // --------------------------------------------------
  // FILTER QUESTIONS
  // --------------------------------------------------

  const filteredQuestions = useMemo(() => {
    const search = questionSearch.toLowerCase().trim();

    return questions.filter((question) => {
      const matchesSearch =
        !search ||
        question.question_text
          ?.toLowerCase()
          .includes(search) ||
        question.topic
          ?.toLowerCase()
          .includes(search) ||
        question.subtopic
          ?.toLowerCase()
          .includes(search);

      let matchesFilter = true;

      if (questionFilter === "pre") {
        matchesFilter = question.pre_assessment === true;
      }

      if (questionFilter === "adaptive") {
        matchesFilter = question.pre_assessment !== true;
      }

      if (questionFilter === "active") {
        matchesFilter = question.active !== false;
      }

      if (questionFilter === "disabled") {
        matchesFilter = question.active === false;
      }

      return matchesSearch && matchesFilter;
    });
  }, [questions, questionSearch, questionFilter]);

  // --------------------------------------------------
  // EXPORT CSV
  // --------------------------------------------------

  function exportStudents() {
    if (!students.length) {
      alert("There are no students to export.");
      return;
    }

    const header = [
      "Name",
      "Email",
      "Attempts",
      "Accuracy",
      "Ability",
      "Status",
    ];

    const rows = students.map((student) => [
      student.name || "",
      student.email || "",
      student.attempts || 0,
      `${student.accuracy || 0}%`,
      `${student.ability || 0}%`,
      student.status || "Not Started",
    ]);

    const csv = [
      header,
      ...rows,
    ]
      .map((row) =>
        row
          .map((value) =>
            `"${String(value).replace(/"/g, '""')}"`
          )
          .join(",")
      )
      .join("\n");

    const blob = new Blob([csv], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");

    link.href = url;
    link.download = "parakh_student_performance.csv";

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
  }

  // --------------------------------------------------
  // LOADING
  // --------------------------------------------------

  if (loading) {
    return (
      <div className="loading">
        Loading PARAKH AI Admin Dashboard...
      </div>
    );
  }

  // --------------------------------------------------
  // DASHBOARD
  // --------------------------------------------------

  return (
    <div className="page">

      {/* HEADER */}
      <div className="hero compact">
        <div>
          <div className="eyebrow">
            ADMIN CONTROL CENTER
          </div>

          <h1>Admin Dashboard</h1>

          <p>
            Monitor student performance, manage assessments,
            create questions, and control student accounts.
          </p>
        </div>

        <div className="admin-header-actions">
          <button
            className="ghost-btn"
            onClick={() => load(true)}
            disabled={refreshing}
          >
            {refreshing ? "Refreshing..." : "↻ Refresh"}
          </button>

          <button
            className="primary-btn"
            onClick={exportStudents}
          >
            ↓ Export Report
          </button>
        </div>
      </div>

      {/* SUMMARY CARDS */}
      <div className="stat-grid">

        <div className="stat-card">
          <span>Total Students</span>
          <strong>
            {stats?.students ?? students.length}
          </strong>
          <small>Registered accounts</small>
        </div>

        <div className="stat-card">
          <span>Students Attempted</span>
          <strong>
            {students.filter(
              (s) => Number(s.attempts || 0) > 0
            ).length}
          </strong>
          <small>Assessment started</small>
        </div>

        <div className="stat-card">
          <span>Not Started</span>
          <strong>
            {stats?.students_not_started ??
              students.filter(
                (s) => Number(s.attempts || 0) === 0
              ).length}
          </strong>
          <small>Awaiting assessment</small>
        </div>

        <div className="stat-card">
          <span>Average Accuracy</span>
          <strong>
            {stats?.accuracy ?? 0}%
          </strong>
          <small>Across assessments</small>
        </div>

        <div className="stat-card">
          <span>Question Bank</span>
          <strong>
            {stats?.questions ?? questions.length}
          </strong>
          <small>Total MCQs</small>
        </div>

        <div className="stat-card">
          <span>Active Questions</span>
          <strong>
            {
              questions.filter(
                (q) => q.active !== false
              ).length
            }
          </strong>
          <small>Available for students</small>
        </div>
      </div>

      {/* PERFORMANCE OVERVIEW */}
      <section className="panel">

        <div className="section-header">
          <div>
            <div className="eyebrow">
              PERFORMANCE OVERVIEW
            </div>

            <h2>Student Performance</h2>

            <p className="muted">
              Monitor attempts, accuracy, ability level,
              and assessment status.
            </p>
          </div>

          <button
            className="ghost-btn"
            onClick={exportStudents}
          >
            Export CSV
          </button>
        </div>

        {/* SEARCH + FILTER */}
        <div className="admin-toolbar">

          <input
            className="search-input"
            placeholder="🔎 Search student by name or email..."
            value={studentSearch}
            onChange={(e) =>
              setStudentSearch(e.target.value)
            }
          />

          <select
            value={studentFilter}
            onChange={(e) =>
              setStudentFilter(e.target.value)
            }
          >
            <option value="all">All Students</option>
            <option value="attempted">Attempted</option>
            <option value="not_started">
              Not Started
            </option>
            <option value="high">
              Accuracy ≥ 70%
            </option>
            <option value="needs_attention">
              Needs Attention
            </option>
          </select>
        </div>

        {/* STUDENT TABLE */}
        <div className="table-wrapper">

          <table className="admin-table">

            <thead>
              <tr>
                <th>STUDENT</th>
                <th>ATTEMPTS</th>
                <th>ACCURACY</th>
                <th>ABILITY</th>
                <th>STATUS</th>
                <th>ACTIONS</th>
              </tr>
            </thead>

            <tbody>

              {filteredStudents.map((student) => {

                const accuracy =
                  Number(student.accuracy || 0);

                return (
                  <tr key={student.id}>

                    <td>
                      <div className="student-name">
                        {student.name}
                      </div>

                      <div className="student-email">
                        {student.email}
                      </div>
                    </td>

                    <td>
                      <strong>
                        {student.attempts || 0}
                      </strong>
                    </td>

                    <td>
                      <div className="performance-cell">

                        <strong>
                          {accuracy}%
                        </strong>

                        <div className="progress-track">
                          <div
                            className="progress-fill"
                            style={{
                              width: `${Math.min(
                                accuracy,
                                100
                              )}%`,
                            }}
                          />
                        </div>

                      </div>
                    </td>

                    <td>
                      <span className="ability-badge">
                        {student.ability ?? 50}%
                      </span>
                    </td>

                    <td>

                      <span
                        className={
                          student.status ===
                          "Completed"
                            ? "status-badge completed"
                            : student.status ===
                              "In Progress"
                            ? "status-badge progress"
                            : "status-badge pending"
                        }
                      >
                        {student.status ||
                          "Not Started"}
                      </span>

                    </td>

                    <td>

                      <div className="row-actions">

                        <button
                          className="ghost-btn"
                          onClick={() =>
                            setSelectedStudent(student)
                          }
                        >
                          View
                        </button>

                        <button
                          className="ghost-btn"
                          onClick={() =>
                            handleReset(student.id)
                          }
                        >
                          Reset
                        </button>

                        <button
                          className="danger-btn"
                          onClick={() =>
                            handleDelete(student.id)
                          }
                        >
                          Delete
                        </button>

                      </div>

                    </td>

                  </tr>
                );
              })}

            </tbody>

          </table>

          {filteredStudents.length === 0 && (
            <div className="empty-state">
              No students match the selected filter.
            </div>
          )}

        </div>

      </section>

      {/* CREATE STUDENT + QUESTION CREATOR */}
      <div className="two-column">

        {/* CREATE STUDENT */}
        <section className="panel">

          <div className="eyebrow">
            STUDENT MANAGEMENT
          </div>

          <h2>Create Student Account</h2>

          <p className="muted">
            Create an account that students can use to
            access their adaptive assessment.
          </p>

          <form
            className="question-form"
            onSubmit={submitStudent}
          >

            <input
              name="name"
              placeholder="Full name"
              value={studentForm.name}
              onChange={changeStudent}
              required
            />

            <input
              name="email"
              type="email"
              placeholder="Email address"
              value={studentForm.email}
              onChange={changeStudent}
              required
            />

            <input
              name="password"
              type="password"
              placeholder="Password (minimum 6 characters)"
              value={studentForm.password}
              onChange={changeStudent}
              required
              minLength={6}
            />

            {studentError && (
              <div className="error">
                {studentError}
              </div>
            )}

            <button
              className="primary-btn"
              type="submit"
            >
              + Create Student
            </button>

          </form>

        </section>

        {/* QUESTION CREATOR */}
        <section className="panel">

          <div className="eyebrow">
            QUESTION CREATOR
          </div>

          <h2>Add New MCQ</h2>

          <p className="muted">
            Add questions to the adaptive assessment
            question bank.
          </p>

          <form
            className="question-form"
            onSubmit={submitQuestion}
          >

            <textarea
              name="question_text"
              placeholder="Enter question"
              value={form.question_text}
              onChange={changeQuestion}
              required
            />

            <input
              name="option_a"
              placeholder="Option A"
              value={form.option_a}
              onChange={changeQuestion}
              required
            />

            <input
              name="option_b"
              placeholder="Option B"
              value={form.option_b}
              onChange={changeQuestion}
              required
            />

            <input
              name="option_c"
              placeholder="Option C"
              value={form.option_c}
              onChange={changeQuestion}
              required
            />

            <input
              name="option_d"
              placeholder="Option D"
              value={form.option_d}
              onChange={changeQuestion}
              required
            />

            <div className="form-row">

              <select
                name="correct_answer"
                value={form.correct_answer}
                onChange={changeQuestion}
                required
              >
                <option value="A">
                  Correct Answer: A
                </option>

                <option value="B">
                  Correct Answer: B
                </option>

                <option value="C">
                  Correct Answer: C
                </option>

                <option value="D">
                  Correct Answer: D
                </option>
              </select>

              <select
                name="difficulty"
                value={form.difficulty}
                onChange={changeQuestion}
              >
                <option value={1}>
                  Difficulty 1 — Easy
                </option>

                <option value={2}>
                  Difficulty 2
                </option>

                <option value={3}>
                  Difficulty 3 — Medium
                </option>

                <option value={4}>
                  Difficulty 4
                </option>

                <option value={5}>
                  Difficulty 5 — Hard
                </option>
              </select>

            </div>

            <div className="form-row">

              <input
                name="topic"
                placeholder="Topic"
                value={form.topic}
                onChange={changeQuestion}
                required
              />

              <input
                name="subtopic"
                placeholder="Subtopic"
                value={form.subtopic}
                onChange={changeQuestion}
                required
              />

            </div>

            <textarea
              name="explanation"
              placeholder="Answer explanation"
              value={form.explanation}
              onChange={changeQuestion}
            />

            <label className="check">

              <input
                type="checkbox"
                name="pre_assessment"
                checked={form.pre_assessment}
                onChange={changeQuestion}
              />

              Include in Level 0 Pre-Assessment

            </label>

            {questionError && (
              <div className="error">
                {questionError}
              </div>
            )}

            <button
              className="primary-btn"
              type="submit"
            >
              + Create Question
            </button>

          </form>

        </section>

      </div>

      {/* QUESTION BANK */}
      <section className="panel">

        <div className="section-header">

          <div>

            <div className="eyebrow">
              QUESTION BANK
            </div>

            <h2>
              {questions.length} Questions
            </h2>

            <p className="muted">
              Manage the questions used by the
              assessment engine.
            </p>

          </div>

        </div>

        {/* QUESTION SEARCH */}
        <div className="admin-toolbar">

          <input
            className="search-input"
            placeholder="🔎 Search questions, topics..."
            value={questionSearch}
            onChange={(e) =>
              setQuestionSearch(e.target.value)
            }
          />

          <select
            value={questionFilter}
            onChange={(e) =>
              setQuestionFilter(e.target.value)
            }
          >
            <option value="all">
              All Questions
            </option>

            <option value="active">
              Active
            </option>

            <option value="disabled">
              Disabled
            </option>

            <option value="pre">
              Pre-Assessment
            </option>

            <option value="adaptive">
              Adaptive
            </option>
          </select>

        </div>

        <div className="question-list">

          {filteredQuestions.map((question) => (

            <div
              className="question-row"
              key={question.id}
            >

              <div>

                <b>
                  #{question.id}{" "}
                  {question.question_text}
                </b>

                <small>
                  {question.topic} •{" "}
                  {question.subtopic} • Difficulty{" "}
                  {question.difficulty} •{" "}

                  {question.pre_assessment
                    ? "Level 0 Pre-Assessment"
                    : "Adaptive"}

                  {!question.active &&
                    " • Disabled"}
                </small>

              </div>

              <div className="row-actions">

                {question.active !== false && (
                  <span className="active-dot">
                    ● Active
                  </span>
                )}

                <button
                  className="danger-btn"
                  disabled={
                    question.active === false
                  }
                  onClick={() =>
                    removeQuestion(question.id)
                  }
                >
                  {question.active !== false
                    ? "Disable"
                    : "Disabled"}
                </button>

              </div>

            </div>

          ))}

          {filteredQuestions.length === 0 && (
            <div className="empty-state">
              No questions match the selected filter.
            </div>
          )}

        </div>

      </section>

      {/* STUDENT DETAILS MODAL */}
      {selectedStudent && (

        <div
          className="modal-overlay"
          onClick={() =>
            setSelectedStudent(null)
          }
        >

          <div
            className="student-modal"
            onClick={(e) =>
              e.stopPropagation()
            }
          >

            <div className="modal-header">

              <div>

                <div className="eyebrow">
                  STUDENT PERFORMANCE
                </div>

                <h2>
                  {selectedStudent.name}
                </h2>

                <p className="muted">
                  {selectedStudent.email}
                </p>

              </div>

              <button
                className="modal-close"
                onClick={() =>
                  setSelectedStudent(null)
                }
              >
                ×
              </button>

            </div>

            <div className="student-detail-grid">

              <div className="detail-card">
                <span>Attempts</span>
                <strong>
                  {selectedStudent.attempts || 0}
                </strong>
              </div>

              <div className="detail-card">
                <span>Accuracy</span>
                <strong>
                  {selectedStudent.accuracy || 0}%
                </strong>
              </div>

              <div className="detail-card">
                <span>Ability Level</span>
                <strong>
                  {selectedStudent.ability ?? 50}%
                </strong>
              </div>

              <div className="detail-card">
                <span>Status</span>
                <strong>
                  {selectedStudent.status ||
                    "Not Started"}
                </strong>
              </div>

            </div>

            <div className="modal-actions">

              <button
                className="ghost-btn"
                onClick={() =>
                  handleReset(selectedStudent.id)
                }
              >
                Reset Assessment
              </button>

              <button
                className="danger-btn"
                onClick={() =>
                  handleDelete(selectedStudent.id)
                }
              >
                Delete Student
              </button>

            </div>

          </div>

        </div>

      )}

    </div>
  );
}