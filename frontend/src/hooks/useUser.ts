/**
 * User Data Hooks
 * 
 * Custom React hooks for accessing and managing user data.
 * Uses React Context for client state and React Query for server state.
 */

import { useContext } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AppStateContext } from '../state/AppProvider';
import {
    User,
    HealthConnection,
    UserUpdateRequest
} from '../types';

// ============================================================================
// API Functions
// ============================================================================

const fetchUser = async (): Promise<User> => {
    const token = localStorage.getItem('token');
    const headers: HeadersInit = {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch('/api/user/me', { headers });
    if (!response.ok) throw new Error('Failed to fetch user');
    const data = await response.json();
    return data.user;
};

const updateUser = async (updates: UserUpdateRequest): Promise<User> => {
    const response = await fetch('/api/user/me', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
    });
    if (!response.ok) throw new Error('Failed to update user');
    const data = await response.json();
    return data.user;
};

// ============================================================================
// Main User Hook
// ============================================================================

/**
 * Returns the complete user object with all profiles and indexes.
 * 
 * @example
 * const { user, isLoading, error, refetch } = useCurrentUser();
 */
export const useCurrentUser = () => {
    return useQuery<User, Error>({
        queryKey: ['user'],
        queryFn: fetchUser,
        staleTime: 5 * 60 * 1000, // 5 minutes
        gcTime: 10 * 60 * 1000, // 10 minutes (cacheTime is deprecated in v5, replaced by gcTime)
    });
};

// ============================================================================
// Financial Profile Hook
// ============================================================================

/**
 * Returns user's financial profile and affordability metrics.
 * 
 * @example
 * const { financial, affordability } = useUserFinancialSnapshot();
 */
export const useUserFinancialSnapshot = () => {
    const { data: user, isLoading, error } = useCurrentUser();

    return {
        accounts: user?.accounts || [],
        recentTransactions: user?.recentTransactions || [],
        isLoading,
        error
    };
};

// ============================================================================
// Indexes Hook
// ============================================================================

/**
 * Returns calculated user indexes with trends.
 * 
 * @example
 * const { indexes, hasHealthIndex } = useUserIndexes();
 */
export const useUserIndexes = () => {
    const { data: user, isLoading, error } = useCurrentUser();

    return {
        indexes: user?.vivIndex,
        hasHealthIndex: user?.vivIndex?.healthScore !== undefined,
        isLoading,
        error
    };
};

// ============================================================================
// Health Connections Hook
// ============================================================================

/**
 * Returns health connection status and metrics.
 * 
 * @example
 * const { connections, metrics, hasAnyConnection } = useHealthConnections();
 */
export const useHealthConnections = () => {
    const { data: user, isLoading, error } = useCurrentUser();

    const getConnectionByProvider = (provider: string): HealthConnection | undefined => {
        return user?.healthConnections.find(c => c.provider === provider);
    };

    const isConnected = (provider: string): boolean => {
        const connection = getConnectionByProvider(provider);
        return connection?.status === 'connected';
    };

    return {
        connections: user?.healthConnections || [],
        metrics: user?.healthSummary,
        hasAnyConnection: (user?.healthConnections?.length || 0) > 0,
        getConnectionByProvider,
        isConnected,
        isLoading,
        error
    };
};

// ============================================================================
// User Update Hook
// ============================================================================

/**
 * Mutation hook for updating user data.
 * 
 * @example
 * const { mutate: updateUser } = useUpdateUser();
 * updateUser({ identity: { locale: 'en-US' } });
 */
export const useUpdateUser = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: updateUser,
        onSuccess: (updatedUser) => {
            // Update the cache with new user data
            queryClient.setQueryData(['user'], updatedUser);
        },
    });
};

// ============================================================================
// Engagement Metrics Hook
// ============================================================================

/**
 * Returns user engagement metrics and streaks.
 * 
 * @example
 * const { lastActive, streaks, mostUsedJourneys } = useUserEngagement();
 */
export const useUserEngagement = () => {
    const { data: user, isLoading, error } = useCurrentUser();

    return {
        // Mock engagement data for now as it's not in User type
        lastActive: new Date().toISOString(),
        streaks: {
            current: 5,
            longest: 12,
            dailyCheckIn: 5,
            financialReview: 2
        },
        mostUsedJourneys: [],
        isLoading,
        error
    };
};
