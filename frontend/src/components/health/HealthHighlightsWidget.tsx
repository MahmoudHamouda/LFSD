import React from 'react';
import { Moon, Footprints, Activity } from 'lucide-react';
import { HealthDailySummary } from '../../types/health';

interface HealthHighlightsWidgetProps {
    summary: HealthDailySummary | null;
}

const HealthHighlightsWidget: React.FC<HealthHighlightsWidgetProps> = ({ summary }) => {

    const items = [
        {
            label: 'Sleep',
            value: summary ? `${Math.floor(summary.sleepHours)}h ${Math.round((summary.sleepHours % 1) * 60)}m` : '--',
            subLabel: 'Last Night',
            icon: <Moon size={18} color="#8B5CF6" />, // Purple
            bg: '#F5F3FF'
        },
        {
            label: 'Steps',
            value: summary ? summary.stepsCount.toLocaleString() : '--',
            subLabel: 'Today',
            icon: <Footprints size={18} color="#F59E0B" />, // Amber
            bg: '#FFFBEB'
        },
        {
            label: 'Recovery',
            value: summary ? `${summary.recoveryScore}%` : '--',
            subLabel: 'Current Status',
            icon: <Activity size={18} color="#10B981" />, // Emerald
            bg: '#ECFDF5'
        }
    ];

    return (
        <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            border: '1px solid var(--border-color)',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '20px',
            height: 'fit-content'
        }}>
            <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Key Indicators</h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {items.map((item, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <div style={{
                            width: '40px', height: '40px',
                            borderRadius: '10px',
                            backgroundColor: item.bg,
                            display: 'flex', alignItems: 'center', justifyContent: 'center'
                        }}>
                            {item.icon}
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
                            <span style={{ fontSize: '12px', color: 'var(--text-tertiary)', fontWeight: 500 }}>{item.label}</span>
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                                <span style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>{item.value}</span>
                                <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>{item.subLabel}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <button style={{
                width: '100%',
                padding: '8px',
                marginTop: '8px',
                background: 'transparent',
                border: '1px solid var(--border-color)',
                borderRadius: '6px',
                color: 'var(--text-secondary)',
                fontSize: '13px',
                cursor: 'pointer'
            }}>
                View Trends
            </button>
        </div>
    );
};

export default HealthHighlightsWidget;
