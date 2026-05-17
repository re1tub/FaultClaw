import { useEffect, useRef } from 'react';

export default function LiveLog({ lines, loading }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [lines]);

  return (
    <div className="panel live-log" style={{ marginTop: 12 }}>
      <div className="panel-header">
        <span className="accent">▸</span> pipeline_log
      </div>
      <div className="log-content">
        {lines.length === 0 ? (
          <div className="log-empty">// waiting for pipeline run</div>
        ) : (
          lines.map((line, i) => (
            <div
              key={i}
              className={`log-line${line.startsWith('> ERROR') ? ' error-line' : ''}`}
            >
              {line}
            </div>
          ))
        )}
        {loading && <span className="log-cursor" />}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
