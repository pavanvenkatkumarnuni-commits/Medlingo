import { useEffect, useRef, useState } from 'react';
import client, { apiErrorMessage } from '../api/client';
import SafetyBanner from '../components/SafetyBanner';

export default function MedicalChat() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([{
    role: 'assistant',
    text: 'Hi, I’m MedLingo. I can explain general medical terms and medicine information in plain language. I can’t diagnose, prescribe, or replace a clinician or pharmacist.',
  }]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [voiceStatus, setVoiceStatus] = useState('');
  const [speakingIndex, setSpeakingIndex] = useState(null);
  const endRef = useRef(null);
  const recognitionRef = useRef(null);
  const SpeechRecognition = typeof window !== 'undefined'
    ? (window.SpeechRecognition || window.webkitSpeechRecognition)
    : null;

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages, loading]);

  useEffect(() => () => {
    recognitionRef.current?.stop();
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  }, []);

  async function sendMessage(e) {
    e?.preventDefault();
    const text = message.trim();
    if (text.length < 2 || loading) return;
    setError('');
    setMessages((items) => [...items, { role: 'user', text }]);
    setMessage('');
    setLoading(true);
    try {
      const { data } = await client.post('/chat', { message: text });
      setMessages((items) => [...items, {
        role: 'assistant',
        text: data.reply,
        urgent: data.urgent,
      }]);
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not send your message. Please try again.'));
    } finally {
      setLoading(false);
    }
  }

  function startVoiceInput() {
    if (!SpeechRecognition) {
      setVoiceStatus('Voice input is not supported by this browser. Try Chrome or Edge, or type your message.');
      return;
    }
    try {
      const recognition = new SpeechRecognition();
      recognition.lang = 'en-IN';
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      recognition.onstart = () => setVoiceStatus('Listening… speak clearly.');
      recognition.onerror = (event) => setVoiceStatus(
        event.error === 'not-allowed'
          ? 'Microphone permission was denied. Allow microphone access or type instead.'
          : 'Voice input stopped. You can try again or type instead.'
      );
      recognition.onresult = (event) => {
        const transcript = event.results?.[0]?.[0]?.transcript || '';
        setMessage((current) => [current, transcript].filter(Boolean).join(' '));
        setVoiceStatus('Voice text added. Review it before sending.');
      };
      recognition.onend = () => {
        recognitionRef.current = null;
      };
      recognitionRef.current = recognition;
      recognition.start();
    } catch {
      setVoiceStatus('Could not start the microphone. Please type your message instead.');
    }
  }

  function speak(text, index) {
    if (!('speechSynthesis' in window)) {
      setError('Spoken replies are not supported by this browser.');
      return;
    }
    window.speechSynthesis.cancel();
    if (speakingIndex === index) {
      setSpeakingIndex(null);
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-IN';
    utterance.onend = () => setSpeakingIndex(null);
    utterance.onerror = () => setSpeakingIndex(null);
    setSpeakingIndex(index);
    window.speechSynthesis.speak(utterance);
  }

  return (
    <main className="container" style={{ maxWidth: 820, paddingTop: '2rem', paddingBottom: '3rem' }}>
      <div style={{ marginBottom: '1.25rem' }}>
        <div className="hint" style={{ color: 'var(--ai-600)', fontWeight: 800, letterSpacing: '.08em' }}>MEDLINGO · VOICE + CHAT</div>
        <h1 style={{ marginBottom: 8 }}>Ask a medical information question</h1>
        <p style={{ margin: 0 }}>Get plain-language educational explanations and general medicine information. You can speak your question or listen to a reply.</p>
      </div>

      <section className="card" aria-label="Medical chat" style={{ padding: '1rem', marginBottom: '1rem' }}>
        <div aria-live="polite" style={{ display: 'flex', flexDirection: 'column', gap: 12, minHeight: 220, maxHeight: 460, overflowY: 'auto', padding: '0.25rem' }}>
          {messages.map((item, index) => (
            <div key={index} style={{
              alignSelf: item.role === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '90%', whiteSpace: 'pre-wrap', overflowWrap: 'anywhere',
              background: item.urgent ? '#FFF0F0' : item.role === 'user' ? 'var(--clinical-100)' : 'var(--surface)',
              border: item.urgent ? '1px solid #E7A5A5' : '1px solid var(--line)',
              borderRadius: 14, padding: '0.85rem 1rem',
            }}>
              <div className="hint" style={{ fontWeight: 700, marginBottom: 4 }}>
                {item.role === 'user' ? 'You' : item.urgent ? 'Urgent safety guidance' : 'MedLingo'}
              </div>
              <div>{item.text}</div>
              {item.role === 'assistant' && (
                <button type="button" className="btn btn-outline btn-sm" style={{ marginTop: 8 }}
                  onClick={() => speak(item.text, index)} aria-label="Read reply aloud">
                  {speakingIndex === index ? 'Stop audio' : '🔊 Read aloud'}
                </button>
              )}
            </div>
          ))}
          {loading && <div className="hint" role="status">Preparing a careful response…</div>}
          <div ref={endRef} />
        </div>

        <form onSubmit={sendMessage} style={{ borderTop: '1px solid var(--line)', paddingTop: '1rem', marginTop: '1rem' }}>
          <label htmlFor="medical-question" style={{ display: 'block', fontWeight: 700, marginBottom: 6 }}>Your question</label>
          <textarea id="medical-question" rows={3} maxLength={2000} value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="e.g. What does 'take with food' mean?"
            style={{ width: '100%', boxSizing: 'border-box' }} />
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginTop: 10 }}>
            <button type="submit" className="btn btn-ai" disabled={loading || message.trim().length < 2}>
              {loading ? 'Sending…' : 'Send question'}
            </button>
            <button type="button" className="btn btn-outline" onClick={startVoiceInput} disabled={loading || !SpeechRecognition}>
              🎙️ Speak question
            </button>
            <span className="hint">{message.length}/2000</span>
          </div>
          {voiceStatus && <p className="hint" role="status" style={{ marginBottom: 0 }}>{voiceStatus}</p>}
          {!SpeechRecognition && <p className="hint" style={{ marginBottom: 0 }}>Voice input is not supported in this browser. You can still type questions and use read-aloud replies.</p>}
          {error && <p className="error-text" role="alert">{error}</p>}
        </form>
      </section>

      <SafetyBanner />
      <p className="hint" style={{ marginTop: 10 }}>Voice features use your browser’s speech APIs. Microphone access may require HTTPS and permission. Avoid entering names, addresses, or other identifying patient details.</p>
    </main>
  );
}
