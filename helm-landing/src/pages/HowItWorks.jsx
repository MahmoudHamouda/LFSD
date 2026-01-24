import React from 'react';
import { useOutletContext } from 'react-router-dom';

export default function HowItWorks() {
    const { openModal } = useOutletContext();

    const steps = [
        {
            num: '01',
            title: 'You connect what matters',
            desc: 'You choose what HELM can see and use.'
        },
        {
            num: '02',
            title: 'HELM looks for meaning',
            desc: 'Patterns over time, not snapshots.'
        },
        {
            num: '03',
            title: 'You get clear options',
            desc: 'What’s happening, why it matters, what you can do.'
        },
        {
            num: '04',
            title: 'You decide, HELM supports',
            desc: 'You stay in control.'
        }
    ];

    return (
        <div className="container section">
            <div style={{ maxWidth: '800px', margin: '0 auto' }}>
                <h1 className="text-center" style={{ marginBottom: '4rem' }}>Simple on the surface.<br />Thoughtful underneath.</h1>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '3rem' }}>
                    {steps.map((step) => (
                        <div key={step.num} style={{
                            display: 'flex',
                            gap: '2rem',
                            alignItems: 'flex-start',
                            padding: '2rem',
                            backgroundColor: 'white',
                            borderRadius: '12px',
                            boxShadow: '0 4px 20px rgba(0,0,0,0.02)'
                        }}>
                            <span style={{
                                fontSize: '1.5rem',
                                fontWeight: 600,
                                color: 'var(--color-bg)',
                                backgroundColor: 'var(--color-text-main)',
                                width: '3rem',
                                height: '3rem',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                borderRadius: '50%',
                                flexShrink: 0
                            }}>
                                {step.num}
                            </span>
                            <div>
                                <h3 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{step.title}</h3>
                                <p style={{ margin: 0, fontSize: '1.125rem' }}>{step.desc}</p>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="text-center" style={{ marginTop: '4rem' }}>
                    <button onClick={openModal} className="btn btn-primary">
                        Request access
                    </button>
                </div>
            </div>
        </div>
    );
}
