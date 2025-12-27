import { FinancialAccount, Transaction } from '../types/finance';

export async function getFinancialAccounts(): Promise<FinancialAccount[]> {
    try {
        const response = await fetch('/api/financial/accounts');
        if (!response.ok) {
            return [];
        }
        const payload = await response.json();
        return payload.data || [];
    } catch (error) {
        console.error('Error fetching accounts:', error);
        return [];
    }
}

export async function getTransactions(limit: number = 20): Promise<Transaction[]> {
    try {
        const response = await fetch(`/api/financial/transactions?limit=${limit}`);
        if (!response.ok) {
            return [];
        }
        const payload = await response.json();
        return payload.data || [];
    } catch (error) {
        console.error('Error fetching transactions:', error);
        return [];
    }
}

export async function getNetWorth(): Promise<number> {
    try {
        const response = await fetch('/api/finance/net-worth');
        if (!response.ok) return 0;
        const payload = await response.json();
        return payload.net_worth || 0;
    } catch (error) {
        console.error('Error fetching net worth:', error);
        return 0;
    }
}

export async function getPortfolioPerformance(): Promise<any> {
    try {
        const response = await fetch('/api/finance/portfolio/performance');
        if (!response.ok) return { total_value: 0, daily_change_percent: 0 };
        return await response.json();
    } catch (error) {
        console.error('Error fetching portfolio performance:', error);
        return { total_value: 0, daily_change_percent: 0 };
    }
}

export async function getFinancialScore(period: 'week' | 'month' = 'week'): Promise<any> {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/scores/current?period=${period}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) return null;
        return await response.json();
    } catch (error) {
        console.error('Error fetching financial score:', error);
        return null;
    }
}

export async function uploadStatement(file: File): Promise<any> {
    try {
        const token = localStorage.getItem('token');

        // Convert file to base64
        const toBase64 = (file: File) => new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => resolve(reader.result as string);
            reader.onerror = error => reject(error);
        });

        const base64Content = await toBase64(file);

        const payload = {
            files: [{
                filename: file.name,
                content: base64Content
            }]
        };

        const response = await fetch('/api/finance/upload-statement', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        return await response.json();
    } catch (error) {
        console.error('Error uploading statement:', error);
        throw error;
    }
}


export async function getFinancialSummary(): Promise<any> {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/finance/summary', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) return null;
        return await response.json();
    } catch (error) {
        console.error('Error fetching financial summary:', error);
        return null;
    }
}


export async function getFinancialHistory(categoryId: string, range: string = '30d'): Promise<any> {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/finance/categories/${categoryId}/history?range=${range}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) return null;
        return await response.json();
    } catch (error) {
        console.error('Error fetching financial history:', error);
        return null;
    }
}

export async function getCategoryCoverage(categoryId: string, windowDays: number = 30): Promise<any> {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/finance/categories/${categoryId}/coverage?window_days=${windowDays}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) return null;
        return await response.json();
    } catch (error) {
        console.error('Error fetching category coverage:', error);
        return null;
    }
}

// --- GOALS API ---

export async function getFinancialGoals(pillar?: string): Promise<any[]> {
    try {
        const token = localStorage.getItem('token');
        const url = pillar ? `/api/finance/goals?pillar=${pillar}` : '/api/finance/goals';
        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) return [];
        return await response.json();
    } catch (error) {
        console.error('Error fetching goals:', error);
        return [];
    }
}

export async function createGoal(goal: any): Promise<any> {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/finance/goals', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(goal)
        });
        if (!response.ok) throw new Error('Failed to create goal');
        return await response.json();
    } catch (error) {
        console.error('Error creating goal:', error);
        throw error;
    }
}

export async function updateGoal(goalId: string, updates: any): Promise<any> {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`/api/finance/goals/${goalId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(updates)
        });
        if (!response.ok) throw new Error('Failed to update goal');
        return await response.json();
    } catch (error) {
        console.error('Error updating goal:', error);
        throw error;
    }
}

export async function deleteGoal(goalId: string): Promise<void> {
    try {
        const token = localStorage.getItem('token');
        await fetch(`/api/finance/goals/${goalId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
    } catch (error) {
        console.error('Error deleting goal:', error);
        throw error;
    }
}

export async function getGoalInsights(): Promise<any> {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/finance/goals/insights', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) return { goals: [] };
        return await response.json();
    } catch (error) {
        console.error('Error fetching goal insights:', error);
        return { goals: [] };
    }
}
