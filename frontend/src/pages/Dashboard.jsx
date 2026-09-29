import { useEffect, useState } from "react";
import { getAssessmentStatus, getStudentAnalytics } from "../services/api";

export default function Dashboard({ user, onStart }) {
  const [analytics, setAnalytics] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getStudentAnalytics(), getAssessmentStatus()])
      .then(([a, s]) => {
        setAnalytics(a.data);
        setStatus(s.data);
      })
      .catch(() => setError("Could not load your learner profile. Please retry."));
  }, []);

  if (error) return <div className="page center"><div className="panel"><p className="error">{error}</p></div></div>;
  if (!analytics || !status) return <div className="loading">Loading learner profile...</div>;

  return (
    <div className="page">
      <div className="hero">
        <div>
          <div className="eyebrow">AI LEARNER PROFILE</div>
          <h1>Welcome, {user.name}</h1>
          <p>
            PARAKH AI combines correctness, response time, topic-wise performance,
            question difficulty and your self-reported confidence to choose the
            next MCQ for your current level (Section III of the paper).
          </p>
        </div>
        <button className="primary-btn" onClick={onStart}>
          {!status.pre_assessment_complete
            ? "Start Level 0 Test"
            : status.session_answered > 0
            ? "Resume Adaptive Test"
            : "Start Adaptive Test"}
        </button>
      </div>

      <div className="stat-grid">
        <div className="stat-card"><span>Overall ability (θ)</span><strong>{analytics.overall_ability}%</strong></div>
        <div className="stat-card"><span>Accuracy</span><strong>{analytics.accuracy}%</strong></div>
        <div className="stat-card"><span>Learning improvement</span><strong>{analytics.learning_improvement}%</strong></div>
        <div className="stat-card"><span>Knowledge retention</span><strong>{analytics.retention_score}%</strong></div>
      </div>

      <div className="stat-grid">
        <div className="stat-card"><span>Questions attempted</span><strong>{analytics.total_questions}</strong></div>
        <div className="stat-card"><span>Average confidence</span><strong>{analytics.average_confidence}/5</strong></div>
        <div className="stat-card"><span>Average response time</span><strong>{analytics.average_response_time}s</strong></div>
        <div className="stat-card"><span>Verification questions</span><strong>{analytics.verification_questions}</strong></div>
      </div>

      {status.pre_assessment_complete && (
        <div className="progress-note">
          Adaptive session {analytics.session.number + 1}: {status.session_answered} / {status.session_length} answered
        </div>
      )}

      <div className="two-column">
        <section className="panel">
          <div className="eyebrow">TOPIC-WISE PERFORMANCE</div>
          <h2>Your learning gaps</h2>

          {analytics.topics.length === 0 && (
            <p className="muted">Complete Level 0 to build your initial learner profile.</p>
          )}

          {analytics.topics.map((topic) => (
            <div className="mastery-row" key={topic.topic}>
              <div className="mastery-label">
                <span>{topic.topic}{topic.flagged ? " ⚠" : ""}</span>
                <strong>{topic.accuracy}%</strong>
              </div>
              <div className="bar">
                <div style={{ width: `${topic.accuracy}%` }} />
              </div>
            </div>
          ))}
        </section>

        <section className="panel">
          <div className="eyebrow">ADAPTIVE DECISION LOGIC</div>
          <h2>How AI selects your next MCQ</h2>

          <div className="feature-list">
            <div><b>Correct + high confidence</b><span>Difficulty increases.</span></div>
            <div><b>Correct + low confidence</b><span>Possible fluke → difficulty holds, verification question queued.</span></div>
            <div><b>Incorrect + low confidence</b><span>Known gap → an easier question follows.</span></div>
            <div><b>Incorrect + high confidence</b><span>Possible misconception → difficulty drops, topic flagged, verification queued.</span></div>
            <div><b>Weak topic</b><span>Preferred within the difficulty band, without ignoring other topics.</span></div>
          </div>
        </section>
      </div>
    </div>
  );
}
