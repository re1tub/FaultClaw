function formatTs(iso) {
  const d = new Date(iso);
  return d.toLocaleString('en-US', {
    month: 'short', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hour12: false,
  });
}

function modeColor(mode, dut) {
  if (dut === 'buggy_adder') return 'buggy';
  if (mode === 'breakdown') return 'breakdown';
  return 'normal';
}

function HistoryCard({ run }) {
  const { timestamp, design_name, mode, dut, total_tests, tests_passed, tests_failed } = run;
  const colorClass = modeColor(mode, dut);
  const pct = total_tests > 0 ? (tests_passed / total_tests) * 100 : 0;
  const hasFail = tests_failed > 0;

  return (
    <div className="history-card">
      <div className="hist-timestamp">{formatTs(timestamp)}</div>
      <div className="hist-design">{design_name}</div>
      <div className={`hist-mode ${colorClass}`}>{colorClass}</div>
      <div className="hist-counts">
        <span className="hist-pass">✓ {tests_passed}</span>
        {hasFail && <span className="hist-fail">✗ {tests_failed}</span>}
        <span style={{ color: 'var(--text-muted)' }}>/ {total_tests}</span>
      </div>
      <div className="hist-bar-wrap">
        <div
          className={`hist-bar-fill${hasFail ? ' has-failures' : ''}`}
          style={{
            width: `${pct}%`,
            '--pct': `${pct}%`,
          }}
        />
      </div>
    </div>
  );
}

export default function HistoryPanel({ history }) {
  const recent = history.slice(0, 5);

  return (
    <div className="panel history-panel">
      <div className="panel-header">
        <span className="accent">▸</span> run_history
        <span style={{ marginLeft: 'auto', color: 'var(--text-dim)', fontSize: 10 }}>
          last {recent.length} of {history.length}
        </span>
      </div>
      {recent.length === 0 ? (
        <div className="history-empty">// no runs recorded yet</div>
      ) : (
        <div className="history-grid">
          {recent.map((run, i) => (
            <HistoryCard key={i} run={run} />
          ))}
        </div>
      )}
    </div>
  );
}
