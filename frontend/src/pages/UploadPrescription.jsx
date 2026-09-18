import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import client, { apiErrorMessage } from '../api/client';
import LanguageSelector from '../components/LanguageSelector';
import SafetyBanner from '../components/SafetyBanner';

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf'];
const MAX_SIZE_MB = 10;

export default function UploadPrescription() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [language, setLanguage] = useState('en');
  const [error, setError] = useState('');
  const [stage, setStage] = useState('idle'); // idle | uploading | extracting | analyzing
  const inputRef = useRef(null);

  function validateAndSetFile(f) {
    setError('');
    if (!f) return;
    if (!ALLOWED_TYPES.includes(f.type)) {
      setError('Only JPG, PNG, and PDF files are supported.');
      return;
    }
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`File is too large. Maximum allowed size is ${MAX_SIZE_MB}MB.`);
      return;
    }
    setFile(f);
    setPreviewUrl(f.type === 'application/pdf' ? null : URL.createObjectURL(f));
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    validateAndSetFile(e.dataTransfer.files?.[0]);
  }

  async function handleAnalyze() {
    if (!file) return;
    setError('');
    setStage('uploading');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const { data: doc } = await client.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (doc.status === 'failed') {
        setError(doc.extraction_error || 'We could not read text from this file.');
        setStage('idle');
        return;
      }

      setStage('analyzing');
      const { data: analysis } = await client.post(`/analyze/document/${doc.id}`, { language });
      navigate(`/results/${analysis.id}`);
    } catch (err) {
      setError(apiErrorMessage(err));
      setStage('idle');
    }
  }

  const isBusy = stage !== 'idle';

  return (
    <div className="container" style={{ paddingTop: '2rem', paddingBottom: '3rem', maxWidth: 680 }}>
      <h1>Upload Prescription</h1>
      <p style={{ marginBottom: '1.25rem' }}>
        Upload a photo or PDF of a prescription and we'll extract the text automatically using OCR.
      </p>

      <div className="card" style={{ padding: '1.5rem' }}>
        {error && <div className="error-text" style={{ marginBottom: '1rem' }}>{error}</div>}

        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          style={{
            border: `2px dashed ${dragOver ? 'var(--ai-600)' : 'var(--line)'}`,
            borderRadius: 'var(--radius-md)',
            padding: file ? '1rem' : '2.5rem 1rem',
            textAlign: 'center',
            cursor: 'pointer',
            background: dragOver ? 'var(--ai-100)' : 'var(--surface)',
            transition: 'background-color 120ms ease, border-color 120ms ease',
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
            style={{ display: 'none' }}
            onChange={(e) => validateAndSetFile(e.target.files?.[0])}
          />

          {!file && (
            <>
              <div style={{ fontSize: '2rem', marginBottom: 8 }}>📄</div>
              <p style={{ margin: 0, fontWeight: 600, color: 'var(--ink)' }}>Drag & drop a prescription here</p>
              <p className="hint">or click to browse · JPG, PNG, or PDF · up to {MAX_SIZE_MB}MB</p>
            </>
          )}

          {file && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, textAlign: 'left' }}>
              {previewUrl ? (
                <img src={previewUrl} alt="Prescription preview" style={{ width: 90, height: 90, objectFit: 'cover', borderRadius: 8, border: '1px solid var(--line)' }} />
              ) : (
                <div style={{ width: 90, height: 90, borderRadius: 8, background: 'var(--clinical-100)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.6rem', color: 'var(--clinical-700)' }}>PDF</div>
              )}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{file.name}</div>
                <div className="hint">{(file.size / 1024).toFixed(0)} KB</div>
                <button
                  type="button"
                  className="btn btn-outline btn-sm"
                  style={{ marginTop: 6 }}
                  onClick={(e) => { e.stopPropagation(); setFile(null); setPreviewUrl(null); }}
                >
                  Remove
                </button>
              </div>
            </div>
          )}
        </div>

        <div style={{ marginTop: '1.25rem' }}>
          <LanguageSelector value={language} onChange={setLanguage} />
        </div>

        <button className="btn btn-ai btn-block" style={{ marginTop: '1.25rem' }} disabled={!file || isBusy} onClick={handleAnalyze}>
          {stage === 'uploading' && <><span className="spinner" /> Reading prescription…</>}
          {stage === 'analyzing' && <><span className="spinner" /> Analyzing with AI…</>}
          {stage === 'idle' && 'Analyze Prescription'}
        </button>
      </div>

      <div style={{ marginTop: '1.5rem' }}>
        <SafetyBanner compact />
      </div>
    </div>
  );
}
