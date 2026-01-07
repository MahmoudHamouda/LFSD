/**
 * Auth0-based Login Page
 * Replaces custom password authentication with Auth0 Universal Login
 */
import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { useNavigate } from 'react-router-dom';
import styles from './Login.module.css';

const LoginAuth0: React.FC = () => {
    const { loginWithRedirect, isLoading } = useAuth0();
    const navigate = useNavigate();

    const handleLogin = async () => {
        await loginWithRedirect({
            appState: {
                returnTo: window.location.pathname
            }
        });
    };

    return (
        <div className={styles.container}>
            <div className={styles.card}>
                <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                    <h1 style={{ margin: 0, fontSize: '32px', fontWeight: 'bold' }}>HELM</h1>
                    <p style={{ color: 'var(--color-text-secondary)', marginTop: '8px' }}>
                        Your Guardian of Wellbeing
                    </p>
                </div>

                <div style={{ marginTop: '32px' }}>
                    <button
                        onClick={handleLogin}
                        className={styles.button}
                        disabled={isLoading}
                        style={{
                            width: '100%',
                            padding: '12px 24px',
                            fontSize: '16px',
                            fontWeight: '600',
                            borderRadius: '8px',
                            border: 'none',
                            background: 'var(--color-accent-blue)',
                            color: 'white',
                            cursor: isLoading ? 'not-allowed' : 'pointer',
                            transition: 'all 0.2s ease',
                            opacity: isLoading ? 0.6 : 1
                        }}
                        onMouseOver={(e) => {
                            if (!isLoading) {
                                e.currentTarget.style.transform = 'translateY(-1px)';
                                e.currentTarget.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.3)';
                            }
                        }}
                        onMouseOut={(e) => {
                            e.currentTarget.style.transform = 'translateY(0)';
                            e.currentTarget.style.boxShadow = 'none';
                        }}
                    >
                        {isLoading ? 'Loading...' : 'Continue with Auth0'}
                    </button>

                    <p style={{
                        marginTop: '16px',
                        fontSize: '13px',
                        color: 'var(--color-text-secondary)',
                        textAlign: 'center'
                    }}>
                        Secure authentication powered by Auth0
                    </p>
                </div>

                <div style={{
                    marginTop: '40px',
                    padding: '16px',
                    background: 'var(--color-bg-tertiary)',
                    borderRadius: '8px',
                    fontSize: '13px',
                    color: 'var(--color-text-secondary)'
                }}>
                    <p style={{ margin: 0, lineHeight: '1.5' }}>
                        <strong>New to HELM?</strong> You'll be able to create an account after clicking "Continue with Auth0"
                    </p>
                </div>
            </div>
        </div>
    );
};

export default LoginAuth0;
