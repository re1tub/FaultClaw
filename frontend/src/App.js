import { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import Header from './components/Header';
import ControlPanel from './components/ControlPanel';
import ResultsPanel from './components/ResultsPanel';
import HistoryPanel from './components/HistoryPanel';
import LiveLog from './components/LiveLog';
import './App.css';

const API_BASE = 'http://localhost:8000';

const LOG_SEQUENCES = {
  verify: [
    '> initializing pipeline...',
    '> agent_1: parsing spec [adder_4bit.v]',
    '> agent_1: 2 inputs detected — a[3:0], b[3:0]',
    '> agent_1: 1 output detected — sum[4:0]',
    '> agent_2: generating adversarial test suite',
    '> agent_2: injecting edge + carry-overflow vectors',
    '> agent_3: golden DUT loaded',
    '> agent_3: running verification pass...',
    '> memory: persisting run record',
    '> pipeline complete.',
  ],
  buggy: [
    '> initializing pipeline...',
    '> agent_1: parsing spec [adder_4bit.v]',
    '> agent_1: 2 inputs detected — a[3:0], b[3:0]',
    '> agent_2: generating adversarial test suite',
    '> agent_2: targeting carry-out overflow vectors',
    '> agent_3: BUGGY DUT loaded [carry-out hardwired to 0]',
    '> agent_3: fault injection active',
    '> agent_3: running verification pass...',
    '> memory: persisting run record',
    '> pipeline complete.',
  ],
  breakdown: [
    '> initializing pipeline...',
    '> agent_1: parsing spec [adder_4bit.v]',
    '> agent_2: BREAKDOWN MODE — exhaustive 16×16 sweep',
    '> agent_2: generating 256 test vectors',
    '> agent_2: full input space covered',
    '> agent_3: golden DUT loaded',
    '> agent_3: running 256 tests...',
    '> memory: persisting run record',
    '> pipeline complete.',
  ],
};

function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [report, setReport] = useState(null);
  const [history, setHistory] = useState([]);
  const [logLines, setLogLines] = useState([]);
  const [activeMode, setActiveMode] = useState(null);
  const intervalRef = useRef(null);

  const fetchHistory = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/history`);
      setHistory([...res.data].reverse());
    } catch {
      // history is non-critical
    }
  }, []);

  useEffect(() => {
    fetchHistory();
    return () => clearInterval(intervalRef.current);
  }, [fetchHistory]);

  const runPipeline = useCallback(async (endpoint, mode) => {
    clearInterval(intervalRef.current);

    setLoading(true);
    setError(null);
    setReport(null);
    setActiveMode(mode);

    const sequence = LOG_SEQUENCES[mode];
    let idx = 0;
    setLogLines([sequence[idx++]]);

    intervalRef.current = setInterval(() => {
      if (idx < sequence.length) {
        setLogLines(prev => [...prev, sequence[idx++]]);
      } else {
        clearInterval(intervalRef.current);
      }
    }, 380);

    try {
      const res = await axios.post(`${API_BASE}${endpoint}`);
      clearInterval(intervalRef.current);
      setLogLines(sequence);
      setReport(res.data);
      fetchHistory();
    } catch (e) {
      clearInterval(intervalRef.current);
      const msg = e.response?.data?.error || e.message;
      setLogLines(prev => [...prev, `> ERROR: ${msg}`]);
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [fetchHistory]);

  const handlers = {
    onVerify:    () => runPipeline('/verify',           'verify'),
    onBuggy:     () => runPipeline('/verify/buggy',     'buggy'),
    onBreakdown: () => runPipeline('/verify/breakdown', 'breakdown'),
  };

  const showResults = report || error || loading;

  return (
    <div className="app">
      <Header />
      <div className="main-grid">
        <div className="left-col">
          <ControlPanel loading={loading} activeMode={activeMode} {...handlers} />
          <LiveLog lines={logLines} loading={loading} />
        </div>
        <div className="right-col">
          {showResults && (
            <ResultsPanel report={report} error={error} loading={loading} />
          )}
          {!showResults && <EmptyState />}
        </div>
      </div>
      <HistoryPanel history={history} />
    </div>
  );
}

function EmptyState() {
  return (
    <div className="panel" style={{ minHeight: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 12, color: 'var(--text-dim)' }}>
      <div style={{ fontSize: 32, color: 'var(--border-mid)' }}>◈</div>
      <div style={{ fontSize: 11, letterSpacing: 2, textTransform: 'uppercase' }}>
        awaiting pipeline run
      </div>
    </div>
  );
}

export default App;
