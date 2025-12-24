
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
    // TODO: In a real implementation, aggregate daily spending from 'transactions' prop.
    // For now, using mock data for visual demonstration if not enough real data.

    const data = [
        { name: 'Mon', amount: 120 },
        { name: 'Tue', amount: 200 },
        { name: 'Wed', amount: 150 },
        { name: 'Thu', amount: 300 },
        { name: 'Fri', amount: 250 },
        { name: 'Sat', amount: 380 },
        { name: 'Sun', amount: 190 },
    ];

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
