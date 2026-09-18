export default function SafetyBanner({ compact }) {
  return (
    <div className="safety-banner" role="note">
      <span aria-hidden="true">⚠️</span>
      <span>
        <strong>Informational purposes only.</strong>{' '}
        {compact
          ? 'This does not replace advice from a qualified healthcare professional.'
          : 'MedLingo AI helps you understand medical information in plain language, but it does not replace advice, diagnosis, or treatment from a qualified healthcare professional. Always confirm medication details with your doctor or pharmacist.'}
      </span>
    </div>
  );
}
