import { Link } from 'react-router-dom';
import NavBar from '../components/NavBar';

const FEATURES = [
  {
    num: '01',
    title: 'SPEC READER',
    accent: 'AGENT 1',
    desc: 'Parses Verilog, SystemVerilog, JSON, and YAML hardware specs into a validated typed interface. Enforces structural constraints before any test runs.',
    detail: '.v .sv .json .yaml .yml',
  },
  {
    num: '02',
    title: 'TEST GENERATOR',
    accent: 'AGENT 2',
    desc: 'Generates adversarial test suites — edge cases, carry-overflow vectors, and full exhaustive sweeps. Seeded by known failure patterns from previous runs.',
    detail: 'normal · breakdown · feedback modes',
  },
  {
    num: '03',
    title: 'VERIFICATION JUDGE',
    accent: 'AGENT 3',
    desc: 'Runs every test vector against a Python DUT simulation, compares actual vs. expected outputs, and explains each failure with root-cause detail.',
    detail: 'pass/fail · coverage % · fault diagnosis',
  },
];

export default function Landing() {
  return (
    <div>
      <NavBar />

      {/* Hero */}
      <section className="hero">
        <div className="container">
          <div className="hero-inner">
            <div className="hero-tag">v2.0.0 — Python-native · No simulator required</div>
            <h1 className="hero-heading">
              FAULT<span className="accent">CLAW</span>
            </h1>
            <p className="hero-sub">Adversarial Hardware Verification</p>
            <p className="hero-tagline">
              Autonomous AI agent that attacks your hardware design to find bugs before silicon does.
              Upload a spec, get a full adversarial test report in seconds.
            </p>
            <div className="hero-actions">
              <Link to="/dashboard" className="btn btn-primary-solid">Open Dashboard →</Link>
              <Link to="/docs" className="btn btn-green">View API Docs</Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="stats-bar">
        <div className="container">
          <div className="stats-inner">
            <div className="stat-block">
              <div className="stat-value">19</div>
              <div className="stat-label">tests / correct adder</div>
            </div>
            <div className="stat-block">
              <div className="stat-value">6</div>
              <div className="stat-label">bugs caught on buggy DUT</div>
            </div>
            <div className="stat-block">
              <div className="stat-value">256</div>
              <div className="stat-label">vectors in breakdown mode</div>
            </div>
            <div className="stat-block">
              <div className="stat-value">100%</div>
              <div className="stat-label">coverage on golden adder</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="features">
        <div className="container">
          <div className="section-label">// pipeline_architecture</div>
          <div className="features-grid">
            {FEATURES.map((f) => (
              <div key={f.num} className="feature-card">
                <div className="feature-num">{f.num}</div>
                <div className="feature-title">
                  <span className="accent">{f.accent}</span> — {f.title}
                </div>
                <p className="feature-desc">{f.desc}</p>
                <div className="feature-detail">{f.detail}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="container" style={{ display: 'flex', justifyContent: 'space-between', width: '100%', flexWrap: 'wrap', gap: 12 }}>
          <span>
            <span className="accent">[FAULTCLAW]</span> — Adversarial Hardware Verification
          </span>
          <span>
            <Link to="/docs" style={{ color: 'var(--text-muted)' }}>API Docs</Link>
            {' · '}
            <Link to="/dashboard" style={{ color: 'var(--text-muted)' }}>Dashboard</Link>
          </span>
        </div>
      </footer>
    </div>
  );
}
