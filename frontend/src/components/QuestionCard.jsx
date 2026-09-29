import { useEffect, useState } from "react";

export default function QuestionCard({
  question,
  onSubmit,
  disabled = false,
}) {
  const [answer, setAnswer] = useState("");
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    setAnswer("");
    setSeconds(0);

    const timer = setInterval(() => {
      setSeconds((s) => s + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [question?.id]);

  const options = [
    ["A", question.option_a],
    ["B", question.option_b],
    ["C", question.option_c],
    ["D", question.option_d],
  ];

  return (
    <div className="panel question-panel">
      <div className="question-meta">
        <span className="pill">{question.topic}</span>
        <span className="pill">Difficulty {question.difficulty}/5</span>
        <span className="timer">⏱ {seconds}s</span>
      </div>

      <h2 className="question-title">{question.question_text}</h2>

      <div className="options">
        {options.map(([key, value]) => (
          <button
            key={key}
            disabled={disabled}
            className={`option ${answer === key ? "selected" : ""}`}
            onClick={() => setAnswer(key)}
          >
            <span className="option-key">{key}</span>
            <span>{value}</span>
          </button>
        ))}
      </div>

      <button
        className="primary-btn"
        disabled={!answer || disabled}
        onClick={() => onSubmit(answer, seconds)}
      >
        Submit Answer
      </button>
    </div>
  );
}
