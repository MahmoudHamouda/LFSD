import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthProvider'; // Fixed path
import logoUrl from '../../assets/helm-logo.svg';
import styles from './Login.module.css';

const LoginNative: React.FC = () => {
    console.log('LOGIN NATIVE: Component Rendered');
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);

        try {
            const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
            const body = isLogin ? { email, password } : { email, password, name };

            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            const text = await res.text();
            console.log('LOGIN NATIVE: Raw Response Body:', text);
            console.log('LOGIN NATIVE: Response Status:', res.status);

            let data;
            try {
                data = JSON.parse(text);
            } catch (e) {
                console.error('LOGIN NATIVE: JSON Parse Error:', e);
                throw new Error("Server returned non-JSON response: " + text.substring(0, 50));
            }

            if (!res.ok) {
                // Handle specific Auth0 errors
                if (data.error === 'access_denied') {
                    throw new Error("Invalid credentials");
                }
                throw new Error(data.error_description || data.message || "Authentication failed");
            }

            // Determine token and user data
            // Login returns: { access_token, id_token, scope, expires_in, token_type }
            // Register returns: { _id, email, email_verified } -> Then we usually need to auto-login

            if (isLogin) {
                const token = data.access_token;
                console.log('LOGIN NATIVE: Token received', token ? 'YES' : 'NO');

                // Decode token or fetch user info to get auth0_id
                // For MVP, we can fetch /api/auth/me?auth0_id=... but we need the ID first.
                // The native login endpoint implementation we did attempts to sync user and logs it.
                // Let's ask backend for the user. 
                // Wait, our backend login endpoint ONLY returns the token data.
                // We need to fetch user profile using the token.
                // Fetch user info from Auth0 directly using the token to get the ID
                // Or try to fetch from our backend using the token
                // Let's cheat slightly and update /me to accept JUST the token (no auth0_id param) if it parses the subject?
                // No, current /me requires param.

                // Better approach: Let's assume the backend login endpoint implementation ALSO returns the user.
                // I should update the backend to return user info. 
                // But since backend deployment is running, I'll do it client side for now:
                // We can decode the JWT locally to get 'sub'.

                // Minimal JWT decode
                let auth0_id = '';
                try {
                    const base64Url = token.split('.')[1];
                    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
                    const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function (c) {
                        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
                    }).join(''));

                    const decoded = JSON.parse(jsonPayload);
                    auth0_id = decoded.sub;
                    console.log('LOGIN NATIVE: Decoded ID', auth0_id);
                } catch (e) {
                    console.error('LOGIN NATIVE: JWT Decode Error', e);
                    throw new Error("Failed to decode token");
                }

                // Now fetch full user from our backend
                console.log('LOGIN NATIVE: Fetching profile for', auth0_id);
                const meRes = await fetch(`/api/auth/me?auth0_id=${encodeURIComponent(auth0_id)}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });

                console.log('LOGIN NATIVE: Profile fetch status', meRes.status);
                const meText = await meRes.text();
                console.log('LOGIN NATIVE: Profile fetch body', meText);

                if (meRes.ok) {
                    try {
                        const meData = JSON.parse(meText);
                        if (meData.user) {
                            console.log('LOGIN NATIVE: Login SUCCESS, Redirecting');
                            login(token, meData.user);
                            navigate('/');
                            return;
                        }
                    } catch (e) {
                        console.error('LOGIN NATIVE: Profile JSON Parse Error', e);
                        throw new Error("Invalid profile response from server");
                    }
                } else if (meRes.status === 404) {
                    console.log('LOGIN NATIVE: User not found in DB, attempting JIT provisioning via /callback');
                    const cbRes = await fetch('/api/auth/callback', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ token: token })
                    });

                    if (cbRes.ok) {
                        const userUser = await cbRes.json();
                        // Callback returns UserResponse (flat), but we need to check usage
                        console.log('LOGIN NATIVE: JIT Provisioning Success', userUser);
                        // The user object is returned directly. 
                        // We need to match what 'login' expects. login expects 'User' interface.
                        // UserResponse has: id, email, name, onboarding_status, auth0_id.
                        // Our local User interface matches this mostly.
                        login(token, userUser);
                        navigate('/');
                        return;
                    } else {
                        const cbText = await cbRes.text();
                        console.error('LOGIN NATIVE: JIT Provisioning Failed', cbText);
                        throw new Error("Failed to create user record: " + cbText);
                    }
                }

                throw new Error("Failed to load user profile: " + meText);

            } else {
                // Registration successful - Auto Login
                console.log('LOGIN NATIVE: Signup Success, Attempting Auto-Login');

                try {
                    const loginRes = await fetch('/api/auth/login', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email, password })
                    });

                    if (loginRes.ok) {
                        const loginData = await loginRes.json();
                        const token = loginData.access_token;

                        // Minimal JWT decode to get ID
                        let auth0_id = '';
                        try {
                            const base64Url = token.split('.')[1];
                            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
                            const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function (c) {
                                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
                            }).join(''));

                            const decoded = JSON.parse(jsonPayload);
                            auth0_id = decoded.sub;
                        } catch (e) {
                            console.error('LOGIN NATIVE: Auto-Login JWT Decode Error', e);
                            throw new Error("Account created, but auto-login failed. Please log in.");
                        }

                        // Fetch full profile
                        const meRes = await fetch(`/api/auth/me?auth0_id=${encodeURIComponent(auth0_id)}`, {
                            headers: { 'Authorization': `Bearer ${token}` }
                        });

                        if (meRes.ok) {
                            const meText = await meRes.text();
                            const meData = JSON.parse(meText);
                            if (meData.user) {
                                console.log('LOGIN NATIVE: Auto-Login SUCCESS');
                                login(token, meData.user);
                                navigate('/');
                                return;
                            }
                        }
                    }
                } catch (autoLoginErr) {
                    console.error('LOGIN NATIVE: Auto-Login Failed', autoLoginErr);
                    // Fallback to manual login
                }

                setIsLogin(true);
                setError("Account created! Please log in.");
                setPassword('');
            }
        } catch (err: any) {
            console.error('LOGIN NATIVE: Overall Error', err);
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.card}>


                <div style={{ textAlign: 'center', marginBottom: '24px' }}>
                    <img src={logoUrl} alt="HELM" className={styles.logo} />
                    <p style={{ color: 'var(--color-text-secondary)', marginTop: '8px' }}>
                        {isLogin ? 'Sign in to your account' : 'Create your account'}
                    </p>
                </div>

                <form onSubmit={handleSubmit}>
                    {error && (
                        <div style={{
                            backgroundColor: 'rgba(239, 68, 68, 0.1)',
                            color: '#ef4444',
                            padding: '12px',
                            borderRadius: '4px',
                            marginBottom: '16px',
                            fontSize: '14px'
                        }}>
                            {error}
                        </div>
                    )}

                    {!isLogin && (
                        <div style={{ marginBottom: '16px' }}>
                            <label style={{ display: 'block', fontSize: '14px', marginBottom: '8px', color: 'var(--color-text-primary)' }}>Name</label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                required={!isLogin}
                                style={{
                                    width: '100%',
                                    padding: '10px',
                                    borderRadius: '4px',
                                    border: '1px solid var(--border-light)',
                                    backgroundColor: 'var(--bg-input)',
                                    color: 'var(--color-text-primary)',
                                    fontSize: '16px'
                                }}
                            />
                        </div>
                    )}

                    <div style={{ marginBottom: '16px' }}>
                        <label style={{ display: 'block', fontSize: '14px', marginBottom: '8px', color: 'var(--color-text-primary)' }}>Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            style={{
                                width: '100%',
                                padding: '10px',
                                borderRadius: '4px',
                                border: '1px solid var(--border-light)',
                                backgroundColor: 'var(--bg-input)',
                                color: 'var(--color-text-primary)',
                                fontSize: '16px'
                            }}
                        />
                    </div>

                    <div style={{ marginBottom: '24px' }}>
                        <label style={{ display: 'block', fontSize: '14px', marginBottom: '8px', color: 'var(--color-text-primary)' }}>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            style={{
                                width: '100%',
                                padding: '10px',
                                borderRadius: '4px',
                                border: '1px solid var(--border-light)',
                                backgroundColor: 'var(--bg-input)',
                                color: 'var(--color-text-primary)',
                                fontSize: '16px'
                            }}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={isLoading}
                        style={{
                            width: '100%',
                            padding: '12px',
                            backgroundColor: 'var(--color-primary)',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            fontSize: '16px',
                            fontWeight: '600',
                            cursor: isLoading ? 'not-allowed' : 'pointer',
                            opacity: isLoading ? 0.7 : 1
                        }}
                    >
                        {isLoading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
                    </button>
                </form>

                <div style={{ marginTop: '20px', borderTop: '1px solid #eee', paddingTop: '20px' }}>
                    <p style={{ textAlign: 'center', color: '#666', fontSize: '14px', marginBottom: '16px' }}>Or continue with</p>
                    <div style={{ display: 'grid', gap: '12px' }}>
                        <button
                            type="button"
                            onClick={() => loginWithRedirect({ authorizationParams: { connection: 'google-oauth2' } })}
                            style={{
                                width: '100%',
                                padding: '10px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                                backgroundColor: '#fff',
                                border: '1px solid #ddd',
                                borderRadius: '4px',
                                color: '#333',
                                cursor: 'pointer',
                                fontWeight: '500',
                                transition: 'background 0.2s'
                            }}
                            onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f5f5f5'}
                            onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#fff'}
                        >
                            <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
                                <path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" fill="#4285F4" />
                                <path d="M9 18c2.43 0 4.467-.806 5.956-2.185l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853" />
                                <path d="M3.964 10.705A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.705V4.963H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.037l3.007-2.332z" fill="#FBBC05" />
                                <path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.964L3.964 7.27C4.672 5.143 6.656 3.58 9 3.58z" fill="#EA4335" />
                            </svg>
                            <span>Google</span>
                        </button>
                        <button
                            type="button"
                            disabled
                            style={{
                                width: '100%',
                                padding: '10px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                                backgroundColor: '#1877F2',
                                border: 'none',
                                borderRadius: '4px',
                                color: '#fff',
                                cursor: 'not-allowed',
                                fontWeight: '500',
                                opacity: 0.6
                            }}
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
                                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.791-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                            </svg>
                            <span>Facebook (Coming Soon)</span>
                        </button>
                        <button
                            type="button"
                            disabled
                            style={{
                                width: '100%',
                                padding: '10px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                                backgroundColor: '#000',
                                border: 'none',
                                borderRadius: '4px',
                                color: '#fff',
                                cursor: 'not-allowed',
                                fontWeight: '500',
                                opacity: 0.6
                            }}
                        >
                            <svg width="18" height="18" viewBox="0 0 384 512" fill="white">
                                <path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z" />
                            </svg>
                            <span>Apple (Coming Soon)</span>
                        </button>
                    </div>
                </div>

                <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '14px' }}>
                    <p>
                        {isLogin ? "Don't have an account? " : "Already have an account? "}
                        <span
                            onClick={() => { setIsLogin(!isLogin); setError(null); }}
                            style={{ color: 'var(--color-accent-blue)', cursor: 'pointer', fontWeight: '600' }}
                        >
                            {isLogin ? 'Sign Up' : 'Log In'}
                        </span>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default LoginNative;
