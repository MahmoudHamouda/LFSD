import React from 'react';
import { useOutletContext } from 'react-router-dom';

export default function Product() {
    const { openModal } = useOutletContext();

    return (
        <div className="container section">
            <div style={{ maxWidth: '800px', margin: '0 auto' }}>
                <h1 style={{ marginBottom: '1.5rem' }}>A clearer way to think about your life decisions</h1>

                <p className="intro-text" style={{ fontSize: '1.25rem', color: 'var(--color-text-main)', marginBottom: '3rem' }}>
                    HELM doesn’t tell you what to do. It helps you understand your situation — then supports you in choosing what makes sense for you.
                </p>

                <div style={{ display: 'grid', gap: '4rem', marginTop: '4rem' }}>

                    <div>
                        <h2 style={{ fontSize: '1.75rem', borderBottom: '1px solid var(--color-border)', paddingBottom: '1rem' }}>What HELM looks at</h2>
                        <ul style={{ marginTop: '1.5rem', listStyle: 'none', padding: 0 }}>
                            <li className="list-item">Financial activity</li>
                            <li className="list-item">Goals and preferences</li>
                            <li className="list-item">Patterns over time</li>
                        </ul>
                    </div>

                    <div>
                        <h2 style={{ fontSize: '1.75rem', borderBottom: '1px solid var(--color-border)', paddingBottom: '1rem' }}>What HELM helps you do</h2>
                        <ul style={{ marginTop: '1.5rem', listStyle: 'none', padding: 0 }}>
                            <li className="list-item">Understand affordability without stress</li>
                            <li className="list-item">Plan in a way that fits real life</li>
                            <li className="list-item">Follow through calmly and practically</li>
                        </ul>
                    </div>

                    <div>
                        <h2 style={{ fontSize: '1.75rem', borderBottom: '1px solid var(--color-border)', paddingBottom: '1rem' }}>Example moments</h2>
                        <ul style={{ marginTop: '1.5rem', listStyle: 'none', padding: 0, fontStyle: 'italic', color: 'var(--color-text-muted)' }}>
                            <li className="list-item">“If I do this now, what happens later?”</li>
                            <li className="list-item">“Is this a good month to commit?”</li>
                            <li className="list-item">“What should I change first?”</li>
                        </ul>
                    </div>

                </div>

                <div style={{ marginTop: '4rem' }}>
                    <button onClick={openModal} className="btn btn-primary">
                        Request access
                    </button>
                </div>
            </div>

            <style>{`
        .list-item {
          padding: 0.75rem 0;
          font-size: 1.125rem;
          border-bottom: 1px dashed var(--color-border);
        }
        .list-item:last-child {
          border-bottom: none;
        }
      `}</style>
        </div>
    );
}
