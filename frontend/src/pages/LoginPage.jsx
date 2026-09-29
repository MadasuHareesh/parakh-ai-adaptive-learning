import { useState } from "react";
import { login } from "../services/api";

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();

    setError("");
    setBusy(true);

    try {
      const res = await login(email, password);

      // Save authentication token
      localStorage.setItem(
        "parakh_token",
        res.data.access_token
      );

      // Send logged-in user information to App.jsx
      onLogin(res.data.user);

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Login failed. Please check your email and password."
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">

      <div className="auth-card">

        {/* BRAND */}
        <div className="brand big">
          PARAKH<span>•AI</span>
        </div>

        <p className="brand-sub">
          AI-Powered Adaptive MCQ Selection
        </p>


        {/* TITLE */}
        <h1>Welcome back</h1>

        <p className="muted">
          Sign in to continue to PARAKH AI.
        </p>


        {/* LOGIN FORM */}
        <form onSubmit={submit}>

          {/* EMAIL */}
          <label htmlFor="email">
            Email
          </label>

          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email"
            autoComplete="username"
            required
            disabled={busy}
          />


          {/* PASSWORD */}
          <label htmlFor="password">
            Password
          </label>

          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            autoComplete="current-password"
            required
            disabled={busy}
          />


          {/* ERROR */}
          {error && (
            <div className="error">
              {error}
            </div>
          )}


          {/* LOGIN BUTTON */}
          <button
            className="primary-btn"
            type="submit"
            disabled={busy}
          >
            {busy ? "Signing in..." : "Login"}
          </button>

        </form>


        {/* DEMO ACCOUNTS */}
        <div className="demo-box">

          <strong>
            Demo accounts
          </strong>

          <br />

          Student:
          <br />
          <span>
            student@parakh.local / student123
          </span>

          <br />
          <br />

          Admin:
          <br />
          <span>
            admin@parakh.local / admin123
          </span>

        </div>

      </div>

    </div>
  );
}