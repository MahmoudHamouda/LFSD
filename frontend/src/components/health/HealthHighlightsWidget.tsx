import React from 'react';
import { Moon, Footprints, Activity } from 'lucide-react';
import { HealthDailySummary } from '../../types/health';
import Card from '../common/Card';

interface HealthHighlightsWidgetProps {
    summary: HealthDailySummary | null;
}

const HealthHighlightsWidget: React.FC<HealthHighlightsWidgetProps> = ({ summary }) => {

    const items = [
        {
            label: 'Sleep',
            value: summary ? `${Math.floor(summary.sleepHours)}h ${Math.round((summary.sleepHours % 1) * 60)}m` : '--',
            subLabel: 'Last Night',
            icon: <Moon size={18} color="var(--color-accent-blue)" />, // Was Purple, mapped to Blue or needs new token? 
            // The user wanted design system usage. Let's use accent colors we have.
            // If we need purple, we should add it to tokens. For now, let's stick to system accents.
            // Actually, let's keep the semantic color but use specific hexes if not in tokens OR add to tokens.
            // Tokens has blue, red, orange, green. No purple. 
            // I will map Sleep to Blue (Calm), Steps to Orange (Activity), Recovery to Green.
            bg: 'var(--bg-secondary)'
        },
        {
            label: 'Steps',
            value: summary ? summary.stepsCount.toLocaleString() : '--',
            subLabel: 'Today',
            icon: <Footprints size={18} color="var(--color-accent-orange)" />,
            bg: 'var(--bg-secondary)'
        },
        {
            label: 'Recovery',
            value: summary ? `${summary.recoveryScore}%` : '--',
            subLabel: 'Current Status',
            icon: <Activity size={18} color="var(--status-success)" />,
            bg: 'var(--bg-secondary)'
        }
    ];

    return (
        <Card title="Key Indicators" actionLabel={summary ? "View Trends" : undefined}>
            {summary ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
                    {items.map((item, idx) => (
                        <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
                            <div style={{
                                width: '40px', height: '40px',
                                borderRadius: 'var(--radius-md)',
                                backgroundColor: item.bg,
                                display: 'flex', alignItems: 'center', justifyContent: 'center'
                            }}>
                                {item.icon}
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
                                <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', fontWeight: 500 }}>{item.label}</span>
                                <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-1)' }}>
                                    <span style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>{item.value}</span>
                                    <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{item.subLabel}</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div style={{ textAlign: 'center', padding: '24px 16px', color: 'var(--text-tertiary)' }}>
                    <Activity size={32} style={{ marginBottom: '12px', opacity: 0.3 }} />
                    <div style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '4px' }}>No health data</div>
                    <div style={{ fontSize: '12px', marginBottom: '16px' }}>Connect a health source to track your vitals.</div>
                    <a
                        href="/profile?tab=health&anchor=connections-health"
                        style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            padding: '8px 16px',
                            backgroundColor: 'var(--color-primary)',
                            color: 'white',
                            borderRadius: '6px',
                            fontSize: '13px',
                            fontWeight: 500,
                            textDecoration: 'none',
                            transition: 'background-color 0.2s'
                        }}
                    >
                        Connect Source
                    </a>
                </div>
            )}
        </Card>
    );
};

export default HealthHighlightsWidget;
