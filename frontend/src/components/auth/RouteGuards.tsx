
import React, { useEffect } from 'react';
import { useAuth } from '../../context/AuthProvider';
import { useNavigate, useLocation } from 'react-router-dom';

export const PublicOnlyRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { status, user } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        if (status === 'AUTHENTICATED' && user) {
            // Determine redirect target
            const returnTo = new URLSearchParams(location.search).get('returnTo');

            if (user.onboarding_status !== 'COMPLETE') {
                // Force onboarding if incomplete
                const step = user.onboarding_step || 'start';
                // Very basic step mappping or just go to /onboarding
                navigate('/onboarding');
            } else {
                // Standard redirect
                navigate(returnTo || '/'); // Using '/' because Layout redirects to /dashboard or home
            }
        }
    }, [status, user, navigate, location]);

    if (status === 'UNKNOWN') return <div style={{ padding: 50, textAlign: 'center' }}>Loading...</div>;

    return <>{children}</>;
};

export const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { status, user } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        if (status === 'UNAUTHENTICATED') {
            navigate(`/login?returnTo=${encodeURIComponent(location.pathname)}`);
        } else if (status === 'AUTHENTICATED' && user) {
            // Check onboarding
            if (user.onboarding_status !== 'COMPLETE') {
                navigate('/onboarding');
            }
        }
    }, [status, user, navigate, location]);

    if (status === 'UNKNOWN') return <div style={{ padding: 50, textAlign: 'center' }}>Loading...</div>;
    if (status === 'UNAUTHENTICATED') return null; // Will redirect

    return <>{children}</>;
};

export const OnboardingRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { status, user } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (status === 'UNAUTHENTICATED') {
            navigate('/login');
        } else if (status === 'AUTHENTICATED' && user) {
            if (user.onboarding_status === 'COMPLETE') {
                navigate('/'); // Already done, go home
            }
        }
    }, [status, user, navigate]);

    if (status === 'UNKNOWN') return <div style={{ padding: 50, textAlign: 'center' }}>Loading...</div>;

    return <>{children}</>;
};

export const AdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { status, user } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (status === 'UNAUTHENTICATED') {
            navigate('/login');
        } else if (status === 'AUTHENTICATED' && user) {
            // Check role
            if (user.identity?.role !== 'admin') {
                navigate('/'); // Unauthorized, go home
            }
        }
    }, [status, user, navigate]);

    if (status === 'UNKNOWN') return <div style={{ padding: 50, textAlign: 'center' }}>Loading...</div>;
    // Hide content if not admin (even if not redirected yet)
    if (status === 'AUTHENTICATED' && user && user.identity?.role !== 'admin') {
        return null;
    }

    return <>{children}</>;
};
