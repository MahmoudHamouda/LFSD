import React, { useEffect, useState } from 'react';
import { getConsent, setConsent } from '../../api/api';

/**
 * Responsible-AI consent banner.
 *
 * When the governance layer is enabled server-side, AI advisory is gated on the
 * user having granted consent for their financial data to be analyzed. This
 * banner checks consent on mount and lets the user grant (or withdraw) it.
 *
 * If governance is OFF, the endpoint reports `has_consent: true`, so the banner
 * simply never appears — no behavior change.
 */
const ConsentBanner: React.FC = () => {
  const [status, setStatus] = useState<'loading' | 'needed' | 'granted' | 'hidden'>('loading');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let active = true;
    getConsent().then((res) => {
      if (!active) return;
      if (res == null) setStatus('hidden'); // not logged in / endpoint unavailable
      else setStatus(res.has_consent ? 'hidden' : 'needed');
    });
    return () => {
      active = false;
    };
  }, []);

  const grant = async () => {
    setSaving(true);
    const ok = await setConsent(true);
    setSaving(false);
    setStatus(ok ? 'granted' : 'needed');
    if (ok) setTimeout(() => setStatus('hidden'), 1500);
  };

  if (status === 'loading' || status === 'hidden') return null;

  return (
    <div
      role="region"
      aria-label="AI advisory consent"
      style={{
        margin: '12px 16px',
        padding: '14px 16px',
        borderRadius: 12,
        border: '1px solid rgba(120,120,140,0.35)',
        background: 'rgba(120,120,200,0.08)',
        display: 'flex',
        gap: 14,
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
      }}
    >
      <div style={{ fontSize: 14, lineHeight: 1.4, maxWidth: 620 }}>
        <strong>Enable AI-assisted guidance</strong>
        <div style={{ opacity: 0.8, marginTop: 2 }}>
          {status === 'granted'
            ? 'Thanks — consent recorded. You can withdraw it anytime.'
            : 'I need your consent to analyze your financial data to answer questions. Your data is minimized and personal identifiers are redacted before any AI processing. You can withdraw consent at any time.'}
        </div>
      </div>
      {status === 'needed' && (
        <button
          onClick={grant}
          disabled={saving}
          style={{
            padding: '9px 18px',
            borderRadius: 999,
            border: 'none',
            cursor: saving ? 'default' : 'pointer',
            fontWeight: 600,
            fontSize: 14,
            color: '#fff',
            background: saving ? '#8888aa' : '#5b5be6',
            whiteSpace: 'nowrap',
          }}
        >
          {saving ? 'Saving…' : 'I consent'}
        </button>
      )}
    </div>
  );
};

export default ConsentBanner;
