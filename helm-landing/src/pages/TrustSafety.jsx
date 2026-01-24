import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { ShieldCheck, Lock, EyeOff, XCircle } from 'lucide-react';

export default function TrustSafety() {
    const { openModal } = useOutletContext();

    return (
        <div className="container section">
            <div style={{ maxWidth: '900px', margin: '0 auto' }}>
                <h1 className="text-center" style={{ marginBottom: '4rem' }}>Built for trust, not tricks</h1>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '2rem' }}>

                    <div className="trust-card">
                        <div className="icon-wrapper"><EyeOff /></div>
                        <h3>Your data is yours</h3>
                        <p>You decide. You can disconnect anytime.</p>
                    </div>

                    <div className="trust-card">
                        <div className="icon-wrapper"><ShieldCheck /></div>
                        <h3>Clear reasoning</h3>
                        <p>You can always see why something is suggested.</p>
                    </div>

                    <div className="trust-card">
                        <div className="icon-wrapper"><Lock /></div>
                        <h3>Security by default</h3>
                        <p>Strong protection and full activity records.</p>
                    </div>

                    <div className="trust-card">
                        <div className="icon-wrapper"><XCircle /></div>
                        <h3>What HELM will not do</h3>
                        <p>No acting without approval. No pushing products. No pretending.</p>
                    </div>

                </div>

                <div className="text-center" style={{ marginTop: '4rem' }}>
                    <button onClick={openModal} className="btn btn-primary">
                        Request access
                    </button>
                </div>
            </div>

            <style>{`
        .trust-card {
          padding: 2.5rem;
          background-color: white;
          border-radius: 12px;
          border: 1px solid var(--color-border);
          transition: transform var(--transition-smooth);
        }
        .trust-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 10px 30px -10px rgba(0,0,0,0.05);
        }
        .icon-wrapper {
          margin-bottom: 1.5rem;
          color: var(--color-text-main);
        }
      `}</style>
        </div>
    );
}
