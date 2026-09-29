const levels = [
  { value: 1, stars: "★☆☆☆☆", title: "Just Guessing" },
  { value: 2, stars: "★★☆☆☆", title: "Low Confidence" },
  { value: 3, stars: "★★★☆☆", title: "Somewhat Sure" },
  { value: 4, stars: "★★★★☆", title: "Confident" },
  { value: 5, stars: "★★★★★", title: "Very Confident" },
];

export default function ConfidenceReview({
  confidence,
  setConfidence,
  onContinue,
}) {
  return (
    <div className="panel confidence-panel">
      <div className="eyebrow">CONFIDENCE REVIEW</div>
      <h2>How confident are you in your answer?</h2>
      <p className="muted">
        This step is required after every MCQ. Your confidence helps the AI
        distinguish strong understanding, guessing, and possible misconceptions.
      </p>

      <div className="confidence-grid">
        {levels.map((level) => (
          <button
            key={level.value}
            className={`confidence-card ${
              confidence === level.value ? "selected" : ""
            }`}
            onClick={() => setConfidence(level.value)}
          >
            <span className="stars">{level.stars}</span>
            <span className="confidence-number">{level.value}</span>
            <span>{level.title}</span>
          </button>
        ))}
      </div>

      <button
        className="primary-btn"
        disabled={!confidence}
        onClick={onContinue}
      >
        Record Answer & Continue
      </button>
    </div>
  );
}
