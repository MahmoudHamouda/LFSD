import React from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const HelmProduct = () => {
    return (
        <div className="helm-product">
            <section className="section container text-center">
                <div className="hero-glow"></div>
                <Link to="/" className="btn btn-ghost" style={{ marginBottom: '1rem' }}>
                    <ArrowLeft size={16} style={{ marginRight: '0.5rem' }} /> Back to Helmory
                </Link>
                <h1>A clearer way to run your month.</h1>
                <p style={{ margin: '0 auto' }}>
                    HELM doesn’t tell you what to do. It helps you understand your situation — then supports you in choosing what makes sense for you.
                </p>
            </section>

            {/* Carousel / Screenshots */}
            <section className="container" style={{ marginBottom: '4rem' }}>
                <div className="surface-1" style={{ overflow: 'hidden' }}>
                    <h3 className="text-center" style={{ marginBottom: '2rem' }}>How it works</h3>

                    {/* Simple horizontal scroll for screenshots */}
                    <div className="flex gap-md" style={{ overflowX: 'auto', padding: '1rem', paddingBottom: '2rem' }}>
                        {/* Real app screenshots */}
                        <img src="/screenshots/home_gauges_mobile.png" alt="Score Dashboard" className="card" style={{ height: '500px', minWidth: '240px', objectFit: 'contain', background: 'white' }} />
                        <img src="/screenshots/dashboard_mobile.png" alt="Spending Dashboard" className="card" style={{ height: '500px', minWidth: '240px', objectFit: 'contain', background: 'white' }} />
                        <img src="/screenshots/chat_booking_mobile.png" alt="Chat Assistant" className="card" style={{ height: '500px', minWidth: '240px', objectFit: 'contain', background: 'white' }} />
                    </div>
                </div>
            </section>

            <section className="container section grid grid-cols-2 gap-lg">
                <div>
                    <h2>What HELM pays attention to</h2>
                    <ul style={{ listStyle: 'none' }}>
                        <li className="card" style={{ marginBottom: '1rem' }}>
                            <h3>Financial activity</h3>
                            <p style={{ margin: 0 }}>Syncs with your bank accounts safely.</p>
                        </li>
                        <li className="card" style={{ marginBottom: '1rem' }}>
                            <h3>Goals and preferences</h3>
                            <p style={{ margin: 0 }}>You define what matters.</p>
                        </li>
                        <li className="card">
                            <h3>Patterns over time</h3>
                            <p style={{ margin: 0 }}>Highlights trends you might miss.</p>
                        </li>
                    </ul>
                </div>

                <div>
                    <h2>Example moments</h2>
                    <div className="surface-1" style={{ padding: '2rem' }}>
                        <p style={{ fontStyle: 'italic', fontSize: '1.25rem', color: 'var(--color-text-main)' }}>“If I do this now, what happens later?”</p>
                        <hr style={{ border: 0, borderTop: '1px solid var(--color-border)', margin: '1.5rem 0' }} />
                        <p style={{ fontStyle: 'italic', fontSize: '1.25rem', color: 'var(--color-text-main)' }}>“Is this a good month to commit?”</p>
                        <hr style={{ border: 0, borderTop: '1px solid var(--color-border)', margin: '1.5rem 0' }} />
                        <p style={{ fontStyle: 'italic', fontSize: '1.25rem', color: 'var(--color-text-main)' }}>“What should I change first?”</p>
                    </div>
                </div>
            </section>

            <section className="section container text-center">
                <h2>Ready to start?</h2>
                <div className="flex justify-center gap-sm">
                    <a href="https://app.helmory.com/login?returnTo=%2Fsignup" className="btn btn-primary">Sign up now</a>
                </div>
            </section>
        </div>
    );
};

export default HelmProduct;
