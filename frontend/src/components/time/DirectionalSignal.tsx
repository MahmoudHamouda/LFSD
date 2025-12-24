import React from 'react';
import { ArrowUpRight, ArrowRight, ArrowDownRight, HelpCircle } from 'lucide-react';
import { Stack, Text } from '@fluentui/react';

export type SignalType = 'Improving' | 'Stable' | 'Declining' | 'Not enough data yet';

interface DirectionalSignalProps {
    signal: SignalType;
}

export const DirectionalSignal: React.FC<DirectionalSignalProps> = ({ signal }) => {
    let icon = <HelpCircle size={14} />;
    let color = 'var(--text-tertiary)';

    switch (signal) {
        case 'Improving':
            icon = <ArrowUpRight size={14} />;
            color = 'var(--color-accent-green)'; // Positive
            break;
        case 'Stable':
            icon = <ArrowRight size={14} />;
            color = 'var(--text-secondary)'; // Neutral
            break;
        case 'Declining':
            icon = <ArrowDownRight size={14} />;
            color = 'var(--color-accent-orange)'; // Warning/Attention (not necessarily failure)
            break;
        case 'Not enough data yet':
        default:
            icon = <HelpCircle size={14} />;
            color = 'var(--text-tertiary)';
            break;
    }

    return (
        <Stack horizontal verticalAlign="center" tokens={{ childrenGap: 6 }}>
            <div style={{ color: color, display: 'flex', alignItems: 'center' }}>
                {icon}
            </div>
            <Text variant="small" style={{ color: 'var(--text-secondary)' }}>
                Early signal: <span style={{ fontWeight: 600, color: color }}>{signal}</span>
            </Text>
        </Stack>
    );
};
