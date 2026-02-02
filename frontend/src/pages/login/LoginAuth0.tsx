/**
 * Auth0-based Login Page
 * Replaces custom password authentication with Auth0 Universal Login
 */
import React from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import styles from './Login.module.css';
import logoUrl from '../../assets/helm-logo.svg';

const LoginAuth0: React.FC = () => {
    const { loginWithRedirect, isLoading } = useAuth0();

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
                <div style={{ textAlign: 'center', marginBottom: '32px' }}>
                    <img src={logoUrl} alt="HELM" className={styles.logo} style={{ width: '80px', height: '80px', marginBottom: '16px' }} />
                    <p style={{ color: 'var(--color-text-secondary)', marginTop: '8px', fontSize: '18px', fontWeight: '500' }}>
                        Your Guardian of Wellbeing
                    </p>
                </div>

                <div style={{ marginTop: '32px' }}>
                    <button
                        onClick={() => loginWithRedirect({ authorizationParams: { connection: 'google-oauth2' } })}
                        className={styles.socialButton}
                        style={{
                            width: '100%',
                            background: 'white',
                            color: '#333',
                            border: '1px solid #ddd',
                            padding: '14px',
                            borderRadius: '12px',
                            fontWeight: '600',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '12px',
                            cursor: 'pointer',
                            fontSize: '16px',
                            boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                            transition: 'all 0.2s ease'
                        }}
                        onMouseOver={(e) => {
                            e.currentTarget.style.transform = 'translateY(-1px)';
                            e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
                        }}
                        onMouseOut={(e) => {
                            e.currentTarget.style.transform = 'translateY(0)';
                            e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.05)';
                        }}
                    >
                        <svg width="24" height="24" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
                            <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" fill="#4285F4" />
                            <path d="M9 18c2.43 0 4.467-.806 5.956-2.185l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853" />
                            <path d="M3.964 10.705A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.705V4.963H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.037l3.007-2.332z" fill="#FBBC05" />
                            <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.964L3.964 7.27C4.672 5.143 6.656 3.58 9 3.58z" fill="#EA4335" />
                        </svg>
                        Continue with Google
                    </button>

                    <div style={{ display: 'grid', gap: '12px', marginTop: '12px' }}>
                        <button
                            disabled
                            style={{
                                width: '100%',
                                background: '#1877F2',
                                color: 'white',
                                border: 'none',
                                padding: '14px',
                                borderRadius: '12px',
                                fontWeight: '600',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '12px',
                                cursor: 'not-allowed',
                                fontSize: '16px',
                                opacity: 0.7
                            }}
                        >
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="white">
                                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.791-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                            </svg>
                            Facebook (Coming Soon)
                        </button>

                        <button
                            disabled
                            style={{
                                width: '100%',
                                background: 'black',
                                color: 'white',
                                border: 'none',
                                padding: '14px',
                                borderRadius: '12px',
                                fontWeight: '600',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '12px',
                                cursor: 'not-allowed',
                                fontSize: '16px',
                                opacity: 0.7
                            }}
                        >
                            <svg width="24" height="24" viewBox="0 0 384 512" fill="white">
                                <path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z" />
                            </svg>
                            Apple (Coming Soon)
                        </button>
                    </div>

                    <div style={{ margin: '20px 0', textAlign: 'center', color: 'var(--color-text-tertiary)', fontSize: '14px' }}>
                        or
                    </div>

                    <button
                        onClick={handleLogin}
                        className={styles.button}
                        disabled={isLoading}
                        style={{
                            width: '100%',
                            padding: '12px 24px',
                            fontSize: '15px',
                            fontWeight: '600',
                            borderRadius: '12px',
                            border: '1px solid var(--border-color)',
                            background: 'transparent',
                            color: 'var(--color-text-primary)',
                            cursor: isLoading ? 'not-allowed' : 'pointer',
                            transition: 'all 0.2s ease',
                            opacity: isLoading ? 0.7 : 1
                        }}
                        onMouseOver={(e) => {
                            if (!isLoading) {
                                e.currentTarget.style.background = 'var(--bg-secondary)';
                            }
                        }}
                        onMouseOut={(e) => {
                            e.currentTarget.style.background = 'transparent';
                        }}
                    >
                        {isLoading ? 'Connecting...' : 'Log In with Email'}
                    </button>

                    <p style={{
                        marginTop: '32px',
                        fontSize: '13px',
                        color: 'var(--color-text-tertiary)',
                        textAlign: 'center',
                        lineHeight: '1.6'
                    }}>
                        By continuing, you agree to HELM's<br />
                        Terms of Service and Privacy Policy.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default LoginAuth0;
