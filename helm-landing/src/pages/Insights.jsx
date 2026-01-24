import React from 'react';
import { useOutletContext } from 'react-router-dom';

export default function Insights() {
    const { openModal } = useOutletContext();

    const topics = [
        "Decision-making in real life",
        "Financial wellbeing beyond wealth",
        "Technology that respects people"
    ];

    return (
        <div className="container section center-content">
            <div style={{ maxWidth: '700px', margin: '0 auto', textAlign: 'center' }}>
                <h1 style={{ marginBottom: '1.5rem' }}>Thinking out loud</h1>

                <div style={{ margin: '3rem 0', textAlign: 'left' }}>
                    <h3 style={{ marginBottom: '1.5rem', color: 'var(--color-text-muted)', fontSize: '1.25rem' }}>Short reflections on:</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                        {topics.map((topic, i) => (
                            <div key={i} className="insight-card" style={{
                                padding: '1.5rem',
                                border: '1px solid var(--color-border)',
                                borderRadius: '8px',
                                cursor: 'default'
                            }}>
                                <h3 style={{ margin: 0, fontSize: '1.25rem' }}>{topic}</h3>
                            </div>
                        ))}
                    </div>
                </div>

                <p style={{ fontSize: '1.25rem', marginBottom: '2rem' }}>No hype. Just perspective.</p>

                <button onClick={openModal} className="btn btn-primary">
                    Request access
                </button>
            </div>
        </div>
    );
}
