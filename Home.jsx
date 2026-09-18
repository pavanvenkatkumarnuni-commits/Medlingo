import { Link } from 'react-router-dom';
import SafetyBanner from '../components/SafetyBanner';

export default function Home() {
  return (
    <div className="container" style={{ paddingTop: '3rem', paddingBottom: '3rem' }}>
      <div style={{ textAlign: 'center', maxWidth: 640, margin: '0 auto 2.5rem' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: 'var(--ai-100)', color: 'var(--ai-600)', fontSize: '0.78rem', fontWeight: 700, padding: '0.35em 0.9em', borderRadius: 999, marginBottom: '1rem' }}>
          AI-POWERED · PLAIN-LANGUAGE MEDICAL HELP
        </div>
        <h1>Understand your medical information in simple language.</h1>
        <p>
          Upload a prescription or paste medical text, and MedLingo AI will identify medicines,
          dosages and instructions, explain them in plain language, and translate the explanation
          into your language.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem', marginBottom: '2.5rem' }}>
        <ActionCard
          to="/upload"
          icon={<UploadIcon />}
          title="Upload Prescription"
          desc="Upload a photo or PDF of a prescription. We'll extract the text automatically."
          cta="Upload a file"
        />
        <ActionCard
          to="/analyze"
          icon={<TextIcon />}
          title="Enter Medical Text"
          desc="Paste prescription text or medical terminology directly for instant analysis."
          cta="Enter text"
        />
        <ActionCard
          to="/history"
          icon={<HistoryIcon />}
          title="View History"
          desc="Revisit past analyses — see detected medicines and reopen full explanations."
          cta="View history"
        />
      </div>

      <div style={{ maxWidth: 720, margin: '0 auto' }}>
        <SafetyBanner />
      </div>
    </div>
  );
}

function ActionCard({ to, icon, title, desc, cta }) {
  return (
    <Link to={to} className="card" style={{ padding: '1.5rem', textDecoration: 'none', color: 'inherit', display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{
        width: 44, height: 44, borderRadius: 10, background: 'var(--clinical-100)', color: 'var(--clinical-700)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        {icon}
      </div>
      <h3 style={{ margin: 0 }}>{title}</h3>
      <p style={{ margin: 0, fontSize: '0.9rem', flex: 1 }}>{desc}</p>
      <span style={{ color: 'var(--clinical-700)', fontWeight: 600, fontSize: '0.88rem' }}>{cta} →</span>
    </Link>
  );
}

function UploadIcon() {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M12 16V4M12 4l-4 4M12 4l4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /><path d="M4 16v3a2 2 0 002 2h12a2 2 0 002-2v-3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>;
}
function TextIcon() {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M4 6h16M4 12h16M4 18h10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>;
}
function HistoryIcon() {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="13" r="8" stroke="currentColor" strokeWidth="2" /><path d="M12 9v4l3 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /><path d="M9 3l3-1 3 1" stroke="currentColor" strokeWidth="2" strokeLinecap="round" /></svg>;
}
