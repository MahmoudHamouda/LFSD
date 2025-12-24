import { HealthDailySummary, SleepSession, Workout } from '../types/health';

export async function getHealthDailySummaries(startDate?: string, endDate?: string): Promise<HealthDailySummary[]> {
    try {
        let url = '/api/health/summaries';
        const params = new URLSearchParams();
        if (startDate) params.append('start_date', startDate);
        if (endDate) params.append('end_date', endDate);

        if (params.toString()) {
            url += `?${params.toString()}`;
        }

        const response = await fetch(url);
        if (!response.ok) {
            return [];
        }
        const payload = await response.json();
        return payload.data || [];
    } catch (error) {
        console.error('Error fetching health summaries:', error);
        return [];
    }
}

export async function getRecentSleepSessions(): Promise<SleepSession[]> {
    try {
        const response = await fetch('/api/health/sleep/recent');
        if (!response.ok) {
            return [];
        }
        const payload = await response.json();
        return payload.data || [];
    } catch (error) {
        console.error('Error fetching sleep sessions:', error);
        return [];
    }
}

export async function getRecoveryScore(): Promise<any> {
    try {
        const response = await fetch('/api/health/recovery-score');
        if (!response.ok) return { score: 0 };
        return await response.json();
    } catch (error) {
        console.error('Error fetching recovery score:', error);
        return { score: 0 };
    }
}

export async function logWorkout(data: any): Promise<boolean> {
    try {
        const response = await fetch('/api/health/workouts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return response.ok;
    } catch (error) {
        console.error('Error logging workout:', error);
        return false;
    }
}

export async function logNutrition(data: any): Promise<boolean> {
    try {
        const response = await fetch('/api/health/nutrition', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return response.ok;
    } catch (error) {
        console.error('Error logging nutrition:', error);
        return false;
    }
}
