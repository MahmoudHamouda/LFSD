import React from 'react';
import { Shield, Clock, AlertTriangle, ArrowRight } from 'lucide-react';

import TrendSparkline from '../common/TrendSparkline';

interface ProgressivePillarCardProps {
    title: string;
    description: string;
    score: number;
    coverageDays: number;
    requiredDays: number;
    riskThreshold: number;
    profileLink: string;
    trendData?: number[]; // Added trend data prop
    onClick?: () => void;
}

const ProgressivePillarCard: React.FC<ProgressivePillarCardProps> = ({
    title,
    description,
    score,
    coverageDays,
    requiredDays,
    riskThreshold,
    profileLink,
    trendData,
    onClick
}) => {
    // 1. Determine State
    let state: 'LEARNING' | 'STABLE' | 'AT_RISK' = 'LEARNING';

    if (coverageDays >= requiredDays) {
        if (score < riskThreshold) {
            state = 'AT_RISK';
        } else {
            state = 'STABLE';
        }
    }

    // 2. State Config (Colors, Icons, Labels)
    const config = {
        LEARNING: {
            badge: 'Learning',
            icon: Clock,
            color: 'var(--text-tertiary)', // Neutral grey/muted blue
            bgColor: 'var(--bg-secondary)',
            borderColor: 'var(--border-light)',
            ringColor: 'var(--border-light)',
        },
        STABLE: {
            badge: 'Stable',
            icon: Shield, // Circle/Dot in spec, using Shield for general stability or just a Dot
            color: 'var(--color-accent-green)',
            bgColor: 'var(--bg-card)',
            borderColor: 'var(--border-light)',
            ringColor: 'var(--color-accent-green)',
        },
        AT_RISK: {
            badge: 'At Risk',
            icon: AlertTriangle,
            color: 'var(--color-accent-red)',
            bgColor: 'var(--bg-error-subtle)',
            borderColor: 'var(--border-light)',
            ringColor: 'var(--color-accent-red)',
        }
    }[state];

    // Override icon for Stable to be a dot if strictly following spec, 
    // but Shield is often better for "Stable". Let's stick to the spec's intent.

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
                height: '100%',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                position: 'relative',
                minHeight: '220px'
            }}
            className="hover:shadow-md"
        >
            {/* HEAD */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', margin: 0, maxWidth: '70%' }}>
                    {title}
                </h3>
                <div style={{
                    display: 'flex', alignItems: 'center', gap: '4px',
                    padding: '4px 8px', borderRadius: '12px',
                    backgroundColor: state === 'AT_RISK' ? 'var(--bg-badge-error)' : state === 'STABLE' ? 'var(--bg-badge-success)' : 'var(--bg-badge-neutral)',
                    border: '1px solid var(--border-light)'
                }}>
                    {state === 'LEARNING' && <Clock size={12} color={config.color} />}
                    {state === 'STABLE' && <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: config.color }} />}
                    {state === 'AT_RISK' && <AlertTriangle size={12} color={config.color} />}
                    <span style={{ fontSize: '11px', fontWeight: 600, color: config.color, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                        {config.badge}
                    </span>
                </div>
            </div>

            {/* BODY - PRIMARY (Score Ring) */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', marginBottom: '16px' }}>
                <div style={{
                    width: '80px', height: '80px', borderRadius: '50%',
                    border: `4px solid ${state === 'LEARNING' ? 'var(--border-light)' : config.ringColor}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    opacity: state === 'LEARNING' ? 0.5 : 1
                }}>
                    <span style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)' }}>
                        {state === 'LEARNING' ? '—' : Math.round(score)}
                    </span>
                </div>
            </div>

            {/* BODY - SECONDARY (Progress / Trend) */}
            <div style={{ marginBottom: '20px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {state === 'LEARNING' ? (
                    <div style={{ width: '100%' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                                {coverageDays} of {requiredDays} days collected
                            </span>
                        </div>
                        {/* Thin Progress Bar */}
                        <div style={{ width: '100%', height: '4px', backgroundColor: 'var(--border-light)', borderRadius: '2px' }}>
                            <div style={{
                                width: `${Math.min((coverageDays / requiredDays) * 100, 100)}%`,
                                height: '100%',
                                backgroundColor: 'var(--color-accent-blue)',
                                borderRadius: '2px'
                            }} />
                        </div>
                    </div>
                ) : (
                    <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {trendData && trendData.length > 0 ? (
                            <TrendSparkline
                                data={trendData}
                                color={config.color}
                                isPositive={trendData[trendData.length - 1] >= trendData[0]}
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
                        Add data <ArrowRight size={14} style={{ marginLeft: '4px' }} />
                    </div>
                ) : (
                    <div style={{ display: 'flex', alignItems: 'center', color: 'var(--text-secondary)', fontSize: '13px', fontWeight: 500 }}>
                        View trends <ArrowRight size={14} style={{ marginLeft: '4px' }} />
                    </div>
                )}
            </div>
        </div>
    );
};

export default ProgressivePillarCard;
