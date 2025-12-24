/**
 * Health Integration Data Models
 * 
 * Types for health provider connections, metrics, and integration settings.
 */

import { HealthProvider, ConnectionStatus, HealthConnection } from './user';

// ============================================================================
// Deep Health Models
// ============================================================================

export interface HealthDailySummary {
    userId: string;
    date: string; // YYYY-MM-DD
    sleepDurationMinutes: number;
    sleepQualityScore: number; // 0-100
    hrvAverage: number;
    restingHeartRate: number;
    stepsCount: number;
}

export interface SleepSession {
    id: string;
    userId: string;
    startTime: string;
    endTime: string;
    deepSleepMinutes: number;
    remSleepMinutes: number;
    wakeCount: number;
}

export interface Workout {
    id: string;
    userId: string;
    startTime: string;
    endTime: string;
    activityType: string;
    caloriesBurned: number;
    averageHeartRate: number;
    perceivedExertion: number; // 0-10
}

// ============================================================================
// Health Connection Management
// ============================================================================

export interface ConnectHealthProviderRequest {
    provider: HealthProvider;
    authCode?: string;        // OAuth authorization code
    permissions: string[];    // Requested permissions
}

export interface ConnectHealthProviderResponse {
    connection: HealthConnection;
    redirectUrl?: string;     // For OAuth flow
}

export interface DisconnectHealthProviderRequest {
    provider: HealthProvider;
}

// ============================================================================
// Health Dashboard Data
// ============================================================================

export interface HealthDashboardData {
    connections: HealthConnection[];
    todaySummary: HealthDailySummary;
    recentSleep: SleepSession[];
    recentWorkouts: Workout[];
}
