import React from 'react';
import { Shield, Clock, AlertTriangle, ArrowRight, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Stack, Text } from '@fluentui/react';

import TrendSparkline from '../common/TrendSparkline';

export interface HealthPillarCardProps {
    title: string;
    description?: string;
    score: number | null; // Null if no score available
    coverageDays: number;
    requiredDays: number;
    riskThreshold: number;
    trendDirection: 'improving' | 'stable' | 'declining' | 'unknown';
    trendData?: number[]; // Added trend data
    onClick?: () => void;
}

const HealthPillarCard: React.FC<HealthPillarCardProps> = ({
    title,
    description,
    score,
    coverageDays,
    requiredDays,
    riskThreshold,
    trendDirection,
    trendData, // Destructure
    onClick
}) => {
    // ... State logic ...
    let state: 'LEARNING' | 'STABLE' | 'AT_RISK' = 'LEARNING';

    if (coverageDays >= requiredDays && score !== null) {
        if (score < riskThreshold) {
            state = 'AT_RISK';
        } else {
            state = 'STABLE';
        }
    } else {
        state = 'LEARNING';
    }

    // ... Config ...
    const config = {
        LEARNING: {
            badge: 'Learning',
            icon: Clock,
            color: 'var(--text-tertiary, #8b96a5)',
            bgColor: 'var(--bg-secondary, #f8f9fa)',
            borderColor: 'var(--border-light, #e1e4e8)',
            ringColor: 'var(--border-light, #e1e4e8)',
        },
        STABLE: {
            badge: 'Stable',
            icon: Shield,
            color: 'var(--color-accent-green, #10b981)',
            bgColor: 'var(--bg-card, #ffffff)',
            borderColor: 'var(--border-light, #e1e4e8)',
            ringColor: 'var(--color-accent-green, #10b981)',
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

    const getDirectionalSignal = () => {
        if (state !== 'LEARNING') return null;
        if (trendDirection === 'unknown') return "Not enough data yet";
        const signalMap = {
            'improving': 'Improving',
            'stable': 'Stable',
            'declining': 'Declining'
        };
        return `Early signal: ${signalMap[trendDirection]}`;
    };

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
                cursor: onClick ? 'pointer' : 'default',
                transition: 'all 0.2s ease',
                minHeight: '220px',
                width: '100%',
                boxSizing: 'border-box'
            }}
            className="hover:shadow-md"
        >
            {/* HERDER */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', margin: 0, maxWidth: '70%', lineHeight: '1.2' }}>
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
                    border: `4px solid ${state === 'LEARNING' ? 'var(--border-light, #e1e4e8)' : config.ringColor}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    opacity: state === 'LEARNING' ? 0.5 : 1
                }}>
                    <span style={{ fontSize: '24px', fontWeight: 700, color: 'var(--text-primary)' }}>
                        {state === 'LEARNING' ? '—' : (score !== null ? Math.round(score) : '—')}
                    </span>
                </div>
            </div>

            {/* BODY - SECONDARY (Progress / Signal) */}
            <div style={{ marginBottom: '20px', minHeight: '34px', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                {state === 'LEARNING' ? (
                    <div style={{ width: '100%' }}>
                        {/* Trend Signal Text */}
                        <div style={{ marginBottom: '8px', textAlign: 'center' }}>
                            <Text variant="small" style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>
                                {getDirectionalSignal()}
                            </Text>
                        </div>

                        {/* Progress Bar for Data Collection */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                            <span style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>
                                {coverageDays}/{requiredDays} days
                            </span>
                        </div>
                        <div style={{ width: '100%', height: '4px', backgroundColor: 'var(--border-light, #e1e4e8)', borderRadius: '2px' }}>
                            <div style={{
                                width: `${Math.min((coverageDays / requiredDays) * 100, 100)}%`,
                                height: '100%',
                                backgroundColor: 'var(--color-accent-blue, #3b82f6)',
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
                                height={32}
                            />
                        ) : (
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                                <div style={{ height: '2px', width: '20px', backgroundColor: config.color }} />
                                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Trend available</span>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* FOOTER - ACTION */}
            <div style={{ borderTop: '1px solid var(--border-light, #eaecef)', paddingTop: '16px', marginTop: 'auto' }}>
                {state === 'LEARNING' ? (
                    <div style={{ display: 'flex', alignItems: 'center', color: 'var(--color-accent-blue, #3b82f6)', fontSize: '13px', fontWeight: 500 }}>
                        {/* Was 'Add data' -> now generic or Manage. But 'Add data' for learning is OK if it points to Profile. 
                            However, the unified contract says "CTA text: Manage data ->" or specific. 
                            Let's keep "Add data" but implementation will redirect. 
                            Wait, User Req said: "Replace ALL of the above with: CTA text: 'Manage data ->'"
                        */}
                        Manage data <ArrowRight size={14} style={{ marginLeft: '4px' }} />
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

export default HealthPillarCard;
