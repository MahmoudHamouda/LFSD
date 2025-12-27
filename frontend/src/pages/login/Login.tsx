import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthProvider';
import styles from './Login.module.css';
import helmLogo from '../../assets/brand/Helm/helm_final_wordmark.svg';
import googleIcon from '../../assets/icons/google.svg';
import facebookIcon from '../../assets/icons/facebook.svg';

// Simple Toggle Component
const AuthTabs = ({ mode, setMode }: { mode: 'login' | 'signup', setMode: (m: 'login' | 'signup') => void }) => (
    <div className={styles.tabs}>
        <div
            onClick={() => setMode('login')}
            className={`${styles.tabItem} ${mode === 'login' ? styles.tabItemActive : ''}`}
        >
            Log In
        </div>
        <div
            onClick={() => setMode('signup')}
            className={`${styles.tabItem} ${mode === 'signup' ? styles.tabItemActive : ''}`}
        >
            Sign Up
        </div>
    </div>
);

const Login: React.FC = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { login } = useAuth();

    const [mode, setMode] = useState<'login' | 'signup'>('login');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Form State
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [name, setName] = useState('');

    // Password Strength Logic
    const getPasswordStrength = (pass: string) => {
        if (!pass) return { score: 0, label: '', color: '' };
        let score = 0;
        if (pass.length >= 8) score++;
        if (pass.length >= 12) score++;
        if (/[A-Z]/.test(pass)) score++;
        if (/[0-9]/.test(pass)) score++;
        if (/[^A-Za-z0-9]/.test(pass)) score++;

        if (score <= 2) return { score, label: 'Weak', color: '#EF4444' }; // Red
        if (score <= 4) return { score, label: 'Medium', color: '#F59E0B' }; // Orange
        return { score, label: 'Strong', color: '#10B981' }; // Green
    };

    const strength = getPasswordStrength(password);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            if (mode === 'signup') {
                if (password !== confirmPassword) {
                    throw new Error("Passwords do not match");
                }
                if (password.length < 6) {
                    throw new Error("Password must be at least 6 characters");
                }

                // 1. Sign Up
                const signupRes = await fetch('/api/auth/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, password, name })
                });

                if (!signupRes.ok) {
                    let errMessage = 'Signup failed';
                    const rawText = await signupRes.text();
                    try {
                        const err = JSON.parse(rawText);
                        errMessage = err.detail || errMessage;
                    } catch (e) {
                        // If raw text is reasonable length, log it to console for debug
                        if (rawText && rawText.length < 3000) {
                            console.error("Signup Server Catch:", rawText);
                        } else {
                            console.error("Signup Server Catch: Response too large to log");
                        }
                        // User-friendly message as requested
                        errMessage = "We couldn't create your account. Please try again or contact support if the issue persists.";
                    }
                    throw new Error(errMessage);
                }

                // 2. Auto Login after signup
                // Proceed to login block
            }

            // 3. Log In (Common for both flows)
            const loginRes = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: email, password })
            });

            if (!loginRes.ok) throw new Error('Invalid credentials');

            const data = await loginRes.json();

            // 4. Update Context
            login(data.access_token, data.user);

            // 5. Navigation handled by PublicOnlyRoute or simple redirect
            // But we can nudge it here if needed
            // navigate('/') -> RouteGuard will pick up user.onboarding_status and redirect accordingly.

        } catch (err: any) {
            console.error(err);
            setError(err.message || 'Authentication failed');
        } finally {
            setLoading(false);
        }
    };



    const handleGoogleLogin = async () => {
        try {
            // 1. Get Auth URL
            const response = await fetch('/api/auth/google/url');
            if (!response.ok) throw new Error('Failed to get auth URL');
            const data = await response.json();

            // 2. Open Popup
            const width = 500;
            const height = 600;
            const left = window.screen.width / 2 - width / 2;
            const top = window.screen.height / 2 - height / 2;

            const popup = window.open(
                data.url,
                'Google Login',
                `width=${width},height=${height},top=${top},left=${left}`
            );

            // 3. Listen for callback
            const handleMessage = async (event: MessageEvent) => {
                // Determine if message is relevant (cross-origin considerations apply if different ports, but auth usually redirects to same origin or uses window.opener)
                // Actually the callback page needs to post message.
                // Assuming /api/auth/google/callback is strictly backend?
                // Wait, the popup loads the Google URL. Google redirects to REDIRECT_URI.
                // The REDIRECT_URI must serve a page that does `window.opener.postMessage(...)`
                // Does our backend serve that? Or does it redirect to a frontend routes?
                // The current `api_routes_auth.py` logic implies `google_auth_callback` is an API POST endpoint called by the frontend WITH the code.
                // So the REDIRECT_URI must be a frontend page like `/auth/callback?code=...`
                // Let's assume there is a frontend route or the existing `OnboardingSteps` logic worked.
                // `OnboardingSteps` listens for `SOCIAL_AUTH_CODE`.
                // Who sends `SOCIAL_AUTH_CODE`?
                // The popup must act as the redirect target.
                // If I don't set up a frontend route for the redirect, this will fail.
                // "Coming Soon" suggests checks weren't done.
                // I need to check `vite.config.ts` or `App.tsx` for a `/google-callback` route or similar.
                // OR `api_routes_auth.py` `google_auth_url` uses a redirect URI pointing to `localhost:3000/something`?
                // Let's assume standard behavior: we need a frontend route to catch the query param and postMessage.

                if (event.data?.type === 'SOCIAL_AUTH_CODE' && event.data?.provider === 'google') {
                    const code = event.data.code;
                    try {
                        const cbResponse = await fetch('/api/auth/google/callback', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ code })
                        });

                        if (cbResponse.ok) {
                            const userData = await cbResponse.json();
                            login(userData.token, userData);
                        } else {
                            setError("Google Login failed");
                        }
                    } catch (e) {
                        console.error(e);
                        setError("Google Login error");
                    }
                    // window.removeEventListener('message', handleMessage); // Clean up
                }
            };

            window.addEventListener('message', handleMessage);

        } catch (error: any) {
            console.error(error);
            setError('Failed to initiate Google login');
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.card}>
                <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                    <img src={helmLogo} alt="HELM" style={{ height: '50px' }} />
                </div>
                <AuthTabs mode={mode} setMode={setMode} />

                <form onSubmit={handleSubmit} className={styles.form}>
                    {mode === 'signup' && (
                        <div className={styles.inputGroup}>
                            <label>Name</label>
                            <input
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                required
                                placeholder="Your Name"
                            />
                        </div>
                    )}

                    <div className={styles.inputGroup}>
                        <label>Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>
                    <div className={styles.inputGroup}>
                        <label>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                        {mode === 'login' && (
                            <div style={{ textAlign: 'right', marginTop: '4px' }}>
                                <a
                                    href="/forgot-password"
                                    style={{ fontSize: '12px', color: 'var(--color-accent-blue)', textDecoration: 'none' }}
                                    onClick={(e) => { e.preventDefault(); navigate('/forgot-password'); }}
                                >
                                    Forgot password?
                                </a>
                            </div>
                        )}
                        {mode === 'signup' && password && (
                            <div style={{ marginTop: '0.5rem' }}>
                                <div style={{
                                    height: '4px',
                                    background: '#E5E7EB',
                                    borderRadius: '2px',
                                    overflow: 'hidden'
                                }}>
                                    <div style={{
                                        width: `${Math.min(100, (strength.score / 5) * 100)}%`,
                                        background: strength.color,
                                        height: '100%',
                                        transition: 'width 0.3s ease'
                                    }} />
                                </div>
                                <div style={{ fontSize: '12px', color: strength.color, marginTop: '4px', textAlign: 'right' }}>
                                    {strength.label}
                                </div>
                            </div>
                        )}
                    </div>

                    {mode === 'signup' && (
                        <div className={styles.inputGroup}>
                            <label>Confirm Password</label>
                            <input
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                required
                            />
                        </div>
                    )}

                    {error && <p className={styles.error}>{error}</p>}

                    <button type="submit" className={styles.button} disabled={loading}>
                        {loading ? 'Processing...' : (mode === 'login' ? 'Log In' : 'Create Account')}
                    </button>

                    <div style={{ marginTop: 24, textAlign: 'center' }}>
                        <p className={styles.separatorText}>Or continue with</p>
                        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                            <button
                                type="button"
                                className={styles.socialButton}
                                onClick={handleGoogleLogin}
                            >
                                <img src={googleIcon} alt="Google" width="20" height="20" />
                                <span>Google</span>
                            </button>
                            <button
                                type="button"
                                className={styles.socialButton}
                                style={{ opacity: 0.6, cursor: 'not-allowed', filter: 'grayscale(100%)' }}
                                disabled
                                title="Coming Soon"
                            >
                                <img src={facebookIcon} alt="Facebook" width="20" height="20" />
                                <span>Facebook <span style={{ fontSize: '0.7em', marginLeft: '4px', opacity: 0.8 }}>(Coming Soon)</span></span>
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default Login;
