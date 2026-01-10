export interface AdminUser {
    id: string;
    email: string;
    account_status: string;
    created_at: string;
}

export interface AuditLogItem {
    id: string;
    timestamp: string;
    actor_id: string | null;
    action: string;
    entity_type: string;
    entity_id: string;
    changes_json?: any;
}

export interface TierConfig {
    plan_id: string;
    name: string;
    config_json: {
        features: string[];
        limits: Record<string, number>;
    };
}

export interface UserLimits {
    user_id: string;
    plan: string;
    current_limits: Record<string, number>;
    overrides: Record<string, number>;
}

export interface BillingSummary {
    total_revenue: number;
    total_cost: number;
    profit: number;
    breakdown: Record<string, number>;
    metrics: {
        total_input_tokens: number;
        total_output_tokens: number;
        active_subscribers: number;
    };
}

export interface CustomerReconciliation {
    user_id: string;
    email: string;
    plan: string;
    revenue: number;
    cost: number;
    margin: number;
}

export interface APICostBreakdown {
    integration: string;
    total_cost: number;
    unit: string;
    usage: number;
}

const getHeaders = () => {
    const token = localStorage.getItem('token');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
};

export async function getAdminUsers(skip = 0, limit = 20): Promise<AdminUser[]> {
    const response = await fetch(`/api/admin/users?skip=${skip}&limit=${limit}`, {
        headers: getHeaders()
    });
    if (!response.ok) throw new Error('Failed to fetch users');
    return response.json();
}

export async function unlockUser(userId: string, reason: string): Promise<any> {
    const response = await fetch('/api/admin/unlock', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ user_id: userId, reason })
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to unlock user');
    }
    return response.json();
}

export async function getAuditLogs(limit = 50): Promise<AuditLogItem[]> {
    const response = await fetch(`/api/admin/audit?limit=${limit}`, {
        headers: getHeaders()
    });
    if (!response.ok) throw new Error('Failed to fetch audit logs');
    return response.json();
}

// --- Subscription & Tier Management ---

export const getTiers = async (): Promise<TierConfig[]> => {
    const response = await fetch('/api/admin/tiers', { headers: getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch tiers');
    return response.json();
};

export const updateTier = async (planId: string, payload: { name?: string, config_json: any }): Promise<TierConfig> => {
    const response = await fetch(`/api/admin/tiers/${planId}`, {
        method: 'PUT',
        headers: getHeaders(),
        body: JSON.stringify(payload)
    });
    if (!response.ok) throw new Error('Failed to update tier');
    return response.json();
};

export const getUserLimits = async (userId: string): Promise<UserLimits> => {
    const response = await fetch(`/api/admin/users/${userId}/limits`, { headers: getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch user limits');
    return response.json();
};

export const setUserLimits = async (userId: string, overrides: Record<string, number>): Promise<any> => {
    const response = await fetch(`/api/admin/users/${userId}/limits`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify(overrides)
    });
    if (!response.ok) throw new Error('Failed to set user limits');
    return response.json();
};

export const updateUserTier = async (userId: string, planId: string): Promise<any> => {
    const response = await fetch(`/api/admin/users/${userId}/tier?plan_id=${planId}`, {
        method: 'PUT',
        headers: getHeaders(),
    });
    if (!response.ok) throw new Error('Failed to update user tier');
    return response.json();
};

export async function getBillingSummary(): Promise<BillingSummary> {
    const response = await fetch('/api/admin/billing/summary', { headers: getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch billing summary');
    return response.json();
}

export async function getCustomerReconciliation(): Promise<CustomerReconciliation[]> {
    const response = await fetch('/api/admin/billing/customers', { headers: getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch customer reconciliation');
    return response.json();
}

export async function getAPICostBreakdown(): Promise<APICostBreakdown[]> {
    const response = await fetch('/api/admin/billing/apis', { headers: getHeaders() });
    if (!response.ok) throw new Error('Failed to fetch API cost breakdown');
    return response.json();
}

export async function reportBug(error_message: string, stack_trace: string, context: any = {}): Promise<any> {
    const response = await fetch('/api/bugs/report', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ error_message, stack_trace, context })
    });
    if (!response.ok) throw new Error('Failed to report bug');
    return response.json();
}
