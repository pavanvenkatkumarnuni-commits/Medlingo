import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import client, { apiErrorMessage } from '../api/client';
import LanguageSelector from '../components/LanguageSelector';
import SafetyBanner from '../components/SafetyBanner';

const MAX_CHARS = 8000;
const EXAMPLE = 'Tab. Amoxicillin 500mg — 1 tablet three times a day for 7 days for throat infection. Tab. Paracetamol 650mg as needed for fever. Avoid alcohol. Take with food.';

export default function TextAnalyzer() {
  const navigate = useNavigate();
  const [text, setText] = useState('');
  const [language, setLanguage] = useState('en');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleAnalyze(e) {
    e.preventDefault();
    setError('');
    const trimmed = text.trim();
    if (trimmed.length < 3) {
      setError('Please enter at least a few words of medical text.');
      return;
    }
    if (trimmed.length > MAX_CHARS) {
      setError(`Text is too long. Please keep it under ${MAX_CHARS} characters.`);
      return;
    }

    setLoading(true);
    try {
      const { data } = await client.post('/analyze/text', { text: trimmed, language });
      navigate(`/results/${data.id}`);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container" style={{ paddingTop: '2rem', paddingBottom: '3rem', maxWidth: 680 }}>
      <h1>Enter Medical Text</h1>
      <p style={{ marginBottom: '1.25rem' }}>
        Paste prescription text or medical terminology below and we'll extract and explain it in plain language.
      </p>

      <form onSubmit={handleAnalyze} className="card" style={{ padding: '1.5rem' }}>
        {error && <div className="error-text" style={{ marginBottom: '1rem' }}>{error}</div>}

        <div className="field">
          <label>Medical text</label>
          <textarea
            rows={8}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="e.g. Tab. Amoxicillin 500mg 1-0-1 for 5 days for throat infection…"
            maxLength={MAX_CHARS}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <button type="button" className="hint" style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--clinical-700)', textAlign: 'left', padding: 0 }} onClick={() => setText(EXAMPLE)}>
              Use an example
            </button>
            <span className="hint">{text.length}/{MAX_CHARS}</span>
          </div>
        </div>

        <div style={{ marginBottom: '1.25rem' }}>
          <LanguageSelector value={language} onChange={setLanguage} />
        </div>

        <button className="btn btn-ai btn-block" disabled={loading}>
          {loading ? <><span className="spinner" /> Analyzing with AI…</> : 'Analyze Text'}
        </button>
      </form>

      <div style={{ marginTop: '1.5rem' }}>
        <SafetyBanner compact />
      </div>
    </div>
  );
}
