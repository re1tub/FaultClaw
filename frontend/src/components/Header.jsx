export default function Header() {
  return (
    <header className="header">
      <div className="header-inner">
        <div>
          <div className="logo">
            <span className="logo-bracket">[</span>
            <span className="logo-word">FAULT</span>
            <span className="logo-accent">CLAW</span>
            <span className="logo-bracket">]</span>
          </div>
          <div className="header-subtitle">// adversarial hardware verification</div>
        </div>
        <div className="header-right">
          <div className="status-badge">
            <span className="status-dot" />
            SYSTEM_ONLINE
          </div>
          <div className="version-tag">v2.0.0 — python pipeline</div>
        </div>
      </div>
    </header>
  );
}
