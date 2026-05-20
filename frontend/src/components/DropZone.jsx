import { useState, useRef } from 'react';

const ALLOWED = ['.v', '.sv', '.json', '.yaml', '.yml'];
const TYPE_MAP = { '.v': 'verilog', '.sv': 'verilog', '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml' };

export default function DropZone({ onFileAccepted, uploading, uploadedFile, disabled }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const accept = (file) => {
    if (!file) return;
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ALLOWED.includes(ext)) {
      alert(`File type not supported. Use: ${ALLOWED.join(', ')}`);
      return;
    }
    onFileAccepted(file);
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    if (disabled) return;
    accept(e.dataTransfer.files[0]);
  };

  const onChange = (e) => accept(e.target.files[0]);

  if (uploading) {
    return (
      <div className="dropzone-wrap">
        <div className="panel-header"><span className="accent">▸</span> file</div>
        <div className="dropzone uploading">
          <div className="dz-spinner" />
          <div className="dz-uploading">uploading...</div>
        </div>
      </div>
    );
  }

  if (uploadedFile) {
    const ext = '.' + uploadedFile.filename.split('.').pop().toLowerCase();
    return (
      <div className="dropzone-wrap">
        <div className="panel-header"><span className="accent">▸</span> file</div>
        <div className="dropzone has-file" onClick={() => !disabled && inputRef.current?.click()}>
          <input ref={inputRef} type="file" accept={ALLOWED.join(',')} onChange={onChange} style={{ display: 'none' }} />
          <div className="dz-file-info">
            <span style={{ color: 'var(--green)', fontSize: 22 }}>✓</span>
            <div className="dz-file-name">{uploadedFile.filename}</div>
            <div className="dz-file-meta">
              <span className="dz-type-badge">{uploadedFile.detected_type}</span>
              <span style={{ fontSize: 10, color: 'var(--text-dim)' }}>
                {new Date(uploadedFile.upload_timestamp).toLocaleTimeString()}
              </span>
            </div>
            <button className="dz-change">↺ change file</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dropzone-wrap">
      <div className="panel-header"><span className="accent">▸</span> file</div>
      <div
        className={`dropzone${dragging ? ' dragging' : ''}`}
        onDragOver={(e) => { e.preventDefault(); if (!disabled) setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !disabled && inputRef.current?.click()}
      >
        <input ref={inputRef} type="file" accept={ALLOWED.join(',')} onChange={onChange} style={{ display: 'none' }} />
        <div className="dz-icon">⬆</div>
        <div className="dz-title">Drop hardware spec here</div>
        <div className="dz-types">.v &nbsp;·&nbsp; .sv &nbsp;·&nbsp; .json &nbsp;·&nbsp; .yaml</div>
        <div className="dz-size">max 10 MB &nbsp;·&nbsp; click to browse</div>
      </div>
    </div>
  );
}
