import React from 'react';
import { useOutletContext } from 'react-router-dom';

export default function Partners() {
    const { openModal } = useOutletContext();

    return (
        <div className="container section center-content">
            <div style={{ maxWidth: '700px', margin: '0 auto', textAlign: 'center' }}>
                <h1 style={{ marginBottom: '1.5rem' }}>Built to work with others — carefully</h1>

                <p style={{ fontSize: '1.25rem', marginBottom: '3rem' }}>
                    HELM connects people to services only when it genuinely makes sense.
                </p>

                <div style={{ textAlign: 'left', backgroundColor: 'var(--color-bg-alt)', padding: '2.5rem', borderRadius: '16px', marginBottom: '3rem' }}>
                    <h3 style={{ marginBottom: '1.5rem' }}>Why partner</h3>
                    <ul style={{ listStyle: 'none', padding: 0 }}>
                        <li style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center' }}>
                            <span style={{ marginRight: '1rem', color: 'var(--color-primary)' }}>•</span>
                            Reach people at the moment decisions are made
                        </li>
                        <li style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center' }}>
                            <span style={{ marginRight: '1rem', color: 'var(--color-primary)' }}>•</span>
                            Consent-based, transparent engagement
                        </li>
                        <li style={{ marginBottom: '0', display: 'flex', alignItems: 'center' }}>
                            <span style={{ marginRight: '1rem', color: 'var(--color-primary)' }}>•</span>
                            Focus on usefulness, not noise
                        </li>
                    </ul>
                </div>

                <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                    <button onClick={openModal} className="btn" style={{ backgroundColor: 'var(--color-text-main)', color: 'white' }}>
                        Become a partner
                    </button>
                    <button onClick={openModal} className="btn" style={{ border: '1px solid var(--color-border)' }}>
                        Request access
                    </button>
                </div>
            </div>
        </div>
    );
}
