import React from 'react';
import { Stack, Text, PrimaryButton, DefaultButton, TextField, IStackStyles } from '@fluentui/react';

const sectionStyles: IStackStyles = {
    root: {
        background: 'white',
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        marginTop: '20px',
    },
};

export const ConnectFinance: React.FC = () => {
    return (
        <Stack styles={sectionStyles} tokens={{ childrenGap: 10 }}>
            <Text variant="large" style={{ fontWeight: 600 }}>Connect Accounts</Text>
            <Text variant="small">Link your bank accounts and investments securely.</Text>
            <Stack horizontal tokens={{ childrenGap: 10 }}>
                <PrimaryButton text="Connect Stripe" />
                <DefaultButton text="Connect Plaid" />
            </Stack>
        </Stack>
    );
};

export const AddAsset: React.FC = () => {
    return (
        <Stack styles={sectionStyles} tokens={{ childrenGap: 10 }}>
            <Text variant="large" style={{ fontWeight: 600 }}>Add Manual Asset</Text>
            <Stack tokens={{ childrenGap: 10 }}>
                <TextField label="Asset Name" placeholder="e.g., Real Estate, Crypto" />
                <Stack horizontal tokens={{ childrenGap: 10 }}>
                    <TextField label="Value" type="number" prefix="$" />
                    <TextField label="Category" />
                </Stack>
                <PrimaryButton text="Save Asset" />
            </Stack>
        </Stack>
    );
};

export const AddTransaction: React.FC = () => {
    return (
        <Stack styles={sectionStyles} tokens={{ childrenGap: 10 }}>
            <Text variant="large" style={{ fontWeight: 600 }}>Add Transaction</Text>
            <Stack tokens={{ childrenGap: 10 }}>
                <TextField label="Merchant / Description" placeholder="e.g., Grocery Store" />
                <Stack horizontal tokens={{ childrenGap: 10 }}>
                    <TextField label="Amount" type="number" prefix="$" />
                    <TextField label="Date" type="date" />
                </Stack>
                <PrimaryButton text="Save Transaction" />
            </Stack>
        </Stack>
    );
};
