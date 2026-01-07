
import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';

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
    auth0_id?: string;
}

interface AuthContextType {
    status: AuthStatus;
    user: User | null;
    checkSession: () => Promise<void>;
    login: (token: string, user: User) => void;
    logout: () => void;
    loginWithRedirect: any; // Using any to avoid complex type import for now
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const {
        isLoading: auth0Loading,
        isAuthenticated,
        user: auth0User,
        getAccessTokenSilently,
        logout: auth0Logout,
        loginWithRedirect
    } = useAuth0();

    const [status, setStatus] = useState<AuthStatus>('UNKNOWN');
    const [user, setUser] = useState<User | null>(null);

    const checkSession = async () => {
        // This is mainly kept for compatibility, but the real logic is in the effect below
        if (isAuthenticated && auth0User) {
            await fetchBackendUser();
        }
    };

    const fetchBackendUser = async () => {
        try {
            if (!auth0User?.sub) return;

            const token = await getAccessTokenSilently();
            // Store token for other API calls if needed (though interceptors are better)
            localStorage.setItem('token', token);

            // Fetch user details from our backend
            // Note: encodeURIComponent is important for auth0|... IDs
            const res = await fetch(`/api/auth/me?auth0_id=${encodeURIComponent(auth0User.sub)}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (res.ok) {
                const data = await res.json();
                if (data.status === 'ok' && data.user) {
                    setUser(data.user);
                    setStatus('AUTHENTICATED');
                } else {
                    console.error("Failed to fetch backend user:", data);
                    // If backend doesn't know us yet (race condition with callback?), we might be in a weird state.
                    // But usually CallbackPage ensures creation first.
                }
            } else {
                console.error("Backend fetch failed", res.status);
            }
        } catch (err) {
            console.error("Error fetching backend user", err);
        }
    };

    // Effect to sync Auth0 state with our App state
    useEffect(() => {
        const initAuth = async () => {
            if (auth0Loading) {
                // Don't set unknown yet, check local storage
            }

            // 1. Check Auth0 SDK first
            if (isAuthenticated) {
                await fetchBackendUser();
                return;
            }

            // 2. Check Native Token in LocalStorage
            const nativeToken = localStorage.getItem('token');
            if (nativeToken) {
                // validate token by fetching user
                try {
                    // Decoding token to get sub would be better, but for now just fetch me
                    // We need the auth0_id to fetch the specific user record... 
                    // Actually, /api/auth/me requires ?auth0_id param.
                    // The native login response should probably return the user object too.
                    // Let's assume we stored user object or can get it.
                    // Ideally /api/auth/me should rely on the token subject, but our backend endpoint expects a param.
                    // Let's rely on the 'user' object in localStorage if available for ID

                    const storedUserStr = localStorage.getItem('user');
                    if (storedUserStr) {
                        const storedUser = JSON.parse(storedUserStr);
                        if (storedUser.auth0_id) {
                            const res = await fetch(`/api/auth/me?auth0_id=${encodeURIComponent(storedUser.auth0_id)}`, {
                                headers: { 'Authorization': `Bearer ${nativeToken}` }
                            });
                            if (res.ok) {
                                const data = await res.json();
                                if (data.status === 'ok' && data.user) {
                                    setUser(data.user);
                                    setStatus('AUTHENTICATED');
                                    return;
                                }
                            }
                        }
                    }
                } catch (e) {
                    console.error("Native session check failed", e);
                }
            }

            // 3. Fallback to unauthenticated if both failed and loading is done
            if (!auth0Loading) {
                setStatus('UNAUTHENTICATED');
                setUser(null);
                // Don't clear token immediately to allow refresh, but for now clear
                // localStorage.removeItem('auth0_token'); 
            }
        };

        initAuth();
    }, [isAuthenticated, auth0Loading]);

    const login = (token: string, userData: User) => {
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(userData));
        setUser(userData);
        setStatus('AUTHENTICATED');
    };

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        setUser(null);
        setStatus('UNAUTHENTICATED');

        // Optional: Logout from Auth0 too if they were logged in via SDK
        if (isAuthenticated) {
            auth0Logout({
                logoutParams: { returnTo: window.location.origin }
            });
        }
    };

    return (
        <AuthContext.Provider value={{ status, user, checkSession, login, logout, loginWithRedirect }}>
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
