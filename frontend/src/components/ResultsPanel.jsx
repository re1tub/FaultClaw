import { useState, useEffect } from 'react';

function ModeBadge({ mode, dut }) {
  const label = dut === 'buggy_adder' ? 'buggy' : (mode || 'normal');
  return <span className={`mode-badge ${label}`}>{label}</span>;
}

function CoverageBar({ pct }) {
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setWidth(pct), 60);
    return () => clearTimeout(t);
  }, [pct]);
  return (
    <div className="coverage-bar-wrap">
      <div className="coverage-bar-fill" style={{ width: `${width}%` }} />
    </div>
  );
}

function FailItem({ test, index }) {
  const { id, inputs, expected, actual, failure_explanation } = test;
  return (
    <div className="fail-item" style={{ animationDelay: `${index * 0.04}s` }}>
      <div className="fail-item-top">
        <span className="fail-id">{id}</span>
        <span className="fail-io">
          a={inputs.a}, b={inputs.b} →{' '}
          <span className="fail-expected">exp:{expected.sum}</span>{' '}
          <span className="fail-got">got:{actual.sum}</span>
        </span>
      </div>
      {failure_explanation && (
        <div className="fail-explanation">{failure_explanation}</div>
      )}
    </div>
  );
}

function downloadReport(report) {
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `faultclaw-${report.design_name || 'report'}-${Date.now()}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default function ResultsPanel({ report, error, loading }) {
  if (loading) {
    return (
      <div className="panel results-panel">
        <div className="panel-header"><span className="accent">▸</span> verification_report</div>
        <div className="results-loading">
          <div className="loading-spinner" />
          <div className="loading-text">running pipeline</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="panel results-panel">
        <div className="panel-header"><span className="accent">▸</span> verification_report</div>
        <div className="results-error">
          <div className="results-error-label">// pipeline error</div>
          {error}
        </div>
      </div>
    );
  }

  if (!report) return null;

  const { design_name, mode, dut, total_tests, tests_passed, tests_failed, coverage_pct, failed_tests } = report;

  return (
    <div className="panel results-panel">
      <div className="panel-header">
        <span className="accent">▸</span> verification_report
        <div className="report-actions">
          <button className="btn btn-ghost" style={{ fontSize: 10, padding: '4px 10px' }} onClick={() => downloadReport(report)}>
            ↓ Download JSON
          </button>
        </div>
      </div>

      <div className="report-meta">
        <span className="report-design">{design_name}</span>
        <ModeBadge mode={mode} dut={dut} />
        <span className="dut-label">{dut}</span>
      </div>

      <div className="metrics-row">
        <div className="metric-block">
          <div className="metric-label">Passed</div>
          <div className="metric-value pass">{tests_passed}</div>
        </div>
        <div className="metric-block">
          <div className="metric-label">Failed</div>
          <div className="metric-value fail">{tests_failed}</div>
        </div>
        <div className="metric-block">
          <div className="metric-label">Coverage</div>
          <div className="metric-value cov">{coverage_pct}%</div>
          <CoverageBar pct={coverage_pct} />
        </div>
      </div>

      {tests_failed === 0 ? (
        <div className="all-passed-banner">✓ ALL {total_tests} TESTS PASSED</div>
      ) : (
        <>
          <div className="fail-list-header">// failed_tests ({tests_failed})</div>
          <div className="fail-list">
            {failed_tests.map((t, i) => (
              <FailItem key={t.id} test={t} index={i} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
