import React from 'react';
import { Stack, Text, PrimaryButton, IStackStyles } from '@fluentui/react';
import { useNavigate } from 'react-router-dom';

interface BlurredDataStateProps {
    title: string;
    description: string;
    actionText: string;
    redirectUrl: string;
}

const overlayStyles: IStackStyles = {
    root: {
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(var(--bg-card-rgb), 0.7)',
        backdropFilter: 'blur(8px)',
        zIndex: 10,
        borderRadius: 'var(--radius-lg)',
    }
};

export const BlurredDataState: React.FC<BlurredDataStateProps> = ({ title, description, actionText, redirectUrl }) => {
    const navigate = useNavigate();

    return (
        <div style={{ position: 'relative', overflow: 'hidden', borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-light)', height: '100%', minHeight: '300px' }}>
            {/* Fake Content Background to simulate data */}
            <div style={{ padding: '20px', opacity: 0.3, filter: 'blur(4px)', pointerEvents: 'none' }}>
                <div style={{ height: '20px', width: '60%', background: 'var(--text-secondary)', marginBottom: '20px', borderRadius: '4px' }}></div>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-end', height: '150px' }}>
                    <div style={{ flex: 1, background: 'var(--color-accent-blue)', height: '60%', borderRadius: '4px' }}></div>
                    <div style={{ flex: 1, background: 'var(--color-accent-green)', height: '80%', borderRadius: '4px' }}></div>
                    <div style={{ flex: 1, background: 'var(--color-accent-orange)', height: '40%', borderRadius: '4px' }}></div>
                    <div style={{ flex: 1, background: 'var(--text-tertiary)', height: '90%', borderRadius: '4px' }}></div>
                </div>
            </div>

            {/* Overlay CTA */}
            <Stack styles={overlayStyles} horizontalAlign="center" verticalAlign="center" tokens={{ childrenGap: 16 }}>
                <Text variant="xLarge" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{title}</Text>
                <Text variant="medium" style={{ color: 'var(--text-secondary)', textAlign: 'center', maxWidth: '80%' }}>
                    {description}
                </Text>
                <PrimaryButton
                    text={actionText}
                    onClick={() => navigate(redirectUrl)}
                    styles={{ root: { borderRadius: '20px', padding: '20px 30px' } }}
                />
            </Stack>
        </div>
    );
};
