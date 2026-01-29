import React from 'react';
import { Lock, Shield, Eye } from 'lucide-react';

const Trust = () => {
    return (
        <div className="container section">
            <div className="hero-glow"></div>
            <div className="text-center" style={{ marginBottom: '4rem' }}>
                <h1>Built for trust, not tricks.</h1>
                <p style={{ margin: '0 auto' }}>Helmory products are not paid to push decisions. You stay in control.</p>
            </div>

            <div className="grid grid-cols-3 gap-lg">
                <div className="card">
                    <Shield size={48} style={{ marginBottom: '1rem', color: 'var(--color-primary)' }} />
                    <h3>Your data is yours</h3>
                    <p>We don't sell your personal data. You can export or delete it at any time.</p>
                </div>
                <div className="card">
                    <Eye size={48} style={{ marginBottom: '1rem', color: 'var(--color-primary)' }} />
                    <h3>Clear reasoning</h3>
                    <p>Our algorithms are explainable. We tell you why a recommendation was made.</p>
                </div>
                <div className="card">
                    <Lock size={48} style={{ marginBottom: '1rem', color: 'var(--color-primary)' }} />
                    <h3>Security by default</h3>
                    <p>Bank-grade encryption for all your financial connections.</p>
                </div>
            </div>
        </div>
    );
};

export default Trust;
