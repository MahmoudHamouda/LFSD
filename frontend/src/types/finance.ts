/**
 * Financial Data Models
 * 
 * Types for deep finance tracking including accounts and detailed transactions.
 */

// ============================================================================
// Accounts
// ============================================================================

export type AccountType = 'checking' | 'savings' | 'credit' | 'investment' | 'loan';

export interface FinancialAccount {
    id: string;
    userId: string;
    institutionName: string;
    accountType: AccountType;
    currentBalance: number;
    limit?: number;
}

// ============================================================================
// Transactions
// ============================================================================

export interface Transaction {
    id: string;
    accountId: string;
    userId: string;
    amount: number;
    currencyCode: string;
    transactionDate: string;
    merchantName: string;
    merchantCategoryCode?: string;
    categoryPrimary: string;
    categoryDetailed?: string;
    isRecurring: boolean;
    locationLat?: number;
    locationLon?: number;
}
