import { useState, useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import NavBar from '../components/NavBar';
import DropZone from '../components/DropZone';
import ResultsPanel from '../components/ResultsPanel';
import LiveLog from '../components/LiveLog';
import RunHistory from '../components/RunHistory';

const API_BASE = 'http://localhost:8000';

const LOG_SEQUENCES = {
  normal: [
    '> initializing pipeline...',
    '> agent_1: parsing spec...',
    '> agent_1: validating port topology',
    '> agent_2: generating adversarial test suite',
    '> agent_2: edge + carry-overflow vectors injected',
    '> agent_3: loading golden DUT model',
    '> agent_3: running verification pass...',
    '> memory: persisting run record',
    '> pipeline complete.',
  ],
  buggy: [
    '> initializing pipeline...',
    '> agent_1: parsing spec...',
    '> agent_2: generating adversarial test suite',
    '> agent_2: targeting carry-out overflow vectors',
    '> agent_3: BUGGY DUT [carry-out hardwired to 0]',
    '> agent_3: fault injection active',
    '> agent_3: running verification pass...',
    '> memory: persisting run record',
    '> pipeline complete.',
  ],
  breakdown: [
    '> initializing pipeline...',
    '> agent_1: parsing spec...',
    '> agent_2: BREAKDOWN MODE — exhaustive 16×16 sweep',
    '> agent_2: generating 256 test vectors',
    '> agent_3: loading golden DUT model',
    '> agent_3: running 256 tests...',
    '> memory: persisting run record',
    '> pipeline complete.',
  ],
};

export default function Dashboard() {
  const [apiKey, setApiKey]           = useState(() => localStorage.getItem('fc_api_key') || '');
  const [keyInput, setKeyInput]       = useState('');
  const [keyInfo, setKeyInfo]         = useState(null);
  const [keyError, setKeyError]       = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploading, setUploading]     = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [running, setRunning]         = useState(false);
  const [activeMode, setActiveMode]   = useState(null);
  const [report, setReport]           = useState(null);
  const [runError, setRunError]       = useState(null);
  const [logLines, setLogLines]       = useState([]);
  const [history, setHistory]         = useState([]);
  const intervalRef = useRef(null);

  const authHeaders = useCallback(() => ({ 'X-API-Key': apiKey }), [apiKey]);

  const fetchUsage = useCallback(async (key) => {
    try {
      const res = await axios.get(`${API_BASE}/auth/usage`, { headers: { 'X-API-Key': key } });
      setKeyInfo(res.data);
      setKeyError('');
    } catch {
      setKeyInfo(null);
      setKeyError('Invalid or expired API key.');
    }
  }, []);

  const fetchHistory = useCallback(async () => {
    if (!apiKey) return;
    try {
      const res = await axios.get(`${API_BASE}/results`, { headers: authHeaders() });
      setHistory(res.data);
    } catch {
      // history is non-critical
    }
  }, [apiKey, authHeaders]);

  useEffect(() => {
    if (apiKey) {
      fetchUsage(apiKey);
      fetchHistory();
    }
  }, [apiKey, fetchUsage, fetchHistory]);

  const connectKey = () => {
    const k = keyInput.trim();
    if (!k) return;
    setApiKey(k);
    localStorage.setItem('fc_api_key', k);
    fetchUsage(k);
  };

  const disconnect = () => {
    setApiKey('');
    setKeyInput('');
    setKeyInfo(null);
    setUploadedFile(null);
    setReport(null);
    setHistory([]);
    localStorage.removeItem('fc_api_key');
  };

  const handleFileAccepted = async (file) => {
    setUploading(true);
    setUploadError('');
    setUploadedFile(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await axios.post(`${API_BASE}/upload`, formData, { headers: authHeaders() });
      setUploadedFile(res.data);
    } catch (e) {
      setUploadError(e.response?.data?.detail || e.message);
    } finally {
      setUploading(false);
    }
  };

  const handleRun = useCallback(async (mode) => {
    if (!uploadedFile || !apiKey) return;
    clearInterval(intervalRef.current);

    setRunning(true);
    setActiveMode(mode);
    setReport(null);
    setRunError(null);

    const seq = LOG_SEQUENCES[mode];
    let idx = 0;
    setLogLines([seq[idx++]]);

    intervalRef.current = setInterval(() => {
      if (idx < seq.length) {
        setLogLines((prev) => [...prev, seq[idx++]]);
      } else {
        clearInterval(intervalRef.current);
      }
    }, 380);

    try {
      const res = await axios.post(
        `${API_BASE}/verify/${uploadedFile.file_id}`,
        { mode },
        { headers: authHeaders() },
      );
      clearInterval(intervalRef.current);
      setLogLines(seq);
      setReport(res.data);
      fetchHistory();
    } catch (e) {
      clearInterval(intervalRef.current);
      const msg = e.response?.data?.detail || e.message;
      setLogLines((prev) => [...prev, `> ERROR: ${msg}`]);
      setRunError(msg);
    } finally {
      setRunning(false);
    }
  }, [uploadedFile, apiKey, authHeaders, fetchHistory]);

  // ── No key state ──────────────────────────────────────────────
  if (!apiKey) {
    return (
      <div>
        <NavBar />
        <div className="dash-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="panel" style={{ maxWidth: 480, width: '100%', margin: '60px 24px' }}>
            <div className="panel-header"><span className="accent">▸</span> connect</div>
            <div className="api-key-prompt">
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', letterSpacing: 1 }}>
                Enter your API key to access the dashboard.
              </div>
              <div className="api-key-field">
                <input
                  className="api-key-input"
                  type="text"
                  placeholder="Paste API key..."
                  value={keyInput}
                  onChange={(e) => setKeyInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && connectKey()}
                />
                <button className="btn btn-green" onClick={connectKey}>Connect</button>
              </div>
              {keyError && <div style={{ fontSize: 11, color: 'var(--red)' }}>{keyError}</div>}
              <div className="api-key-hint">
                No key?{' '}
                <Link to="/#get-key" style={{ color: 'var(--green)' }}>Get one on the home page →</Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const showResults = report || runError || running;

  return (
    <div>
      <NavBar />
      <div className="dash-page">
        <div className="dash-layout">
          {/* Left column */}
          <div className="dash-left">

            {/* API Key */}
            <div className="panel">
              <div className="panel-header"><span className="accent">▸</span> authenticated</div>
              <div className="api-key-connected">
                {keyInfo && <div className="key-email">{keyInfo.email}</div>}
                {keyInfo && (
                  <div className="key-meta">
                    <span className="key-runs">{keyInfo.run_count} runs used</span>
                    {' · '}
                    <span>since {new Date(keyInfo.created_at).toLocaleDateString()}</span>
                  </div>
                )}
                <div className="key-masked">{apiKey.slice(0, 10)}...{apiKey.slice(-6)}</div>
                <button className="key-disconnect" onClick={disconnect}>✕ disconnect</button>
              </div>
            </div>

            {/* File upload */}
            <div className="panel">
              <DropZone
                onFileAccepted={handleFileAccepted}
                uploading={uploading}
                uploadedFile={uploadedFile}
                disabled={running}
              />
              {uploadError && (
                <div style={{ padding: '8px 16px', fontSize: 11, color: 'var(--red)' }}>{uploadError}</div>
              )}
            </div>

            {/* Run buttons */}
            <div className="panel">
              <div className="panel-header"><span className="accent">▸</span> run_mode</div>
              <div className="run-buttons">
                {[
                  { mode: 'normal',    color: 'green', icon: '▶', label: 'RUN VERIFY',     desc: 'Full pipeline — golden DUT, normal mode' },
                  { mode: 'buggy',     color: 'amber', icon: '⚡', label: 'RUN BUGGY',      desc: 'Buggy DUT — carry-out hardwired to 0' },
                  { mode: 'breakdown', color: 'red',   icon: '◉', label: 'BREAKDOWN MODE', desc: 'Exhaustive 16×16 sweep — 256 test vectors' },
                ].map(({ mode, color, icon, label, desc }) => (
                  <button
                    key={mode}
                    className={`run-btn ${color}${running && activeMode === mode ? ' active' : ''}`}
                    onClick={() => handleRun(mode)}
                    disabled={running || !uploadedFile}
                  >
                    <span className="run-btn-icon">{icon}</span>
                    <span>
                      <span className="run-btn-label">{label}</span>
                      <span className="run-btn-desc">{desc}</span>
                    </span>
                  </button>
                ))}
              </div>
              {!uploadedFile && (
                <div style={{ padding: '8px 16px 14px', fontSize: 11, color: 'var(--text-dim)' }}>
                  Upload a file to enable run buttons.
                </div>
              )}
            </div>

            {/* Live log */}
            <div className="panel live-log">
              <div className="panel-header"><span className="accent">▸</span> pipeline_log</div>
              <LiveLog lines={logLines} loading={running} />
            </div>
          </div>

          {/* Right column */}
          <div className="dash-right">
            {showResults ? (
              <ResultsPanel report={report} error={runError} loading={running} />
            ) : (
              <div className="panel empty-state" style={{ minHeight: 320 }}>
                <div className="empty-state-icon">◈</div>
                <div className="empty-state-label">awaiting pipeline run</div>
              </div>
            )}
          </div>
        </div>

        {/* History table */}
        <div className="dash-full">
          <RunHistory history={history} />
        </div>
      </div>
    </div>
  );
}
