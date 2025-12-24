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
            backgroundColor: 'var(--bg-surface)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
            padding: 'var(--spacing-md)',
            marginTop: 'var(--spacing-sm)',
            width: '100%',
            maxWidth: '400px'
        }}>
            <h4 style={{ margin: '0 0 var(--spacing-sm) 0', fontSize: '14px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                {title}
            </h4>

            <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
                {/* Option A */}
                <div
                    onClick={() => onSelect && onSelect('A')}
                    style={{
                        flex: 1,
                        padding: 'var(--spacing-sm)',
                        borderRadius: 'var(--radius-sm)',
                        border: `2px solid ${recommendation === 'A' ? 'var(--color-accent-blue)' : 'var(--border-color)'}`,
                        backgroundColor: recommendation === 'A' ? 'rgba(55, 147, 209, 0.05)' : 'transparent',
                        cursor: onSelect ? 'pointer' : 'default',
                        transition: 'all 0.2s'
                    }}
                >
                    <div style={{ fontWeight: 600, fontSize: '14px', marginBottom: '4px' }}>{optionA.title}</div>
                    <div style={{ color: 'var(--color-success, #10b981)', fontSize: '12px', fontWeight: 500 }}>{optionA.impact}</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{optionA.consequence}</div>
                    {recommendation === 'A' && (
                        <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--color-accent-blue)', fontWeight: 600 }}>
                            RECOMMENDED
                        </div>
                    )}
                </div>

                {/* Option B */}
                <div
                    onClick={() => onSelect && onSelect('B')}
                    style={{
                        flex: 1,
                        padding: 'var(--spacing-sm)',
                        borderRadius: 'var(--radius-sm)',
                        border: `2px solid ${recommendation === 'B' ? 'var(--color-accent-blue)' : 'var(--border-color)'}`,
                        backgroundColor: recommendation === 'B' ? 'rgba(55, 147, 209, 0.05)' : 'transparent',
                        cursor: onSelect ? 'pointer' : 'default',
                        transition: 'all 0.2s'
                    }}
                >
                    <div style={{ fontWeight: 600, fontSize: '14px', marginBottom: '4px' }}>{optionB.title}</div>
                    <div style={{ color: 'var(--color-success, #10b981)', fontSize: '12px', fontWeight: 500 }}>{optionB.impact}</div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '12px' }}>{optionB.consequence}</div>
                    {recommendation === 'B' && (
                        <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--color-accent-blue)', fontWeight: 600 }}>
                            RECOMMENDED
                        </div>
                    )}
                </div>
            </div>

            <div style={{ marginTop: 'var(--spacing-md)', fontSize: '13px', color: 'var(--text-primary)', fontStyle: 'italic', borderTop: '1px solid var(--border-color)', paddingTop: 'var(--spacing-sm)' }}>
                "{reasoning}"
            </div>
        </div>
    );
};

export default TradeoffCard;
