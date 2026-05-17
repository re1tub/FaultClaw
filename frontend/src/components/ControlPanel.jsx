export default function ControlPanel({ loading, activeMode, onVerify, onBuggy, onBreakdown }) {
  const btn = (label, desc, icon, color, mode, handler) => (
    <button
      className={`action-btn ${color}${loading && activeMode === mode ? ' active-run' : ''}`}
      onClick={handler}
      disabled={loading}
    >
      <span className="action-btn-icon">{icon}</span>
      <span className="action-btn-body">
        <span className="action-btn-label">{label}</span>
        <span className="action-btn-desc">{desc}</span>
      </span>
    </button>
  );

  return (
    <div className="panel control-panel">
      <div className="panel-header">
        <span className="accent">▸</span> control_panel
      </div>
      <div className="btn-stack">
        {btn(
          'RUN VERIFY',
          'Full pipeline — golden DUT, normal mode',
          '▶',
          'green',
          'verify',
          onVerify,
        )}
        {btn(
          'RUN BUGGY',
          'Buggy DUT — carry-out hardwired to 0',
          '⚡',
          'amber',
          'buggy',
          onBuggy,
        )}
        {btn(
          'BREAKDOWN MODE',
          'Exhaustive 16×16 sweep — 256 test vectors',
          '◉',
          'red',
          'breakdown',
          onBreakdown,
        )}
      </div>
    </div>
  );
}
