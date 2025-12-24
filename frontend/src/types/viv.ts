/**
 * Viv Logic Engine Data Models
 * 
 * Types for the core intelligence layer including indexes, logs, and life goals.
 */

// ============================================================================
// Viv Indexes (The Vitals)
// ============================================================================

export interface VivIndex {
    id: string;
    userId: string;
    timestamp: string;
    financialScore: number;
    healthScore: number;
    timeScore: number;
    snapshotReason?: string;
}

// ============================================================================
// Life Goals (The Targets)
// ============================================================================

export type GoalPriority = 'high' | 'medium' | 'low';

export interface ImpactVector {
    finance?: number; // -100 to +100
    health?: number;
    time?: number;
}

export interface LifeGoal {
    id: string;
    userId: string;
    title: string;
    targetAmount: number;
    savedAmount: number;
    deadline?: string;
    impactVector: ImpactVector;
    priority: GoalPriority;
}

// ============================================================================
// Viv Logs (The Audit Trail)
// ============================================================================

export interface VivLog {
    id: string;
    userId: string;
    timestamp: string;
    userIntent: string;
    contextSnapshot: {
        financial: number;
        health: number;
        time: number;
    };
    decisionLogic: string;
    aiResponse: string;
}
