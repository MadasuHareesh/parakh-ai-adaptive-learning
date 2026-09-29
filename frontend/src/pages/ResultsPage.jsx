import { useEffect, useState } from "react";
import { getStudentAnalytics } from "../services/api";

export default function ResultsPage() {
  const [data, setData] = useState(null);

  useEffect(() => {
    getStudentAnalytics().then((res) => setData(res.data));
  }, []);

  if (!data) return <div className="loading">Loading analytics...</div>;

  return (
    <div className="page">
      <div className="hero compact">
        <div>
          <div className="eyebrow">RESULTS & ANALYTICS</div>
          <h1>Your Adaptive Learning Report</h1>
          <p>
            Evaluated using accuracy, ability, response time, learning
            improvement, knowledge retention and confidence calibration.
          </p>
        </div>
      </div>

      <div className="stat-grid">
        <div className="stat-card"><span>Accuracy</span><strong>{data.accuracy}%</strong></div>
        <div className="stat-card"><span>Overall ability</span><strong>{data.overall_ability}%</strong></div>
        <div className="stat-card"><span>Learning improvement</span><strong>{data.learning_improvement}%</strong></div>
        <div className="stat-card"><span>Knowledge retention</span><strong>{data.retention_score}%</strong></div>
      </div>

      <div className="stat-grid">
        <div className="stat-card"><span>Average response time</span><strong>{data.average_response_time}s</strong></div>
        <div className="stat-card"><span>Verification questions</span><strong>{data.verification_questions}</strong></div>
        <div className="stat-card">
          <span>Calibration gap (G)</span>
          <strong>{data.calibration_gap > 0 ? "+" : ""}{data.calibration_gap}</strong>
        </div>
        <div className="stat-card"><span>Questions attempted</span><strong>{data.total_questions}</strong></div>
      </div>

      <section className="panel">
        <div className="eyebrow">TOPIC-WISE PERFORMANCE</div>
        <h2>Current knowledge profile</h2>

        {data.topics.length === 0 && <p className="muted">No adaptive attempts yet.</p>}

        {data.topics.map((t) => (
          <div className="mastery-row" key={t.topic}>
            <div className="mastery-label">
              <span>{t.topic}{t.flagged ? " ⚠ possible misconception" : ""}</span>
              <strong>{t.accuracy}%</strong>
            </div>
            <div className="bar">
              <div style={{ width: `${t.accuracy}%` }} />
            </div>
          </div>
        ))}
      </section>

      <section className="panel">
        <div className="eyebrow">CONFIDENCE DISTRIBUTION</div>
        <div className="confidence-distribution">
          {Object.entries(data.confidence_distribution).map(([level, count]) => (
            <div key={level}>
              <strong>{level}</strong>
              <span>{count} responses</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
