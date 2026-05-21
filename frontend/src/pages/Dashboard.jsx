import { useState, useEffect, useRef, useCallback } from 'react';
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
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploading, setUploading]       = useState(false);
  const [uploadError, setUploadError]   = useState('');
  const [running, setRunning]           = useState(false);
  const [activeMode, setActiveMode]     = useState(null);
  const [report, setReport]             = useState(null);
  const [runError, setRunError]         = useState(null);
  const [logLines, setLogLines]         = useState([]);
  const [history, setHistory]           = useState([]);
  const intervalRef = useRef(null);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/results`);
      setHistory(res.data);
    } catch {
      // history is non-critical
    }
  }, []);

  useEffect(() => {
    fetchHistory();
    return () => clearInterval(intervalRef.current);
  }, [fetchHistory]);

  const handleFileAccepted = async (file) => {
    setUploading(true);
    setUploadError('');
    setUploadedFile(null);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await axios.post(`${API_BASE}/upload`, formData);
      setUploadedFile(res.data);
    } catch (e) {
      setUploadError(e.response?.data?.detail || e.message);
    } finally {
      setUploading(false);
    }
  };

  const handleRun = useCallback(async (mode) => {
    if (!uploadedFile) return;
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
  }, [uploadedFile, fetchHistory]);

  const showResults = report || runError || running;

  return (
    <div>
      <NavBar />
      <div className="dash-page">
        <div className="dash-layout">

          {/* Left column */}
          <div className="dash-left">

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
