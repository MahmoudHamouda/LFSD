import React from 'react';
import { Stack, Text, IStackStyles, ProgressIndicator } from '@fluentui/react';

const cardStyles: IStackStyles = {
    root: {
        background: 'white',
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        minWidth: '300px',
    },
};

interface SleepCardProps {
    score: number;
    duration: string;
    deepSleep: string;
    remSleep: string;
}

export const SleepCard: React.FC<SleepCardProps> = ({ score, duration, deepSleep, remSleep }) => {
    return (
        <Stack styles={cardStyles} tokens={{ childrenGap: 15 }}>
            <Stack horizontal horizontalAlign="space-between" verticalAlign="center">
                <Text variant="large" style={{ fontWeight: 600 }}>Sleep Performance</Text>
                <div style={{
                    background: score >= 80 ? '#e6ffec' : score >= 60 ? '#fff4e5' : '#ffe6e6',
                    padding: '5px 10px',
                    borderRadius: '12px',
                    color: score >= 80 ? '#107c10' : score >= 60 ? '#d83b01' : '#a80000',
                    fontWeight: 'bold'
                }}>
                    {score}
                </div>
            </Stack>

            <Text variant="xxLarge" style={{ fontWeight: 'bold' }}>{duration}</Text>

            <Stack tokens={{ childrenGap: 10 }}>
                <Stack>
                    <Stack horizontal horizontalAlign="space-between">
                        <Text variant="small">Deep Sleep</Text>
                        <Text variant="small">{deepSleep}</Text>
                    </Stack>
                    <ProgressIndicator percentComplete={0.25} barHeight={4} styles={{ progressBar: { background: '#0078d4' } }} />
                </Stack>
                <Stack>
                    <Stack horizontal horizontalAlign="space-between">
                        <Text variant="small">REM Sleep</Text>
                        <Text variant="small">{remSleep}</Text>
                    </Stack>
                    <ProgressIndicator percentComplete={0.30} barHeight={4} styles={{ progressBar: { background: '#8764b8' } }} />
                </Stack>
            </Stack>
        </Stack>
    );
};
