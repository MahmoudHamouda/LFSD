import React from 'react';

interface TradeoffOption {
    title: string;
    impact: string; // e.g., "Saves $40", "Add 20 mins"
    consequence: string; // e.g., "Less comfort", "More stress"
    score?: number; // 0-100, purely visual
}

interface TradeoffCardProps {
    title: string;
    optionA: TradeoffOption;
    optionB: TradeoffOption;
    recommendation: 'A' | 'B';
    reasoning: string;
    onSelect?: (option: 'A' | 'B') => void;
}

const TradeoffCard: React.FC<TradeoffCardProps> = ({ title, optionA, optionB, recommendation, reasoning, onSelect }) => {
    return (
        <div style={{
            backgroundColor: 'var(--bg-card)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
            padding: 'var(--space-4)',
            marginTop: 'var(--space-2)',
            width: '100%',
            maxWidth: '400px',
            boxShadow: 'var(--shadow-sm)'
        }}>
            <h4 style={{ margin: '0 0 var(--space-2) 0', fontSize: '12px', color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 700 }}>
                {title}
            </h4>

            <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                {/* Option A */}
                <div
                    onClick={() => onSelect && onSelect('A')}
                    style={{
                        flex: 1,
                        padding: 'var(--space-3)',
                        borderRadius: 'var(--radius-md)',
                        border: `2px solid ${recommendation === 'A' ? 'var(--color-accent-blue)' : 'var(--border-light)'}`,
                        backgroundColor: recommendation === 'A' ? 'var(--bg-badge-success)' : 'var(--bg-secondary)',
                        cursor: onSelect ? 'pointer' : 'default',
                        transition: 'all 0.2s'
                    }}
                >
                    <div style={{ fontWeight: 600, fontSize: '14px', marginBottom: '4px', color: 'var(--text-primary)' }}>{optionA.title}</div>
                    <div style={{ color: 'var(--status-success)', fontSize: '12px', fontWeight: 600 }}>{optionA.impact}</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{optionA.consequence}</div>
                    {recommendation === 'A' && (
                        <div style={{ marginTop: '8px', fontSize: '10px', color: 'var(--color-accent-blue)', fontWeight: 800, textTransform: 'uppercase' }}>
                            RECOMMENDED
                        </div>
                    )}
                </div>

                {/* Option B */}
                <div
                    onClick={() => onSelect && onSelect('B')}
                    style={{
                        flex: 1,
                        padding: 'var(--space-3)',
                        borderRadius: 'var(--radius-md)',
                        border: `2px solid ${recommendation === 'B' ? 'var(--color-accent-blue)' : 'var(--border-light)'}`,
                        backgroundColor: recommendation === 'B' ? 'var(--bg-badge-success)' : 'var(--bg-secondary)',
                        cursor: onSelect ? 'pointer' : 'default',
                        transition: 'all 0.2s'
                    }}
                >
                    <div style={{ fontWeight: 600, fontSize: '14px', marginBottom: '4px', color: 'var(--text-primary)' }}>{optionB.title}</div>
                    <div style={{ color: 'var(--status-success)', fontSize: '12px', fontWeight: 600 }}>{optionB.impact}</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{optionB.consequence}</div>
                    {recommendation === 'B' && (
                        <div style={{ marginTop: '8px', fontSize: '10px', color: 'var(--color-accent-blue)', fontWeight: 800, textTransform: 'uppercase' }}>
                            RECOMMENDED
                        </div>
                    )}
                </div>
            </div>

            <div style={{ marginTop: 'var(--space-4)', fontSize: '13px', color: 'var(--text-primary)', fontStyle: 'italic', borderTop: '1px solid var(--border-light)', paddingTop: 'var(--space-2)' }}>
                "{reasoning}"
            </div>
        </div>
    );
};

export default TradeoffCard;
