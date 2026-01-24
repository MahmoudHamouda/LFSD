import React from 'react';
import { Link } from 'react-router-dom';

export default function Footer() {
    return (
        <footer className="container" style={{ padding: 'var(--spacing-xl) var(--spacing-sm)', borderTop: '1px solid var(--color-border)', marginTop: 'var(--spacing-xl)' }}>
            <div className="flex justify-between items-center" style={{ flexWrap: 'wrap', gap: '2rem' }}>
                <div className="flex flex-col gap-sm">
                    <span style={{ fontWeight: 600 }}>HELM</span>
                    <span style={{ color: 'var(--color-text-light)', fontSize: '0.9rem' }}>
                        © {new Date().getFullYear()} HELM. All rights reserved.
                    </span>
                </div>

                <div className="flex gap-md" style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>
                    <Link to="/trust-safety">Privacy</Link>
                    <Link to="/trust-safety">Terms</Link>
                    <a href="mailto:hello@helm.com">Contact</a>
                </div>
            </div>
        </footer>
    );
}
