import { NavLink } from 'react-router-dom';

export default function Navbar() {
  const linkStyle = ({ isActive }) => ({
    padding: '0.5em 0.2em',
    fontWeight: 600,
    fontSize: '0.9rem',
    color: isActive ? 'var(--clinical-700)' : 'var(--ink-soft)',
    borderBottom: isActive ? '2px solid var(--clinical-700)' : '2px solid transparent',
    textDecoration: 'none',
  });

  return (
    <header style={{ borderBottom: '1px solid var(--line)', background: 'var(--surface-raised)', position: 'sticky', top: 0, zIndex: 30 }}>
      <div className="container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 64 }}>
        <NavLink to="/" style={{ display: 'flex', alignItems: 'center', gap: 9, textDecoration: 'none' }}>
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect x="2" y="2" width="24" height="24" rx="7" fill="#14547A" />
            <path d="M14 8v12M8 14h12" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
            <circle cx="20.5" cy="7.5" r="3.5" fill="#5B5FEF" />
          </svg>
          <span style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.15rem', color: 'var(--clinical-900)' }}>
            MedLingo <span style={{ color: 'var(--ai-600)' }}>AI</span>
          </span>
        </NavLink>

        <nav style={{ display: 'flex', gap: '1.5rem' }}>
          <NavLink to="/" style={linkStyle} end>Home</NavLink>
          <NavLink to="/upload" style={linkStyle}>Upload Prescription</NavLink>
          <NavLink to="/analyze" style={linkStyle}>Enter Text</NavLink>
          <NavLink to="/history" style={linkStyle}>History</NavLink>
        </nav>
      </div>
    </header>
  );
}
