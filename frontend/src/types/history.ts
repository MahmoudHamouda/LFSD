/**
 * History Data Models
 * 
 * Normalized types for unified history timeline aggregating all user activities:
 * transactions, notifications, activities, chat, recommendations, and health metrics.
 */

// ============================================================================
// History Item Types
// ============================================================================

export type HistoryItemType =
    | "transaction"
    | "notification"
    | "activity"
    | "chat"
    | "recommendation"
    | "health"
    | "viv_log";

export type HistoryCategory = 'financial' | 'time' | 'health' | 'all';

export type ImportanceLevel = 'high' | 'medium' | 'low';

// ============================================================================
// Base History Item
// ============================================================================

export interface HistoryItem {
    id: string;
    type: HistoryItemType;
    title: string;
    subtitle?: string;
    amount?: number;         // For transactions
    metricValue?: number;    // For health metrics / indexes
    timestamp: string;
    tags?: string[];
    sourceService: string;   // "financials" | "notifications" | "activity" | "chat" | "recommendations" | "health"
    icon?: string;
    importance?: ImportanceLevel;
    metadata?: Record<string, any>;
    raw: unknown;            // Original data structure for detail view
}

// ============================================================================
// Specific History Item Types
// ============================================================================

export interface TransactionHistoryItem extends HistoryItem {
    type: "transaction";
    amount: number;
    category: string;
    description?: string;
}

export interface NotificationHistoryItem extends HistoryItem {
    type: "notification";
    message: string;
    readStatus: boolean;
}

export interface ActivityHistoryItem extends HistoryItem {
    type: "activity";
    action: string;
    details?: string;
}

export interface ChatHistoryItem extends HistoryItem {
    type: "chat";
    conversationId: string;
    lastMessage: string;
}

export interface RecommendationHistoryItem extends HistoryItem {
    type: "recommendation";
    description: string;
    actionUrl?: string;
    actionLabel?: string;
}

export interface HealthHistoryItem extends HistoryItem {
    type: "health";
    metricType: string;  // "sleep", "recovery", "activity", etc.
    metricValue: number;
    insight?: string;
    provider: string;    // "whoop", "apple_health", "android_health"
}

// ============================================================================
// History Filters
// ============================================================================

export interface DateRange {
    start: string;
    end: string;
}

export interface HistoryFilters {
    types: HistoryItemType[];
    dateRange?: DateRange;
    importance?: ImportanceLevel | 'all';
    category?: HistoryCategory;
    searchQuery?: string;
}

// ============================================================================
// History Response
// ============================================================================

export interface HistoryDayGroup {
    date: string;           // ISO date string (YYYY-MM-DD)
    label: string;          // "Today", "Yesterday", "This Week", etc.
    items: HistoryItem[];
}

export interface HistoryResponse {
    groups: HistoryDayGroup[];
    totalCount: number;
    hasMore: boolean;
    nextCursor?: string;
}

// ============================================================================
// History API Request
// ============================================================================

export interface HistoryRequest {
    filters: HistoryFilters;
    limit?: number;
    cursor?: string;
}
