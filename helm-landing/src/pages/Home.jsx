import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { ArrowRight, Eye, Scale, ArrowUpRight } from 'lucide-react';

export default function Home() {
    const { openModal } = useOutletContext();

    return (
        <div className="home">
            {/* Hero */}
            <section className="container section center-content" style={{ paddingBottom: '2rem' }}>
                <div style={{ maxWidth: '800px', margin: '0 auto' }}>
                    <h1 style={{ fontSize: 'clamp(2.5rem, 5vw, 4rem)', letterSpacing: '-0.03em', lineHeight: 1.1 }}>
                        Make better decisions with the life you already live.
                    </h1>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: 400, color: 'var(--color-text-muted)', marginTop: '1.5rem', marginBottom: '2rem' }}>
                        HELM helps you understand your money, time, and choices — and turns that understanding into clear, practical actions.
                    </h2>

                    <div style={{ margin: '3rem 0', fontSize: '1.125rem', lineHeight: 1.7, color: 'var(--color-text-main)' }}>
                        <p>Life is full of decisions:</p>
                        <ul style={{ listStyle: 'none', padding: 0, margin: '1.5rem 0', display: 'flex', flexDirection: 'column', gap: '0.5rem', color: 'var(--color-text-muted)' }}>
                            <li className="flex items-center gap-sm">
                                <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-text-light)' }}></span>
                                Can I afford this?
                            </li>
                            <li className="flex items-center gap-sm">
                                <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-text-light)' }}></span>
                                Am I over-stretching myself?
                            </li>
                            <li className="flex items-center gap-sm">
                                <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-text-light)' }}></span>
                                What should I focus on next?
                            </li>
                            <li className="flex items-center gap-sm">
                                <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-text-light)' }}></span>
                                Is there a better way to run my month?
                            </li>
                        </ul>
                        <p>
                            HELM connects the dots between your financial life, daily habits, and priorities — then helps you decide and act with confidence.
                        </p>
                        <p style={{ fontWeight: 500, marginTop: '1rem' }}>
                            No spreadsheets. No guesswork.
                        </p>
                    </div>

                    <button onClick={openModal} className="btn btn-primary" style={{ padding: '1rem 2rem', fontSize: '1.125rem' }}>
                        Request access <ArrowRight size={18} style={{ marginLeft: '8px' }} />
                    </button>
                </div>
            </section>

            {/* Three Blocks */}
            <section className="container section">
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                    gap: '2rem',
                    margin: '2rem 0'
                }}>
                    <div style={{ padding: '2rem', backgroundColor: 'var(--color-bg-alt)', borderRadius: '16px' }}>
                        <div style={{ marginBottom: '1.5rem', color: 'var(--color-text-muted)' }}>
                            <Eye size={32} strokeWidth={1.5} />
                        </div>
                        <h3>See clearly</h3>
                        <p>Bring information together to understand patterns, not just numbers.</p>
                    </div>

                    <div style={{ padding: '2rem', backgroundColor: 'var(--color-bg-alt)', borderRadius: '16px' }}>
                        <div style={{ marginBottom: '1.5rem', color: 'var(--color-text-muted)' }}>
                            <Scale size={32} strokeWidth={1.5} />
                        </div>
                        <h3>Decide calmly</h3>
                        <p>Think through trade-offs without pressure.</p>
                    </div>

                    <div style={{ padding: '2rem', backgroundColor: 'var(--color-bg-alt)', borderRadius: '16px' }}>
                        <div style={{ marginBottom: '1.5rem', color: 'var(--color-text-muted)' }}>
                            <ArrowUpRight size={32} strokeWidth={1.5} />
                        </div>
                        <h3>Act easily</h3>
                        <p>Move forward when you’re ready.</p>
                    </div>
                </div>

                <div className="text-center" style={{ marginTop: '3rem' }}>
                    <button onClick={openModal} className="btn btn-primary">
                        Request access
                    </button>
                </div>
            </section>

            {/* Trust Note */}
            <section className="container section text-center" style={{ paddingBottom: '6rem' }}>
                <h3 style={{ fontSize: '1.75rem', marginBottom: '1rem' }}>Designed with privacy, security, and restraint in mind.</h3>
                <p style={{ fontSize: '1.25rem', marginBottom: '2rem' }}>You stay in control. Always.</p>
                <button onClick={openModal} className="btn btn-primary">
                    Request access
                </button>
            </section>
        </div>
    );
}
