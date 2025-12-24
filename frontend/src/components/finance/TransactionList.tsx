import React from 'react';
import { Stack, Text, IStackStyles, Icon } from '@fluentui/react';
import { Transaction } from '../../types/finance';

const containerStyles: IStackStyles = {
    root: {
        background: 'white',
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        marginTop: '20px',
    },
};

const itemStyles: IStackStyles = {
    root: {
        padding: '12px 0',
        borderBottom: '1px solid #f3f2f1',
    },
};

interface TransactionListProps {
    transactions: Transaction[];
}

export const TransactionList: React.FC<TransactionListProps> = ({ transactions }) => {
    const formatCurrency = (amount: number, currency: string = 'USD') => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
        }).format(Math.abs(amount));
    };

    return (
        <Stack styles={containerStyles}>
            <Text variant="large" style={{ fontWeight: 600, marginBottom: '15px' }}>Recent Transactions</Text>
            <Stack>
                {transactions.map((txn) => (
                    <Stack key={txn.id} horizontal horizontalAlign="space-between" verticalAlign="center" styles={itemStyles}>
                        <Stack horizontal tokens={{ childrenGap: 15 }} verticalAlign="center">
                            <div style={{
                                width: '40px', height: '40px', borderRadius: '50%',
                                background: '#f3f2f1', display: 'flex', alignItems: 'center', justifyContent: 'center'
                            }}>
                                <Icon iconName="Shop" style={{ color: '#666' }} />
                            </div>
                            <Stack>
                                <Text variant="medium" style={{ fontWeight: 600 }}>{txn.merchantName}</Text>
                                <Text variant="small" style={{ color: '#666' }}>{txn.categoryPrimary} • {new Date(txn.transactionDate).toLocaleDateString()}</Text>
                            </Stack>
                        </Stack>
                        <Text variant="medium" style={{ fontWeight: 600, color: txn.amount > 0 ? 'green' : 'black' }}>
                            {txn.amount > 0 ? '+' : '-'}{formatCurrency(txn.amount, txn.currencyCode)}
                        </Text>
                    </Stack>
                ))}
                {transactions.length === 0 && <Text>No recent transactions.</Text>}
            </Stack>
        </Stack>
    );
};
