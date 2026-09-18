import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import client, { apiErrorMessage } from '../api/client';
import LanguageSelector, { LANGUAGES } from '../components/LanguageSelector';
import SafetyBanner from '../components/SafetyBanner';

export default function Results() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState('');
  const [showRawText, setShowRawText] = useState(false);

  const [activeLang, setActiveLang] = useState('en');
  const [translating, setTranslating] = useState(false);
  const [translatedView, setTranslatedView] = useState(null); // { explanation_text, terminology }

  const load = useCallback(async () => {
    try {
      const { data } = await client.get(`/history/${id}`);
      setAnalysis(data);
      setActiveLang(data.language || 'en');
      const existing = data.translations?.find((t) => t.language === data.language);
      if (data.language !== 'en' && existing) {
        setTranslatedView({ explanation_text: existing.translated_explanation, terminology: existing.translated_terminology });
      }
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not load this analysis.'));
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  async function handleLanguageChange(lang) {
    setActiveLang(lang);
    if (lang === 'en') { setTranslatedView(null); return; }

    const cached = analysis.translations?.find((t) => t.language === lang);
    if (cached) {
      setTranslatedView({ explanation_text: cached.translated_explanation, terminology: cached.translated_terminology });
      return;
    }

    setTranslating(true);
    setError('');
    try {
      const { data } = await client.post(`/translate/${id}`, { language: lang });
      setTranslatedView({ explanation_text: data.translated_explanation, terminology: data.translated_terminology });
      setAnalysis((a) => ({ ...a, translations: [...(a.translations || []), data] }));
    } catch (err) {
      setError(apiErrorMessage(err, 'Translation failed.'));
    } finally {
      setTranslating(false);
    }
  }

  async function handleDelete() {
    if (!confirm('Delete this analysis from your history?')) return;
    await client.delete(`/history/${id}`);
    navigate('/history');
  }

  if (error && !analysis) {
    return (
      <div className="container" style={{ paddingTop: '2rem' }}>
        <div className="error-text">{error}</div>
        <Link to="/" className="btn btn-outline" style={{ marginTop: '1rem' }}>Back to home</Link>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="container" style={{ paddingTop: '2rem' }}>
        <div className="skeleton" style={{ height: 40, width: 300, marginBottom: 16 }} />
        <div className="skeleton" style={{ height: 200, marginBottom: 16 }} />
        <div className="skeleton" style={{ height: 200 }} />
      </div>
    );
  }

  const displayExplanation = translatedView?.explanation_text ?? analysis.explanation_text;
  const displayTerminology = translatedView?.terminology?.length ? translatedView.terminology : analysis.terminology;

  return (
    <div className="container" style={{ paddingTop: '2rem', paddingBottom: '3rem', maxWidth: 780 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12, marginBottom: '1.25rem' }}>
        <div>
          <h1 style={{ marginBottom: 4 }}>Analysis results</h1>
          <p style={{ margin: 0 }}>
            {analysis.source_type === 'upload' ? 'From uploaded file' : 'From pasted text'} · {new Date(analysis.created_at).toLocaleString()}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-outline btn-sm" onClick={handleDelete}>Delete</button>
        </div>
      </div>

      {analysis.ai_provider_used === 'offline' && (
        <div className="safety-banner" style={{ marginBottom: '1.25rem' }}>
          <span aria-hidden="true">ℹ️</span>
          <span>
            This result uses rule-based extraction only — no AI provider is currently configured
            on the server, so explanations are limited to reference data for recognized medicines.
            Configure <code>ANTHROPIC_API_KEY</code> in the backend for full AI-generated explanations.
          </span>
        </div>
      )}

      {error && <div className="error-text" style={{ margin: '1rem 0' }}>{error}</div>}

      <div className="card" style={{ padding: '1.5rem', marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: 12, marginBottom: '1rem' }}>
          <h3 style={{ margin: 0 }}>Plain-language explanation</h3>
          <div style={{ width: 220 }}>
            <LanguageSelector value={activeLang} onChange={handleLanguageChange} label="" />
          </div>
        </div>
        {translating ? (
          <div className="skeleton" style={{ height: 80 }} />
        ) : (
          <p style={{ whiteSpace: 'pre-line', color: 'var(--ink)' }}>{displayExplanation || 'No explanation available.'}</p>
        )}
        {activeLang !== 'en' && !translating && (
          <p className="hint">Shown in {LANGUAGES[activeLang]}. Medicine names and dosage numbers are kept as originally written.</p>
        )}
      </div>

      {analysis.warnings?.length > 0 && (
        <div className="card" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.25rem', borderColor: '#EAD3A3', background: 'var(--amber-100)' }}>
          <h3 style={{ margin: '0 0 0.5rem 0', color: '#6B4E14' }}>Uncertainties & warnings</h3>
          <ul style={{ margin: 0, paddingLeft: '1.2rem', color: '#6B4E14' }}>
            {analysis.warnings.map((w, i) => <li key={i} style={{ marginBottom: 4 }}>{w}</li>)}
          </ul>
        </div>
      )}

      <h3 style={{ marginBottom: '0.75rem' }}>Medicines identified ({analysis.medicines.length})</h3>
      {analysis.medicines.length === 0 ? (
        <div className="empty-state card" style={{ marginBottom: '1.25rem' }}>
          <p>No medicines could be confidently identified from this text.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: '1.25rem' }}>
          {analysis.medicines.map((m) => <MedicineCard key={m.id} medicine={m} />)}
        </div>
      )}

      {analysis.conditions?.length > 0 && (
        <div className="card" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.25rem' }}>
          <h3>Conditions mentioned</h3>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {analysis.conditions.map((c, i) => <span key={i} className="badge badge-neutral" style={{ textTransform: 'capitalize' }}>{c}</span>)}
          </div>
        </div>
      )}

      {displayTerminology?.length > 0 && (
        <div className="card" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.25rem' }}>
          <h3>Terminology explained</h3>
          <dl style={{ margin: 0 }}>
            {displayTerminology.map((t, i) => (
              <div key={i} style={{ marginBottom: 10 }}>
                <dt style={{ fontWeight: 700 }}>{t.term}</dt>
                <dd style={{ margin: '2px 0 0 0', color: 'var(--ink-soft)' }}>{t.meaning}</dd>
              </div>
            ))}
          </dl>
        </div>
      )}

      <div className="card" style={{ padding: '1rem 1.5rem', marginBottom: '1.25rem' }}>
        <button className="btn btn-outline btn-sm" onClick={() => setShowRawText((s) => !s)}>
          {showRawText ? 'Hide' : 'Show'} original extracted text
        </button>
        {showRawText && (
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.85rem', color: 'var(--ink-soft)', marginTop: 10, fontFamily: 'inherit' }}>
            {analysis.raw_text}
          </pre>
        )}
      </div>

      <SafetyBanner />
    </div>
  );
}

