import React from 'react';
import { ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

const Products = () => {
    return (
        <div className="container section">
            <div className="hero-glow"></div>
            <h1 className="text-center">Our Products</h1>

            <div style={{ marginTop: '3rem' }}>
                <Link to="/helm" style={{ display: 'block' }}>
                    <div className="surface-1 card" style={{ padding: '3rem', cursor: 'pointer', border: '2px solid transparent' }}>
                        <div className="grid grid-cols-2 gap-md items-center">
                            <div>
                                <h2 style={{ fontSize: '2.5rem' }}>HELM</h2>
                                <p style={{ fontSize: '1.25rem' }}>Your personal command center for money and life.</p>
                                <span className="btn btn-primary" style={{ marginTop: '1rem' }}>
                                    Learn more <ArrowRight size={18} style={{ marginLeft: '0.5rem' }} />
                                </span>
                            </div>
                            <div style={{ background: 'white', height: '300px', borderRadius: '16px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                {/* Placeholder for HELM image */}
                                <img src="/screenshots/home_desktop.png" alt="HELM Desktop" style={{ maxHeight: '100%', maxWidth: '100%' }} />
                            </div>
                        </div>
                    </div>
                </Link>

                <div className="grid grid-cols-3 gap-md" style={{ marginTop: '2rem' }}>
                    <div className="card" style={{ opacity: 0.7 }}>
                        <h3>Productivity Tools</h3>
                        <p>Coming soon.</p>
                    </div>
                    <div className="card" style={{ opacity: 0.7 }}>
                        <h3>Money Tools</h3>
                        <p>Coming soon.</p>
                    </div>
                    <div className="card" style={{ opacity: 0.7 }}>
                        <h3>Lifestyle Utils</h3>
                        <p>Coming soon.</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Products;
