export default function ResultFeedback({ result, onNext }) {
  const evaluation = result.evaluation || {};

  return (
    <div className="panel result-panel">
      <div className={`result-icon ${result.correct ? "good" : "bad"}`}>
        {result.correct ? "✓" : "!"}
      </div>

      <div className="eyebrow">{evaluation.label}</div>
      <h2>{result.correct ? "Correct answer" : "Not quite"}</h2>

      <div className="result-grid">
        <div>
          <span>Confidence</span>
          <strong>{result.confidence}/5</strong>
        </div>
        <div>
          <span>Overall ability</span>
          <strong>{Math.round(result.overall_ability * 100)}%</strong>
        </div>
        <div>
          <span>Next target difficulty</span>
          <strong>{(1 + result.target_difficulty * 4).toFixed(1)}/5</strong>
        </div>
      </div>

      <div className="decision-box">
        <strong>AI decision:</strong> {evaluation.message}
      </div>

      {result.explanation && <p className="explanation">{result.explanation}</p>}

      <button className="primary-btn" onClick={onNext}>
        {result.session_complete ? "View Session Summary" : "Next Best MCQ"}
      </button>
    </div>
  );
}
