import React, { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';

export default function AuthCallback() {
    const [searchParams] = useSearchParams();
    const code = searchParams.get('code');
    const error = searchParams.get('error');

    useEffect(() => {
        if (code) {
            console.log("Got auth code:", code);
            // Send code to parent window
            if (window.opener) {
                window.opener.postMessage({ type: 'HEALTH_AUTH_CODE', provider: 'google', code }, '*');
                setTimeout(() => window.close(), 100); // Small delay to ensure message sends
            }
        } else if (error) {
            console.error("Auth error:", error);
            if (window.opener) window.close();
        }
    }, [code, error]);

    return (
        <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100vh',
            fontFamily: 'sans-serif',
            color: '#64748b'
        }}>
            <div style={{ textAlign: 'center' }}>
                <h3>Authenticating...</h3>
                <p>Please wait while we connect your account.</p>
            </div>
        </div>
    );
}
