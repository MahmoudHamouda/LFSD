import React from 'react';
import { useOutletContext } from 'react-router-dom';

export default function About() {
    const { openModal } = useOutletContext();

    return (
        <div className="container section center-content">
            <div style={{ maxWidth: '700px', margin: '0 auto', textAlign: 'center' }}>
                <h1 style={{ marginBottom: '2rem' }}>Why HELM exists</h1>

                <div style={{ fontSize: '1.25rem', textAlign: 'left', lineHeight: 1.8 }}>
                    <p style={{ marginBottom: '1.5rem' }}>Most tools focus on transactions.<br />Most advice ignores context.</p>

                    <p style={{ marginBottom: '3rem', fontSize: '1.5rem', fontWeight: 500, color: 'var(--color-text-main)' }}>
                        HELM exists to help people think better — calmly, clearly, and honestly — about their lives.
                    </p>

                    <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>Long view</h3>
                    <p>
                        Over time, HELM learns with you — not to control, but to support better choices as life changes.
                    </p>
                </div>

                <div style={{ marginTop: '4rem' }}>
                    <button onClick={openModal} className="btn btn-primary">
                        Request access
                    </button>
                </div>
            </div>
        </div>
    );
}
