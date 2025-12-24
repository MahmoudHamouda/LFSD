import { HistoryItem, HistoryResponse, HistoryFilters } from '../types/history';

export async function getUnifiedHistory(
    filters: HistoryFilters,
    limit: number = 50,
    cursor?: string
): Promise<HistoryResponse | null> {
    try {
        const response = await fetch('/api/history/unified', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filters,
                limit,
                cursor
            }),
        });

        if (!response.ok) {
            console.error('Failed to fetch history');
            return null;
        }

        return await response.json();
    } catch (error) {
        console.error('Error fetching history:', error);
        return null;
    }
}
