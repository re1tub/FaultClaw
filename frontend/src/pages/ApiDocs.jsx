import NavBar from '../components/NavBar';
import { Link } from 'react-router-dom';

const BASE = 'http://localhost:8000';

function Method({ m }) {
  return <span className={`method-badge ${m}`}>{m}</span>;
}

function Code({ children, label }) {
  return (
    <div className="code-block">
      {label && <span className="label">{label}</span>}
      <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
        {children}
      </pre>
    </div>
  );
}

function Endpoint({ method, path, desc, auth, request, response }) {
  return (
    <div className="endpoint-block">
      <div className="endpoint-header">
        <Method m={method} />
        <span className="endpoint-path">{BASE}{path}</span>
      </div>
      <p className="endpoint-desc">{desc}</p>
      {auth && <div className="endpoint-auth">⚿ Requires X-API-Key header</div>}
      {request && <Code label="request">{request}</Code>}
      {response && <Code label="response" style={{ marginTop: 8 }}>{response}</Code>}
    </div>
  );
}

export default function ApiDocs() {
  return (
    <div>
      <NavBar />
      <div className="docs-page">
        <h1>API <span className="accent">Reference</span></h1>
        <p className="docs-intro">
          The FaultClaw API lets you upload hardware specs, run adversarial verification pipelines,
          and retrieve results programmatically. All protected endpoints require an API key in the
          {' '}<code style={{ color: 'var(--green)', fontSize: 12 }}>X-API-Key</code> request header.
          Get a key on the <Link to="/#get-key" style={{ color: 'var(--green)' }}>home page</Link>.
        </p>

        <div className="docs-base-url">
          Base URL: <span className="url">{BASE}</span>
          <span style={{ color: 'var(--text-muted)', marginLeft: 16, fontSize: 11 }}>
            (start server: <code style={{ color: 'var(--text-secondary)' }}>uvicorn api.main:app --port 8000</code>)
          </span>
        </div>

        {/* Auth */}
        <div className="docs-section">
          <div className="docs-section-title">// authentication</div>

          <Endpoint
            method="POST"
            path="/auth/register"
            desc="Generate an API key for an email address. Returns the same key if the email already exists."
            request={`curl -X POST ${BASE}/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{"email": "engineer@company.com"}'`}
            response={`{
  "api_key": "a3f8c2e9d4b7...",
  "email": "engineer@company.com",
  "created_at": "2026-05-19T14:00:00Z"
}`}
          />

          <Endpoint
            method="GET"
            path="/auth/usage"
            desc="Check your API key's run count and registration date."
            auth
            request={`curl ${BASE}/auth/usage \\
  -H "X-API-Key: a3f8c2e9d4b7..."`}
            response={`{
  "email": "engineer@company.com",
  "created_at": "2026-05-19T14:00:00Z",
  "run_count": 12
}`}
          />
        </div>

        {/* Upload */}
        <div className="docs-section">
          <div className="docs-section-title">// file upload</div>

          <Endpoint
            method="POST"
            path="/upload"
            desc="Upload a hardware spec file (.v .sv .json .yaml .yml). Max 10 MB. Returns a file_id you use in the verify call."
            auth
            request={`curl -X POST ${BASE}/upload \\
  -H "X-API-Key: a3f8c2e9d4b7..." \\
  -F "file=@adder_4bit.v"`}
            response={`{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "adder_4bit.v",
  "detected_type": "verilog",
  "upload_timestamp": "2026-05-19T14:05:00Z"
}`}
          />
        </div>

        {/* Verify */}
        <div className="docs-section">
          <div className="docs-section-title">// verification</div>

          <Endpoint
            method="POST"
            path="/verify/{file_id}"
            desc={`Run the full FaultClaw pipeline on an uploaded file. mode is one of: "normal" (default), "breakdown" (exhaustive 256-test sweep), or "buggy" (simulates carry-out hardwired to 0).`}
            auth
            request={`curl -X POST ${BASE}/verify/550e8400-... \\
  -H "X-API-Key: a3f8c2e9d4b7..." \\
  -H "Content-Type: application/json" \\
  -d '{"mode": "normal"}'`}
            response={`{
  "design_name": "adder_4bit",
  "mode": "normal",
  "dut": "golden_adder",
  "total_tests": 19,
  "tests_passed": 19,
  "tests_failed": 0,
  "coverage_pct": 100.0,
  "failed_tests": [],
  "timestamp": "2026-05-19T14:05:12Z",
  "file_id": "550e8400-..."
}`}
          />

          <Endpoint
            method="POST"
            path="/verify/buggy (example with failures)"
            desc='Use mode "buggy" to test against the buggy DUT simulation. Failed tests include root-cause explanations.'
            auth
            request={`curl -X POST ${BASE}/verify/550e8400-... \\
  -H "X-API-Key: a3f8c2e9d4b7..." \\
  -H "Content-Type: application/json" \\
  -d '{"mode": "buggy"}'`}
            response={`{
  "design_name": "adder_4bit",
  "mode": "normal",
  "dut": "buggy_adder",
  "total_tests": 19,
  "tests_passed": 13,
  "tests_failed": 6,
  "coverage_pct": 68.4,
  "failed_tests": [
    {
      "id": "edge_003",
      "inputs": {"a": 15, "b": 1},
      "expected": {"sum": 16},
      "actual": {"sum": 0},
      "failure_explanation": "sum: expected 16, got 0; carry-out bit missing — sum[4] should be 1 (15+1=16 overflows 4 bits)"
    }
  ]
}`}
          />
        </div>

        {/* Results */}
        <div className="docs-section">
          <div className="docs-section-title">// results history</div>

          <Endpoint
            method="GET"
            path="/results"
            desc="Returns the last 10 verification runs for your API key."
            auth
            request={`curl ${BASE}/results \\
  -H "X-API-Key: a3f8c2e9d4b7..."`}
            response={`[
  {
    "id": 42,
    "file_id": "550e8400-...",
    "mode": "normal",
    "timestamp": "2026-05-19T14:05:12Z",
    "design_name": "adder_4bit",
    "total_tests": 19,
    "tests_passed": 19,
    "tests_failed": 0,
    "coverage_pct": 100.0
  }
]`}
          />

          <Endpoint
            method="GET"
            path="/results/{file_id}"
            desc="Returns the latest verification result for a specific uploaded file."
            auth
            request={`curl ${BASE}/results/550e8400-... \\
  -H "X-API-Key: a3f8c2e9d4b7..."`}
          />
        </div>

        <div style={{ marginTop: 40, padding: '20px 0', borderTop: '1px solid var(--border)', fontSize: 11, color: 'var(--text-muted)', letterSpacing: 1 }}>
          FaultClaw API v2.0.0 · <Link to="/dashboard" style={{ color: 'var(--green)' }}>Open Dashboard →</Link>
        </div>
      </div>
    </div>
  );
}
