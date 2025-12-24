import React, { useEffect, useState } from 'react';
import { Stack, Text, PrimaryButton } from '@fluentui/react';
import { useNavigate } from 'react-router-dom';
import { LineChart, Line, ResponsiveContainer, YAxis } from 'recharts';
import { getFinancialHistory } from '../../api/financialApi';

const cardStyles = {
    root: {
        backgroundColor: 'var(--bg-card)',
        borderRadius: 'var(--radius-lg)',
        padding: '24px',
        boxShadow: 'var(--shadow-sm)',
        border: '1px solid var(--border-light)',
    }
};

const subScoreCardStyles = {
    backgroundColor: 'var(--bg-secondary)',
    borderRadius: 'var(--radius-md)',
    padding: '12px',
    border: '1px solid var(--border-light)',
    display: 'flex',
    flexDirection: 'column' as 'column',
    justifyContent: 'space-between',
    minHeight: '100px'
};

interface FinancialScoreBreakdownProps {
    score: number;
    subscores: Record<string, number>;
    hasData: boolean;
    loading?: boolean;
}

export const FinancialScoreBreakdown: React.FC<FinancialScoreBreakdownProps> = ({ score, subscores, hasData, loading }) => {
    const navigate = useNavigate();
    const [history, setHistory] = useState<any[]>([]);

    useEffect(() => {
        if (hasData) {
            getFinancialHistory(10).then(data => {
                // Formatting for charts: simplest is just reverse order to be chronological
                if (Array.isArray(data)) {
                    setHistory(data.reverse());
                }
            });
        }
    }, [hasData]);

    const maxScores: Record<string, number> = {
        income_stability: 15,
        burn_rate: 15,
        savings_momentum: 15,
        debt_stress: 15,
        recurring_commitments: 10,
        spending_stability: 10,
        liquidity_cushion: 10,
        risk_indicators: 10
    };

    // Helper to get chart data for a specific subscore key
    const getChartData = (key: string) => {
        if (!history || history.length === 0) return [];
        return history.map((snapshot, idx) => ({
            name: idx,
            value: snapshot[`${key}_score`] || 0
        }));
    };

    if (loading) {
        return <div style={{ padding: '20px', textAlign: 'center' }}>Loading Score Data...</div>;
    }

    return (
        <Stack styles={cardStyles} tokens={{ childrenGap: 20 }}>
            <Stack horizontal horizontalAlign="space-between" verticalAlign="center">
                <Text variant="xLarge" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Financial Pulse</Text>
                {!hasData && (
                    <PrimaryButton
                        text="Update Data"
                        onClick={() => navigate('/profile')}
                        iconProps={{ iconName: 'Sync' }}
                    />
                )}
            </Stack>

            <Stack horizontal horizontalAlign="center" tokens={{ childrenGap: 40 }} wrap>
                {/* Main Score - Left or Top */}
                <div style={{
                    width: '140px',
                    height: '140px',
                    borderRadius: '50%',
                    background: `conic-gradient(var(--color-accent-blue) ${score}%, var(--bg-secondary) ${score}% 100%)`,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    position: 'relative'
                }}>
                    <div style={{
                        width: '116px',
                        height: '116px',
                        borderRadius: '50%',
                        background: 'var(--bg-card)',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        alignItems: 'center'
                    }}>
                        <span style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>{Math.round(score)}</span>
                        <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Overall</span>
                    </div>
                </div>

                {/* Subscores Grid */}
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', // Wider for charts
                    gap: '16px',
                    width: '100%',
                    flex: 1
                }}>
                    {Object.entries(subscores || {}).map(([key, value]) => {
                        const maxVal = maxScores[key] || 10;
                        const data = getChartData(key);
                        const isPositive = data.length > 1 && data[data.length - 1].value >= data[0].value;

                        return (
                            <div key={key} style={subScoreCardStyles}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                    <div>
                                        <div style={{ fontSize: '13px', color: 'var(--text-secondary)', textTransform: 'capitalize', fontWeight: 500 }}>
                                            {key.replace(/_/g, ' ')}
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginTop: '4px' }}>
                                            <span style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)' }}>
                                                {value}
                                            </span>
                                            <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>
                                                / {maxVal}
                                            </span>
                                        </div>
                                    </div>

                                    {/* Mini Sparkline */}
                                    <div style={{ width: '80px', height: '40px' }}>
                                        {hasData && data.length > 0 ? (
                                            <ResponsiveContainer width="100%" height="100%">
                                                <LineChart data={data}>
                                                    <Line
                                                        type="monotone"
                                                        dataKey="value"
                                                        stroke={isPositive ? "var(--color-accent-green)" : "#FF5252"}
                                                        strokeWidth={2}
                                                        dot={false}
                                                    />
                                                    <YAxis domain={[0, maxVal]} hide />
                                                </LineChart>
                                            </ResponsiveContainer>
                                        ) : (
                                            <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '10px', color: 'var(--text-tertiary)' }}>No Trend</div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </Stack>

            {!hasData && (
                <Stack horizontalAlign="center" styles={{ root: { padding: '10px', backgroundColor: 'rgba(var(--color-accent-blue-rgb), 0.1)', borderRadius: '8px' } }}>
                    <Text variant="small" style={{ color: 'var(--text-secondary)', textAlign: 'center' }}>
                        Connect your accounts to see 3-month history trends for each score.
                    </Text>
                </Stack>
            )}
        </Stack>
    );
};
