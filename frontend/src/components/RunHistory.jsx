function ts(iso) {
  const d = new Date(iso);
  return d.toLocaleString('en-US', {
    month: 'short', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
    hour12: false,
  });
}

function CovBar({ pct }) {
  return (
    <span>
      <span className="hist-cov-bar">
        <span className="hist-cov-fill" style={{ width: `${pct}%` }} />
      </span>
      {pct}%
    </span>
  );
}

export default function RunHistory({ history }) {
  return (
    <div className="panel run-history">
      <div className="panel-header">
        <span className="accent">▸</span> run_history
        <span className="badge">{history.length} runs</span>
      </div>
      {history.length === 0 ? (
        <div className="hist-empty">// no runs recorded yet</div>
      ) : (
        <table className="history-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Design</th>
              <th>Mode</th>
              <th>Passed</th>
              <th>Failed</th>
              <th>Coverage</th>
            </tr>
          </thead>
          <tbody>
            {history.map((r) => (
              <tr key={r.id ?? r.timestamp}>
                <td>{ts(r.timestamp)}</td>
                <td className="hist-design">{r.design_name}</td>
                <td className={`hist-mode ${r.mode}`}>{r.mode}</td>
                <td className="hist-pass">✓ {r.tests_passed}</td>
                <td className={r.tests_failed > 0 ? 'hist-fail' : 'hist-pass'}>
                  {r.tests_failed > 0 ? `✗ ${r.tests_failed}` : '—'}
                </td>
                <td><CovBar pct={r.coverage_pct} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
