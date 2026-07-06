import { User, UserUpdateRequest } from '../types/user';

/** Real integration statuses for the current user (connector id -> connected). */
export async function getUserConnections(): Promise<Record<string, boolean>> {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/user/connections', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) return {};
        const payload = await response.json();
        return payload.connections || {};
    } catch {
        return {};
    }
}

export async function getUserProfile(): Promise<User | null> {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/user/me', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) {
            console.error('Failed to fetch user profile');
            return null;
        }
        const payload = await response.json();
        // Handle potentially wrapped response (e.g. { data: { user: ... } })
        if (payload.data && payload.data.user) {
            return payload.data.user;
        }
        return payload.user || payload.data;
    } catch (error) {
        console.error('Error fetching user profile:', error);
        return null;
    }
}

export async function updateUserProfile(updates: UserUpdateRequest): Promise<User | null> {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/user/me', {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(updates),
        });

        if (!response.ok) {
            console.error('Failed to update user profile');
            return null;
        }
        const payload = await response.json();
        // Handle potentially wrapped response
        if (payload.data && payload.data.user) {
            return payload.data.user;
        }
        return payload.user || payload.data;
    } catch (error) {
        console.error('Error updating user profile:', error);
        return null;
    }
}
