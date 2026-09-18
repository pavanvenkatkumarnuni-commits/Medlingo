export const LANGUAGES = {
  en: 'English', te: 'Telugu', hi: 'Hindi', ta: 'Tamil', kn: 'Kannada',
  ml: 'Malayalam', bn: 'Bengali', mr: 'Marathi', gu: 'Gujarati', pa: 'Punjabi',
  ur: 'Urdu', es: 'Spanish', fr: 'French', ar: 'Arabic', zh: 'Chinese (Simplified)',
};

export default function LanguageSelector({ value, onChange, label = 'Explanation language' }) {
  return (
    <div className="field" style={{ marginBottom: 0 }}>
      {label && <label>{label}</label>}
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {Object.entries(LANGUAGES).map(([code, name]) => (
          <option key={code} value={code}>{name}</option>
        ))}
      </select>
    </div>
  );
}
