import { useEffect, useState } from "react";

import { getMe } from "./services/api";

import Topbar from "./components/Topbar";
import AdminDashboard from "./pages/AdminDashboard";
import AssessmentPage from "./pages/AssessmentPage";
import Dashboard from "./pages/Dashboard";
import LoginPage from "./pages/LoginPage";
import ResultsPage from "./pages/ResultsPage";

export default function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState("dashboard");
  const [mode, setMode] = useState(null);
  const [booting, setBooting] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("parakh_token");

    if (!token) {
      setBooting(false);
      return;
    }

    getMe()
      .then((res) => {
        setUser(res.data);

        // IMPORTANT:
        // Admin should always land on Admin Dashboard.
        if (res.data.role === "admin") {
          setView("admin");
        } else {
          setView("dashboard");
        }
      })
      .catch(() => {
        localStorage.removeItem("parakh_token");
        setUser(null);
      })
      .finally(() => {
        setBooting(false);
      });
  }, []);

  function logout() {
    localStorage.removeItem("parakh_token");

    setUser(null);
    setView("dashboard");
    setMode(null);
  }

  function startAssessment() {
    // Admin is NOT allowed to start assessments.
    if (user?.role === "admin") {
      return;
    }

    setMode("pre_assessment");
    setView("assessment");
  }

  function exitAssessment() {
    setView("dashboard");
    setMode(null);
  }

  if (booting) {
    return (
      <div className="loading">
        Starting PARAKH AI...
      </div>
    );
  }

  if (!user) {
    return (
      <LoginPage
        onLogin={(loggedInUser) => {
          setUser(loggedInUser);

          // Redirect based on role immediately after login.
          if (loggedInUser.role === "admin") {
            setView("admin");
          } else {
            setView("dashboard");
          }
        }}
      />
    );
  }

  // --------------------------------------------------
  // ADMIN
  // --------------------------------------------------

  if (user.role === "admin") {
    return (
      <>
        <Topbar
          user={user}
          onLogout={logout}
        />

        <nav className="nav">

          <button
            className={view === "admin" ? "active" : ""}
            onClick={() => {
              setView("admin");
              setMode(null);
            }}
          >
            Admin Dashboard
          </button>

        </nav>

        {view === "admin" && (
          <AdminDashboard />
        )}
      </>
    );
  }

  // --------------------------------------------------
  // STUDENT ASSESSMENT
  // --------------------------------------------------

  if (view === "assessment") {
    return (
      <>
        <Topbar
          user={user}
          onLogout={logout}
        />

        <AssessmentPage
          mode={mode}
          onExit={exitAssessment}
        />
      </>
    );
  }

  // --------------------------------------------------
  // STUDENT APPLICATION
  // --------------------------------------------------

  return (
    <>
      <Topbar
        user={user}
        onLogout={logout}
      />

      <nav className="nav">

        <button
          className={
            view === "dashboard"
              ? "active"
              : ""
          }
          onClick={() => {
            setView("dashboard");
            setMode(null);
          }}
        >
          Dashboard
        </button>

        <button
          className={
            view === "results"
              ? "active"
              : ""
          }
          onClick={() => {
            setView("results");
            setMode(null);
          }}
        >
          Results
        </button>

      </nav>

      {view === "dashboard" && (
        <Dashboard
          user={user}
          onStart={startAssessment}
        />
      )}

      {view === "results" && (
        <ResultsPage />
      )}
    </>
  );
}