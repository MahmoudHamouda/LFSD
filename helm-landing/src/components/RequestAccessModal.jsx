import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';

export default function RequestAccessModal({ isOpen, onClose }) {
    const [status, setStatus] = useState('idle'); // idle, submitting, success
    const [formData, setFormData] = useState({
        email: '',
        intent: 'Personal use',
        message: ''
    });

    // Reset form when modal opens
    useEffect(() => {
        if (isOpen) {
            setStatus('idle');
            setFormData({ email: '', intent: 'Personal use', message: '' });
        }
    }, [isOpen]);

    const handleSubmit = (e) => {
        e.preventDefault();
        setStatus('submitting');

        // Simulate API call
        setTimeout(() => {
            setStatus('success');
        }, 1000);
    };

    if (!isOpen && status === 'idle') {
        // We can keep it in DOM for animation if we use CSS transition, 
        // but React rendering is easier to handle with conditional CSS classes 
        // or just checking isOpen prop in the container.
    }

    // Close on Escape
    useEffect(() => {
        const handleEsc = (e) => {
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [onClose]);

    return (
        <div className={`modal-overlay ${isOpen ? 'open' : ''}`} onClick={(e) => {
            if (e.target === e.currentTarget) onClose();
        }}>
            <div className="modal-content">
                <div className="flex justify-between items-center" style={{ marginBottom: '1.5rem' }}>
                    <h3 style={{ margin: 0 }}>Request access</h3>
                    <button onClick={onClose} style={{ padding: '4px', cursor: 'pointer' }}>
                        <X size={24} color="var(--color-text-muted)" />
                    </button>
                </div>

                {status === 'success' ? (
                    <div className="text-center" style={{ padding: '2rem 0' }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✨</div>
                        <h3 style={{ marginBottom: '0.5rem' }}>You're on the list</h3>
                        <p>Thanks for your interest. We'll be in touch soon.</p>
                        <button onClick={onClose} className="btn btn-primary" style={{ marginTop: '1rem' }}>
                            Close
                        </button>
                    </div>
                ) : (
                    <form onSubmit={handleSubmit} className="flex flex-col" style={{ gap: '1.25rem' }}>
                        <div className="flex flex-col gap-sm">
                            <label htmlFor="email" style={{ fontWeight: 500, fontSize: '0.9rem' }}>Email address</label>
                            <input
                                id="email"
                                type="email"
                                required
                                placeholder="you@example.com"
                                value={formData.email}
                                onChange={e => setFormData({ ...formData, email: e.target.value })}
                                style={{
                                    padding: '0.75rem',
                                    borderRadius: '8px',
                                    border: '1px solid var(--color-border)',
                                    fontSize: '1rem',
                                    fontFamily: 'inherit'
                                }}
                            />
                        </div>

                        <div className="flex flex-col gap-sm">
                            <label htmlFor="intent" style={{ fontWeight: 500, fontSize: '0.9rem' }}>I'm interested for...</label>
                            <select
                                id="intent"
                                value={formData.intent}
                                onChange={e => setFormData({ ...formData, intent: e.target.value })}
                                style={{
                                    padding: '0.75rem',
                                    borderRadius: '8px',
                                    border: '1px solid var(--color-border)',
                                    fontSize: '1rem',
                                    fontFamily: 'inherit',
                                    backgroundColor: 'white'
                                }}
                            >
                                <option>Personal use</option>
                                <option>Partner</option>
                                <option>Enterprise / institution</option>
                                <option>Just curious</option>
                            </select>
                        </div>

                        <div className="flex flex-col gap-sm">
                            <label htmlFor="message" style={{ fontWeight: 500, fontSize: '0.9rem' }}>
                                What are you hoping HELM helps with? <span style={{ color: 'var(--color-text-light)', fontWeight: 400 }}>(Optional)</span>
                            </label>
                            <textarea
                                id="message"
                                rows={3}
                                value={formData.message}
                                onChange={e => setFormData({ ...formData, message: e.target.value })}
                                style={{
                                    padding: '0.75rem',
                                    borderRadius: '8px',
                                    border: '1px solid var(--color-border)',
                                    fontSize: '1rem',
                                    fontFamily: 'inherit',
                                    resize: 'vertical'
                                }}
                            />
                        </div>

                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={status === 'submitting'}
                            style={{ marginTop: '0.5rem', width: '100%' }}
                        >
                            {status === 'submitting' ? 'Sending...' : 'Request Access'}
                        </button>
                    </form>
                )}
            </div>
        </div>
    );
}
