import { useEffect, useState } from "react";
import { getNextQuestion, submitAnswer } from "../services/api";
import QuestionCard from "../components/QuestionCard";
import ConfidenceReview from "../components/ConfidenceReview";
import ResultFeedback from "../components/ResultFeedback";

export default function AssessmentPage({ mode, onExit }) {
  const [question, setQuestion] = useState(null);
  const [progress, setProgress] = useState({ done: 0, total: 0 });
  const [answer, setAnswer] = useState("");
  const [responseTime, setResponseTime] = useState(1);
  const [confidence, setConfidence] = useState(null);
  const [stage, setStage] = useState("question");
  const [result, setResult] = useState(null);
  const [pending, setPending] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sessionDone, setSessionDone] = useState(false);

  async function loadQuestion() {
    setLoading(true);
    setError("");
    setResult(null);
    setConfidence(null);
    setAnswer("");
    setStage("question");

    try {
      const res = await getNextQuestion(mode);
      setProgress(res.data.progress || { done: 0, total: 0 });
      setPending({ action: res.data.pending_action, reason: res.data.pending_reason });

      if (res.data.completed) {
        setQuestion(null);
        setSessionDone(true);
      } else {
        setQuestion(res.data.question);
        setSessionDone(false);
      }
    } catch (err) {
      setError(err?.response?.data?.detail || "Could not load the next question.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadQuestion();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode]);

  async function handleAnswer(selected, seconds) {
    setAnswer(selected);
    setResponseTime(Math.max(seconds, 1));
    setStage("confidence");
  }

  async function handleConfidence() {
    if (!question || !answer || !confidence) {
      window.alert("Please answer the MCQ and select a confidence level (1-5).");
      return;
    }

    try {
      const res = await submitAnswer({
        question_id: question.id,
        selected_answer: answer,
        confidence: Number(confidence),
        response_time: Math.max(Number(responseTime), 1),
        mode,
      });
      setResult(res.data);
      setStage("result");
    } catch (error) {
      const detail =
        error?.response?.status === 409
          ? "This question expired. Loading a fresh one."
          : error?.response?.data?.detail || error?.message || "Unable to reach the PARAKH backend.";
      window.alert(`Submission failed:\n${detail}`);
      if (error?.response?.status === 409) loadQuestion();
    }
  }

  function handleNext() {
    if (result?.session_complete) {
      onExit();
      return;
    }
    loadQuestion();
  }

  if (loading) return <div className="loading">Loading adaptive engine...</div>;

  if (error) {
    return (
      <div className="page center">
        <div className="panel">
          <p className="error">{error}</p>
          <button className="primary-btn" onClick={loadQuestion}>Retry</button>
        </div>
      </div>
    );
  }

  if (!question && stage !== "result") {
    return (
      <div className="page center">
        <div className="panel completion">
          <div className="result-icon good">✓</div>
          <div className="eyebrow">ASSESSMENT COMPLETE</div>
          <h1>{mode === "pre_assessment" ? "Initial learner profile created" : "Adaptive session complete"}</h1>
          <p className="muted">
            Your performance, confidence, response time and topic-wise results have been stored for analytics.
          </p>
          <button className="primary-btn" onClick={onExit}>View Dashboard</button>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="assessment-head">
        <div>
          <div className="eyebrow">{mode === "pre_assessment" ? "LEVEL 0 • DIAGNOSTIC TEST" : "AI ADAPTIVE ASSESSMENT"}</div>
          <h1>{mode === "pre_assessment" ? "Build your initial learner profile" : "Next Best MCQ"}</h1>
        </div>
        <div className="progress-box">
          <span>{progress.done} / {progress.total}</span>
          <div className="progress"><div style={{ width: `${progress.total ? (progress.done / progress.total) * 100 : 0}%` }} /></div>
        </div>
      </div>

      {mode === "adaptive" && pending?.reason && stage === "question" && (
        <div className="ai-banner">
          <b>AI selection signal:</b> {pending.reason}
          {question?.is_verification && " — verification question"}
        </div>
      )}

      {stage === "question" && question && (
        <QuestionCard question={question} onSubmit={handleAnswer} />
      )}

      {stage === "confidence" && (
        <ConfidenceReview confidence={confidence} setConfidence={setConfidence} onContinue={handleConfidence} />
      )}

      {stage === "result" && result && (
        <ResultFeedback result={result} onNext={handleNext} />
      )}
    </div>
  );
}
