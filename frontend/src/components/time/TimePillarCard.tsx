import React from 'react';
import { Clock, Shield, AlertTriangle, ArrowRight } from 'lucide-react';
import TrendSparkline from '../common/TrendSparkline';
import { DirectionalSignal, SignalType } from './DirectionalSignal';

interface TimePillarCardProps {
    title: string;
    score: number | null | undefined; // Null/Undefined means no score yet
    coverageDays: number;
    requiredDays: number;
    riskThreshold: number;
    trendData?: number[]; // For Level 2 Sparkline
    earlySignal?: SignalType; // For Level 1 Directional Signal
    onClick?: () => void;
}

export const TimePillarCard: React.FC<TimePillarCardProps> = ({
    title,
    score,
    coverageDays,
    requiredDays,
    riskThreshold,
    trendData,
    earlySignal,
    onClick
}) => {
    // 1. Determine State
    let state: 'LEARNING' | 'STABLE' | 'AT_RISK' = 'LEARNING';

    // Ensure we have a valid score number for comparison, treating null as 0 for safety but logic mainly depends on coverage
    const safeScore = score ?? 0;

    if (coverageDays >= requiredDays) {
        if (typeof score === 'number' && safeScore < riskThreshold) {
            state = 'AT_RISK';
        } else {
            state = 'STABLE';
        }
    }

    // 2. State Config
    const config = {
        LEARNING: {
            badge: 'Learning',
            icon: Clock,
            color: 'var(--text-tertiary)',
            bgColor: 'var(--bg-secondary)',
            borderColor: 'var(--border-light)',
            ringColor: 'var(--border-light)',
            displayValue: '—'
        },
        STABLE: {
            badge: 'Stable',
            icon: Shield,
            color: 'var(--color-accent-green)',
            bgColor: 'var(--bg-card)',
            borderColor: 'var(--border-light)',
            ringColor: 'var(--color-accent-green)',
            displayValue: Math.round(safeScore).toString()
        },
        AT_RISK: {
            badge: 'At Risk',
            icon: AlertTriangle,
            color: '#EF4444',
            bgColor: '#FEF2F2',
            borderColor: '#FECACA',
            ringColor: '#EF4444',
            displayValue: Math.round(safeScore).toString()
        }
    }[state];

    return (
        <div
            onClick={onClick}
            style={{
                backgroundColor: config.bgColor,
                border: `1px solid ${config.borderColor}`,
                borderRadius: '12px',
                padding: '20px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                minHeight: '220px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
            }}
            className="hover:shadow-md"
        >
            {/* COMPONENT HEADER */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', margin: 0, maxWidth: '75%' }}>
                    {title}
                </h3>
                <div style={{
                    display: 'flex', alignItems: 'center', gap: '4px',
                    padding: '4px 8px', borderRadius: '12px',
                    backgroundColor: state === 'AT_RISK' ? 'rgba(239, 68, 68, 0.1)' : 'var(--bg-tertiary)',
                    border: `1px solid ${state === 'AT_RISK' ? 'rgba(239, 68, 68, 0.2)' : 'transparent'}`
                }}>
                    {state === 'LEARNING' && <Clock size={12} color={config.color} />}
                    {state === 'STABLE' && <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: config.color }} />}
                    {state === 'AT_RISK' && <AlertTriangle size={12} color={config.color} />}
                    <span style={{ fontSize: '11px', fontWeight: 600, color: config.color, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        {config.badge}
                    </span>
                </div>
            </div>

            {/* MAIN SCORE RING */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                <div style={{
                    width: '80px', height: '80px', borderRadius: '50%',
                    border: `4px solid ${state === 'LEARNING' ? 'var(--border-light)' : config.ringColor}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    opacity: state === 'LEARNING' ? 0.5 : 1
                }}>
                    <span style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)' }}>
                        {config.displayValue}
                    </span>
                </div>
            </div>

            {/* DATA SIGNAL / TREND */}
            <div style={{ marginBottom: '20px', minHeight: '32px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {state === 'LEARNING' ? (
                    earlySignal ? (
                        <DirectionalSignal signal={earlySignal} />
                    ) : (
                        <div style={{ width: '100%', padding: '0 10px' }}>
                            {/* Progress Bar fallback if no signal */}
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                <span style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>Learning...</span>
                                <span style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>{Math.round((coverageDays / requiredDays) * 100)}%</span>
                            </div>
                            <div style={{ width: '100%', height: '4px', backgroundColor: 'var(--border-light)', borderRadius: '2px' }}>
                                <div style={{
                                    width: `${Math.min((coverageDays / requiredDays) * 100, 100)}%`,
                                    height: '100%',
                                    backgroundColor: 'var(--color-accent-blue)',
                                    borderRadius: '2px'
                                }} />
                            </div>
                        </div>
                    )
                ) : (
                    <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {trendData && trendData.length > 0 ? (
                            <TrendSparkline
                                data={trendData}
                                color={config.color}
                                isPositive={trendData[trendData.length - 1] >= trendData[0]}
                                height={32}
                            />
                        ) : (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <div style={{ height: '2px', width: '20px', backgroundColor: config.color }} />
                                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Trend available</span>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* FOOTER - ACTION */}
            <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: '16px', marginTop: 'auto' }}>
                {state === 'LEARNING' ? (
                    <div style={{ display: 'flex', alignItems: 'center', color: 'var(--color-accent-blue)', fontSize: '13px', fontWeight: 500 }}>
                        Continue logging <ArrowRight size={14} style={{ marginLeft: '4px' }} />
                    </div>
                ) : (
                    <div style={{ display: 'flex', alignItems: 'center', color: 'var(--text-secondary)', fontSize: '13px', fontWeight: 500 }}>
                        View analysis <ArrowRight size={14} style={{ marginLeft: '4px' }} />
                    </div>
                )}
            </div>
        </div>
    );
};
