import React from 'react';
import { Stack, Text, IStackStyles } from '@fluentui/react';

const cardStyles: IStackStyles = {
    root: {
        background: 'white',
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        minWidth: '250px',
    },
};

interface NetWorthCardProps {
    amount: number;
    currency?: string;
}

export const NetWorthCard: React.FC<NetWorthCardProps> = ({ amount, currency = 'USD' }) => {
    const formattedAmount = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
    }).format(amount);

    return (
        <Stack styles={cardStyles} tokens={{ childrenGap: 10 }}>
            <Text variant="large" style={{ fontWeight: 600, color: '#666' }}>Net Worth</Text>
            <Text variant="xxLarge" style={{ fontWeight: 'bold', color: '#0078d4' }}>{formattedAmount}</Text>
            <Text variant="small" style={{ color: '#666' }}>Total Assets - Liabilities</Text>
        </Stack>
    );
};
