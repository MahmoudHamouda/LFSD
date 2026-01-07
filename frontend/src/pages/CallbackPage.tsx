/**
 * Auth0 Callback Page
 * Handles redirect after Auth0 authentication
 */
import React, { useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { useNavigate } from 'react-router-dom';

export const CallbackPage: React.FC = () => {
    const { getAccessTokenSilently, isAuthenticated, isLoading, user: auth0User } = useAuth0();
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        const handleCallback = async () => {
            try {
                if (isLoading) return;

                if (!isAuthenticated) {
                    console.error('Not authenticated after callback');
                    navigate('/login');
                    return;
                }

                // Get the Auth0 access token
                const token = await getAccessTokenSilently();
                const user = auth0User;

                if (!user) {
                    throw new Error('User details not available');
                }

                // Send to backend
                const response = await fetch('/api/auth/callback', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        token: token,
                        email: user.email,
                        auth0_id: user.sub,
                        name: user.name,
                        picture: user.picture
                    }),
                });

                if (!response.ok) {
                    throw new Error('Failed to complete authentication');
                }

                const userData = await response.json();

                // Store user data in localStorage
                localStorage.setItem('user', JSON.stringify(userData));
                localStorage.setItem('auth0_token', token);

                // Redirect to home page
                navigate('/');
            } catch (err) {
                console.error('Callback error:', err);
                setError(err instanceof Error ? err.message : 'Authentication failed');
            }
        };

        handleCallback();
    }, [isAuthenticated, isLoading, getAccessTokenSilently, navigate]);

    if (error) {
        return (
            <div style={{ padding: '2rem', textAlign: 'center' }}>
                <h2>Authentication Error</h2>
                <p>{error}</p>
                <button onClick={() => navigate('/login')}>Return to Login</button>
            </div>
        );
    }

    return (
        <div style={{ padding: '2rem', textAlign: 'center' }}>
            <h2>Completing authentication...</h2>
            <p>Please wait while we log you in.</p>
        </div>
    );
};