function MedicineCard({ medicine }) {
  const confClass = { high: 'badge-high', medium: 'badge-medium', low: 'badge-low' }[medicine.confidence] || 'badge-neutral';
  return (
    <div className="card" style={{ padding: '1.25rem 1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 10, marginBottom: 8 }}>
        <h3 style={{ margin: 0 }}>{medicine.name}</h3>
        <span className={`badge ${confClass}`}>{medicine.confidence} confidence</span>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem 1.5rem', marginBottom: 10, fontSize: '0.88rem' }}>
        <Field label="Dosage" value={medicine.dosage} />
        <Field label="Frequency" value={medicine.frequency} />
        <Field label="Duration" value={medicine.duration} />
      </div>

      {medicine.instructions && (
        <p style={{ fontSize: '0.9rem', margin: '0 0 8px 0' }}><strong>Instructions:</strong> {medicine.instructions}</p>
      )}
      {medicine.common_use && (
        <p style={{ fontSize: '0.9rem', margin: '0 0 8px 0' }}><strong>Commonly used for:</strong> {medicine.common_use}</p>
      )}
      {medicine.plain_explanation && (
        <p style={{ fontSize: '0.9rem', margin: 0, color: 'var(--ink)' }}>{medicine.plain_explanation}</p>
      )}
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div>
      <div className="hint" style={{ marginBottom: 2 }}>{label}</div>
      <div style={{ fontWeight: 600 }}>{value || <span style={{ color: 'var(--ink-soft)', fontWeight: 400 }}>Not identified</span>}</div>
    </div>
  );
}
