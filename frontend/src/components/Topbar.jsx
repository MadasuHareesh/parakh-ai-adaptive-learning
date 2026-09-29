export default function Topbar({ user, onLogout }) {
  return (
    <header className="topbar">
      <div>
        <div className="brand">PARAKH<span>•AI</span></div>
        <div className="brand-sub">Confidence-Aware Adaptive Learning</div>
      </div>
      <div className="topbar-right">
        <span>{user?.name}</span>
        <button className="ghost-btn" onClick={onLogout}>Logout</button>
      </div>
    </header>
  );
}
