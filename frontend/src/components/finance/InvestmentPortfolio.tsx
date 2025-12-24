import React from 'react';
import { Stack, Text, IStackStyles, Icon } from '@fluentui/react';

const cardStyles: IStackStyles = {
    root: {
        background: 'white',
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        minWidth: '300px',
    },
};

interface InvestmentPortfolioProps {
    totalValue: number;
    dailyChangePercent: number;
}

export const InvestmentPortfolio: React.FC<InvestmentPortfolioProps> = ({ totalValue, dailyChangePercent }) => {
    const formattedValue = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
    }).format(totalValue);

    const isPositive = dailyChangePercent >= 0;

    return (
        <Stack styles={cardStyles} tokens={{ childrenGap: 15 }}>
            <Stack horizontal horizontalAlign="space-between" verticalAlign="center">
                <Text variant="large" style={{ fontWeight: 600 }}>Investments</Text>
                <Icon iconName="StockDown" style={{ fontSize: '20px', color: '#0078d4' }} />
            </Stack>

            <Stack>
                <Text variant="xxLarge" style={{ fontWeight: 'bold' }}>{formattedValue}</Text>
                <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 5 }}>
                    <Icon iconName={isPositive ? 'Up' : 'Down'} style={{ color: isPositive ? 'green' : 'red', fontSize: '12px' }} />
                    <Text variant="medium" style={{ color: isPositive ? 'green' : 'red', fontWeight: 600 }}>
                        {Math.abs(dailyChangePercent)}% Today
                    </Text>
                </Stack>
            </Stack>

            {/* Placeholder for Chart */}
            <div style={{ height: '60px', background: '#f3f9fd', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Text variant="small" style={{ color: '#0078d4' }}>Performance Chart Placeholder</Text>
            </div>
        </Stack>
    );
};
