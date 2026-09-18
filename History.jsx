import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import client, { apiErrorMessage } from '../api/client';
import { LANGUAGES } from '../components/LanguageSelector';

export default function History() {
  const [items, setItems] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const { data } = await client.get('/history');
      setItems(data);
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not load history.'));
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleDelete(id, e) {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm('Delete this analysis from your history?')) return;
    await client.delete(`/history/${id}`);
    load();
  }

  return (
    <div className="container" style={{ paddingTop: '2rem', paddingBottom: '3rem', maxWidth: 780 }}>
      <h1>History</h1>
      <p style={{ marginBottom: '1.5rem' }}>Your previous prescription and text analyses, stored on this device.</p>

      {error && <div className="error-text" style={{ marginBottom: '1rem' }}>{error}</div>}

      {!items && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {[1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 84 }} />)}
        </div>
      )}

      {items && items.length === 0 && (
        <div className="empty-state card">
          <p>No analyses yet. Upload a prescription or enter medical text to get started.</p>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginTop: 10 }}>
            <Link to="/upload" className="btn btn-primary btn-sm">Upload Prescription</Link>
            <Link to="/analyze" className="btn btn-outline btn-sm">Enter Text</Link>
          </div>
        </div>
      )}

      {items && items.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {items.map((item) => (
            <Link
              key={item.id}
              to={`/results/${item.id}`}
              className="card"
              style={{ padding: '1.1rem 1.4rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, textDecoration: 'none', color: 'inherit', flexWrap: 'wrap' }}
            >
              <div style={{ minWidth: 0, flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span className="badge badge-neutral">{item.source_type === 'upload' ? 'File' : 'Text'}</span>
                  <span className="hint">{new Date(item.created_at).toLocaleString()}</span>
                  {item.language !== 'en' && <span className="badge badge-ai">{LANGUAGES[item.language] || item.language}</span>}
                </div>
                <div style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {item.source_label || 'Untitled analysis'}
                </div>
                <div className="hint">
                  {item.medicine_names.length > 0
                    ? `Medicines: ${item.medicine_names.join(', ')}`
                    : 'No medicines confidently identified'}
                </div>
              </div>
              <button className="btn btn-outline btn-sm" onClick={(e) => handleDelete(item.id, e)}>Delete</button>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
