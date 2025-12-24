import React from 'react';
import { Stack, Text, IStackStyles } from '@fluentui/react';
import { Sparkline } from '../common/Sparkline';
import { ArrowUpRight, ArrowRight, ArrowDownRight, HelpCircle } from 'lucide-react';

const containerStyles: IStackStyles = {
    root: {
        background: 'white',
        borderRadius: '12px',
        padding: '24px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        alignItems: 'center',
        height: '100%',
        justifyContent: 'center',
        border: '1px solid var(--border-light)',
    },
};

interface ProductivityScoreProps {
    score?: number;
    trendData?: number[];
    isUnlocked?: boolean;
    coverageDays?: number;
}

export const ProductivityScore: React.FC<ProductivityScoreProps> = ({
    score = 0,
    trendData = [],
    isUnlocked = false,
    coverageDays = 0
}) => {
    // Determine Signal for Locked State (Mock logic for now based on score or random)
    // In real app, this would come from props
    const signal = 'Improving';

    return (
        <Stack styles={containerStyles} tokens={{ childrenGap: 16 }}>
            <Text variant="large" style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Productivity Score</Text>

            <div style={{ position: 'relative', width: '160px', height: '160px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <svg width="160" height="160" viewBox="0 0 160 160">
                    {/* Background Circle */}
                    <circle cx="80" cy="80" r="70" fill="none" stroke="var(--bg-tertiary)" strokeWidth="12" />

                    {/* Progress Circle - Only show if unlocked or partial? Spec says 'Always visible' score but maybe different state */}
                    {/* If unlocked, show actual score ring. If locked, maybe just gray or partial? 
                         Spec: "If locked: Show directional arrow only". 
                         Let's keep the ring but make it subtle or just the arrow inside.
                     */}
                    {isUnlocked && (
                        <circle
                            cx="80"
                            cy="80"
                            r="70"
                            fill="none"
                            stroke="var(--color-accent-blue)" // Blue for productivity generally
                            strokeWidth="12"
                            strokeDasharray={`${2 * Math.PI * 70}`}
                            strokeDashoffset={`${2 * Math.PI * 70 * (1 - score / 100)}`}
                            transform="rotate(-90 80 80)"
                            style={{ transition: 'stroke-dashoffset 0.8s ease' }}
                            strokeLinecap="round"
                        />
                    )}
                </svg>

                <div style={{ position: 'absolute', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    {isUnlocked ? (
                        <>
                            <Text variant="xxLarge" style={{ fontWeight: 700, fontSize: '36px', lineHeight: '1' }}>{Math.round(score)}</Text>
                            <div style={{ marginTop: '8px', height: '24px', width: '60px' }}>
                                <Sparkline data={trendData} color="var(--color-accent-blue)" width={60} height={24} strokeWidth={2} />
                            </div>
                        </>
                    ) : (
                        <>
                            {/* Locked State: Directional Arrow */}
                            <ArrowUpRight size={48} color="var(--text-secondary)" />
                            <Text variant="medium" style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>Improving</Text>
                        </>
                    )}
                </div>
            </div>

            <Text variant="small" style={{ color: 'var(--text-secondary)', textAlign: 'center', maxWidth: '80%' }}>
                {isUnlocked
                    ? "Tracking how you use your time over weeks, not days"
                    : `Learning your rhythm... (${coverageDays} days data)`
                }
            </Text>
        </Stack>
    );
};
