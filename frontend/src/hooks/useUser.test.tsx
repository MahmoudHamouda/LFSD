/**
 * Unit tests for user data hooks
 * 
 * Tests the custom React hooks with mocked React Query
 */

import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import {
    useCurrentUser,
    useUserFinancialSnapshot,
    useUserIndexes,
    useHealthConnections,
    useUpdateUser,
    useUserEngagement
} from './useUser';
import { User } from '../types';

// ============================================================================
// Test Setup
// ============================================================================

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
            mutations: { retry: false },
        },
    });

    return ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient} >
            {children}
        </QueryClientProvider>
    );
};

const mockUser: User = {
    identity: {
        id: 'user-123',
        username: 'testuser',
        email: 'test@example.com',
        avatar: 'https://example.com/avatar.jpg',
        locale: 'en-US',
        timezone: 'America/New_York',
        profile: {},
        vivPreferences: {
            riskTolerance: 'medium',
            communicationStyle: 'concise',
            conflictResolutionMode: 'collaborative'
        }
    },
    vivIndex: {
        id: '1',
        userId: 'user-123',
        timestamp: '2024-01-15T12:00:00Z',
        financialScore: 78,
        healthScore: 85,
        timeScore: 65
    },
    lifeGoals: [],
    accounts: [],
    recentTransactions: [],
    healthConnections: [
        {
            provider: 'whoop',
            status: 'connected',
            connectedAt: '2024-01-01T00:00:00Z',
            lastSyncedAt: '2024-01-15T12:00:00Z',
            permissions: ['sleep', 'recovery', 'activity'],
        },
    ],
    healthSummary: {
        userId: 'user-123',
        date: '2024-01-15',
        stepsCount: 8500,
        sleepDurationMinutes: 450,
        sleepQualityScore: 85,
        hrvAverage: 65,
        restingHeartRate: 60
    }
};

// Mock fetch
global.fetch = jest.fn();

// ============================================================================
// useCurrentUser Tests
// ============================================================================

describe('useCurrentUser', () => {
    beforeEach(() => {
        (global.fetch as jest.Mock).mockClear();
    });

    it('should fetch and return user data', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ user: mockUser }),
        });

        const { result } = renderHook(() => useCurrentUser(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(result.current.data).toEqual(mockUser);
        expect(result.current.error).toBeNull();
    });

    it('should handle fetch errors', async () => {
        (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

        const { result } = renderHook(() => useCurrentUser(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(result.current.data).toBeUndefined();
        expect(result.current.error).toBeTruthy();
    });
});

// ============================================================================
// useUserFinancialSnapshot Tests
// ============================================================================

describe('useUserFinancialSnapshot', () => {
    it('should return financial profile', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ user: mockUser }),
        });

        const { result } = renderHook(() => useUserFinancialSnapshot(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(result.current.accounts).toEqual(mockUser.accounts);
        expect(result.current.recentTransactions).toEqual(mockUser.recentTransactions);
    });
});

// ============================================================================
// useUserIndexes Tests
// ============================================================================

describe('useUserIndexes', () => {
    it('should return calculated indexes', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ user: mockUser }),
        });

        const { result } = renderHook(() => useUserIndexes(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(result.current.indexes).toEqual(mockUser.vivIndex);
        expect(result.current.hasHealthIndex).toBe(true);
    });

    it('should indicate no health index when not connected', async () => {
        const userWithoutHealth = {
            ...mockUser,
            vivIndex: {
                ...mockUser.vivIndex,
                healthScore: undefined,
            },
        };

        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ user: userWithoutHealth }),
        });

        const { result } = renderHook(() => useUserIndexes(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(result.current.hasHealthIndex).toBe(false);
    });
});

// ============================================================================
// useHealthConnections Tests
// ============================================================================

describe('useHealthConnections', () => {
    it('should return health connections and metrics', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ user: mockUser }),
        });

        const { result } = renderHook(() => useHealthConnections(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(result.current.connections).toEqual(mockUser.healthConnections);
        expect(result.current.metrics).toEqual(mockUser.healthSummary);
        expect(result.current.hasAnyConnection).toBe(true);
    });

    it('should check if specific provider is connected', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ user: mockUser }),
        });

        const { result } = renderHook(() => useHealthConnections(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        expect(result.current.isConnected('whoop')).toBe(true);
        expect(result.current.isConnected('apple_health')).toBe(false);
    });

    it('should get connection by provider', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ user: mockUser }),
        });

        const { result } = renderHook(() => useHealthConnections(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        const whoopConnection = result.current.getConnectionByProvider('whoop');
        expect(whoopConnection?.provider).toBe('whoop');
        expect(whoopConnection?.status).toBe('connected');
    });
});

// ============================================================================
// useUpdateUser Tests
// ============================================================================

describe('useUpdateUser', () => {
    it('should update user data', async () => {
        const updatedUser = {
            ...mockUser,
            identity: { ...mockUser.identity, locale: 'fr-FR' },
        };

        (global.fetch as jest.Mock)
            .mockResolvedValueOnce({
                ok: true,
                json: async () => ({ user: mockUser }),
            })
            .mockResolvedValueOnce({
                ok: true,
                json: async () => ({ user: updatedUser }),
            });

        const { result } = renderHook(() => ({
            user: useCurrentUser(),
            update: useUpdateUser(),
        }), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.user.isLoading).toBe(false));

        // Trigger update
        result.current.update.mutate({
            identity: { locale: 'fr-FR' },
        });

        await waitFor(() => expect(result.current.update.isSuccess).toBe(true));

        expect(result.current.user.data?.identity.locale).toBe('fr-FR');
    });
});

// ============================================================================
// useUserEngagement Tests
// ============================================================================

describe('useUserEngagement', () => {
    it('should return engagement metrics', async () => {
        (global.fetch as jest.Mock).mockResolvedValueOnce({
            ok: true,
            json: async () => ({ user: mockUser }),
        });

        const { result } = renderHook(() => useUserEngagement(), {
            wrapper: createWrapper(),
        });

        await waitFor(() => expect(result.current.isLoading).toBe(false));

        // Engagement is mocked in the hook, so we check against the mock values in the hook
        expect(result.current.streaks).toEqual({ current: 0, longest: 0 });
        expect(result.current.mostUsedJourneys).toEqual([]);
        expect(result.current.lastActive).toBeDefined();
    });
});
