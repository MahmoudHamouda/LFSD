
import React, { createContext, useContext, useEffect, useState } from 'react';

// Types
export type AuthStatus = 'UNKNOWN' | 'UNAUTHENTICATED' | 'AUTHENTICATED';
export type OnboardingStatus = 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETE';

interface User {
    id: string;
    email: string;
    name: string;
    onboarding_status: OnboardingStatus;
    onboarding_step?: string;
    onboarding_version?: number;
}

interface AuthContextType {
    status: AuthStatus;
    user: User | null;
    checkSession: () => Promise<void>;
    login: (token: string, user: User) => void;
    logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [status, setStatus] = useState<AuthStatus>('UNKNOWN');
    const [user, setUser] = useState<User | null>(null);

    const checkSession = async () => {
        try {
            // Check for token in localStorage first (legacy/hybrid support)
            const localToken = localStorage.getItem('token');

            const res = await fetch('/api/auth/session', {
                headers: localToken ? { 'Authorization': `Bearer ${localToken}` } : {},
                cache: 'no-store'
            });

            if (res.ok) {
                const data = await res.json();
                if (data.authenticated && data.user) {
                    setUser(data.user);
                    setStatus('AUTHENTICATED');
                } else {
                    console.warn("Session check returned specific unauth:", data);
                    handleUnauth();
                }
            } else {
                handleUnauth();
            }
        } catch (err) {
            console.error("Session check failed", err);
            handleUnauth();
        }
    };

    const handleUnauth = () => {
        localStorage.removeItem('token');
        setUser(null);
        setStatus('UNAUTHENTICATED');
    };

    const login = (token: string, userData: User) => {
        localStorage.setItem('token', token); // Still using localStorage for access token per plan implication of "hybrid"
        setUser(userData);
        setStatus('AUTHENTICATED');
    };

    const logout = async () => {
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
        } catch (e) { console.error("Logout api fail", e); }
        handleUnauth();
        window.location.href = '/login';
    };

    useEffect(() => {
        checkSession();
    }, []);

    return (
        <AuthContext.Provider value={{ status, user, checkSession, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
