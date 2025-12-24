import React from 'react';
import { Stack, Text, IStackStyles } from '@fluentui/react';

const cardStyles: IStackStyles = {
    root: {
        background: 'white',
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        minWidth: '300px',
    },
};

interface RecoverySparklineProps {
    score: number;
    hrv: number;
    rhr: number;
}

export const RecoverySparkline: React.FC<RecoverySparklineProps> = ({ score, hrv, rhr }) => {
    return (
        <Stack styles={cardStyles} tokens={{ childrenGap: 15 }}>
            <Stack horizontal horizontalAlign="space-between" verticalAlign="center">
                <Text variant="large" style={{ fontWeight: 600 }}>Recovery</Text>
                <div style={{
                    background: score >= 66 ? '#e6ffec' : score >= 33 ? '#fff4e5' : '#ffe6e6',
                    padding: '5px 10px',
                    borderRadius: '12px',
                    color: score >= 66 ? '#107c10' : score >= 33 ? '#d83b01' : '#a80000',
                    fontWeight: 'bold'
                }}>
                    {score}%
                </div>
            </Stack>

            <Stack horizontal tokens={{ childrenGap: 20 }}>
                <Stack>
                    <Text variant="small" style={{ color: '#666' }}>HRV</Text>
                    <Text variant="xLarge">{hrv} ms</Text>
                </Stack>
                <Stack>
                    <Text variant="small" style={{ color: '#666' }}>RHR</Text>
                    <Text variant="xLarge">{rhr} bpm</Text>
                </Stack>
            </Stack>

            {/* Placeholder for Sparkline */}
            <div style={{ height: '40px', background: '#f3f2f1', borderRadius: '4px', display: 'flex', alignItems: 'flex-end', padding: '0 5px', gap: '2px' }}>
                {[40, 50, 45, 60, 55, 70, 65, 80, 75, 90].map((h, i) => (
                    <div key={i} style={{ flex: 1, height: `${h}%`, background: '#0078d4', borderRadius: '2px 2px 0 0' }}></div>
                ))}
            </div>
        </Stack>
    );
};
