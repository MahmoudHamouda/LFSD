
export interface LifestyleRecommendation {
    id: string;
    title: string;
    description: string;
    type: 'treat' | 'habit' | 'social';
    cost?: number;
    time_commitment?: string;
}

export interface LifeGoal {
    id: string;
    title: string;
    category: 'finance' | 'health' | 'career' | 'personal';
    target_date: string;
    progress: number;
}

export async function getLifestyleRecommendations(): Promise<LifestyleRecommendation[]> {
    try {
        const response = await fetch('/api/lifestyle/recommendations');
        if (!response.ok) return [];
        const payload = await response.json();
        return payload.data || [];
    } catch (error) {
        console.error('Error fetching lifestyle recommendations:', error);
        return [];
    }
}

export async function getLifeGoals(): Promise<LifeGoal[]> {
    try {
        const response = await fetch('/api/lifestyle/goals');
        if (!response.ok) return [];
        const payload = await response.json();
        return payload.data || [];
    } catch (error) {
        console.error('Error fetching life goals:', error);
        return [];
    }
}

export async function createLifeGoal(goal: Omit<LifeGoal, 'id' | 'progress'>): Promise<boolean> {
    try {
        const response = await fetch('/api/lifestyle/goals', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(goal)
        });
        return response.ok;
    } catch (error) {
        console.error('Error creating life goal:', error);
        return false;
    }
}
