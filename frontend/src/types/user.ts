/**
 * User Data Models
 * 
 * Comprehensive TypeScript types for user data including identity,
 * financial profile, health profile, engagement metrics, and derived indexes.
 */

import { VivIndex, LifeGoal } from './viv';
import { FinancialAccount, Transaction } from './finance';
import { HealthDailySummary } from './health';

// ============================================================================
// Identity & Profile
// ============================================================================

export interface UserProfile {
    bio?: string;
    location?: string;
    occupation?: string;
    [key: string]: any;
}

export interface VivPreferences {
    riskTolerance: 'low' | 'medium' | 'high';
    communicationStyle: 'concise' | 'detailed' | 'supportive';
    conflictResolutionMode: 'avoidant' | 'collaborative' | 'competitive';
}

export interface UserIdentity {
    id: string;
    username: string;
    email: string;
    // Standard fields requested by user
    firstName?: string;
    lastName?: string;
    phoneNumber?: string;
    avatar?: string;
    role?: 'user' | 'admin'; // Added role

    locale: string;
    timezone: string;

    profile: UserProfile;
    vivPreferences: VivPreferences;
}

// ============================================================================
// Health Profile & Connections
// ============================================================================

export type HealthProvider = 'whoop' | 'apple_health' | 'android_health';

export type ConnectionStatus =
    | 'not_connected'
    | 'connecting'
    | 'connected'
    | 'error'
    | 'reconnect';

export interface HealthConnection {
    provider: HealthProvider;
    status: ConnectionStatus;
    connectedAt?: string;
    lastSyncedAt?: string;
    permissions: string[];
    errorMessage?: string;
}

// ============================================================================
// Complete User Model
// ============================================================================

export interface User {
    identity: UserIdentity;

    // Core Viv Data
    vivIndex: VivIndex;
    lifeGoals: LifeGoal[];

    // Deep Data Snapshots (for dashboard)
    accounts: FinancialAccount[];
    recentTransactions: Transaction[];
    healthSummary?: HealthDailySummary;
    healthConnections: HealthConnection[];

    // Engagement Metrics
    engagement?: {
        lastActive?: string;
        streaks?: {
            dailyCheckIn: number;
            financialReview: number;
        };
        mostUsedJourneys?: string[];
    };
}

// ============================================================================
// API Response Types
// ============================================================================

export interface UserResponse {
    user: User;
    timestamp: string;
}


// ============================================================================
// Onboarding Data
// ============================================================================

export interface OnboardingData {
    user_id?: string;
    // Financial Pillars
    currency?: string;
    onboarding_session_id?: string;
    session_ids?: string[];
    is_manual_mode?: boolean;

    monthly_income?: number;
    monthly_income_type?: string;
    income_frequency?: string;
    employment_type?: string;
    other_income_sources?: string[];

    monthly_expenses?: number;
    monthly_expenses_type?: string;

    has_debt?: string;
    total_debt?: number;
    monthly_debt_payments?: number;

    housing_status?: string;
    housing_value?: number;
    rent_amount?: number;
    rent_frequency?: string;

    car_status?: string;
    car_value?: number;
    car_lease_amount?: number;
    car_lease_frequency?: string;

    other_assets_status?: string;
    other_assets_description?: string;

    discretionary_spend?: number;
    discretionary_spend_type?: string;

    monthly_savings?: number;
    monthly_savings_type?: string;

    investments_status?: string;
    investments_value?: number;
    investments_types?: string[];
    risk_appetite?: string;

    // Health Pillars
    sleep_hours?: string;
    sleep_consistency?: string;
    wake_tired?: string;

    activity_level?: string;
    activity_type?: string;

    stress_level?: string;
    energy_pattern?: string;

    diet_style?: string;
    water_intake?: string;
    smoking_pattern?: string;
    alcohol_pattern?: string;

    eating_out_frequency?: string;
    takeaway_frequency?: string;
    cooking_frequency?: string;
    nightlife_frequency?: string;

    // Productivity (Time & Productivity Pillar)
    // A) Work & Structure
    work_status?: string;
    work_hours_per_week?: string;
    uses_digital_calendar?: string;
    commute_duration?: string;

    // B) Daily Time Use
    time_meals_house_daily?: string;
    time_admin_weekly?: string;

    // C) Time Drains & Style
    main_time_drains?: string[];
    routine_style?: string;
    task_style?: string;

    // D) Pressure
    time_overwhelm_level?: string;
}

export interface UserUpdateRequest {
    identity?: Partial<UserIdentity>;
    vivPreferences?: Partial<VivPreferences>;
    onboarding_data?: OnboardingData;
}

