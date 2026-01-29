import React from 'react';

const About = () => {
    return (
        <div className="container section">
            <div className="hero-glow"></div>
            <div style={{ maxWidth: '800px', margin: '0 auto' }}>
                <h1>Why Helmory exists</h1>
                <p style={{ fontSize: '1.5rem', color: 'var(--color-text-main)' }}>
                    Most tools focus on transactions. Most advice ignores context.
                </p>
                <p>
                    We build software that helps people think better — calmly, clearly, and honestly — about their lives.
                    We believe that when you see your patterns clearly, without judgment, you naturally make better decisions.
                </p>

                <div className="surface-1" style={{ marginTop: '3rem' }}>
                    <h3>Looking ahead</h3>
                    <p>Over time, our products should feel less like apps — and more like good habits.</p>
                </div>
            </div>
        </div>
    );
};

export default About;
