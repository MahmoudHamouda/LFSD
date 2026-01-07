
import React from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Stack, Text, IStackStyles } from '@fluentui/react';
import { Transaction } from '../../types/finance';

interface SpendingTrendsProps {
    transactions: Transaction[];
}

const cardStyles: IStackStyles = {
    root: {
        backgroundColor: 'var(--bg-card)',
        borderRadius: 'var(--radius-lg)',
        padding: '20px',
        border: '1px solid var(--border-light)',
        minHeight: '300px',
    },
};

export const SpendingTrends: React.FC<SpendingTrendsProps> = ({ transactions }) => {
    // Aggregate daily spending for the last 7 days
    const data = React.useMemo(() => {
        if (!transactions || transactions.length === 0) return [];

        const today = new Date();
        const last7Days = Array.from({ length: 7 }, (_, i) => {
            const d = new Date();
            d.setDate(today.getDate() - (6 - i)); // 6 days ago to today
            return d;
        });

        return last7Days.map(date => {
            const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
            const dateStr = date.toISOString().split('T')[0];

            // Sum negative amounts (spending) for this day
            const amount = transactions
                .filter(t => t.transaction_date.startsWith(dateStr) && t.amount < 0)
                .reduce((sum, t) => sum + Math.abs(t.amount), 0);

            return { name: dayName, amount };
        });
    }, [transactions]);

    if (data.length === 0) {
        return (
            <Stack styles={cardStyles}>
                <Text variant="large" styles={{ root: { fontWeight: 600, color: 'var(--text-primary)' } }}>
                    Weekly Spending Trend
                </Text>
                <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                    No spending data available for this week.
                </div>
            </Stack>
        );
    }

    return (
        <Stack styles={cardStyles} tokens={{ childrenGap: 10 }}>
            <Text variant="large" styles={{ root: { fontWeight: 600, color: 'var(--text-primary)' } }}>
                Weekly Spending Trend
            </Text>
            <div style={{ width: '100%', height: 250 }}>
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data}>
                        <defs>
                            <linearGradient id="colorAmount" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="var(--color-accent-blue)" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="var(--color-accent-blue)" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-light)" />
                        <XAxis
                            dataKey="name"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: 'var(--text-secondary)', fontSize: 12 }}
                            tickFormatter={(value) => `$${value}`}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-light)', borderRadius: '8px' }}
                            itemStyle={{ color: 'var(--text-primary)' }}
                            labelStyle={{ color: 'var(--text-secondary)' }}
                        />
                        <Area
                            type="monotone"
                            dataKey="amount"
                            stroke="var(--color-accent-blue)"
                            fillOpacity={1}
                            fill="url(#colorAmount)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </Stack>
    );
};
