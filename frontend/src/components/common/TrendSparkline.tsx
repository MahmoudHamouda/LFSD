import React from 'react';
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis } from 'recharts';

interface TrendSparklineProps {
    data: number[];
    color?: string; // Hex color or CSS variable
    height?: number;
    width?: number | string;
    isPositive?: boolean;
}

const TrendSparkline: React.FC<TrendSparklineProps> = ({
    data,
    color = 'var(--color-primary)',
    height = 40,
    width = '100%',
    isPositive = true,
}) => {
    if (!data || data.length < 2) {
        return (
            <div style={{
                height,
                width,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'var(--bg-secondary)',
                borderRadius: '4px',
                opacity: 0.5
            }}>
                <span style={{ fontSize: '10px', color: 'var(--text-tertiary)' }}>No Trend Data</span>
            </div>
        );
    }

    const chartData = data.map((val, idx) => ({ i: idx, v: val }));
    const strokeColor = isPositive ? 'var(--color-trend-up, #10B981)' : 'var(--color-trend-down, #EF4444)';
    const fillColor = isPositive ? 'var(--color-trend-up, #10B981)' : 'var(--color-trend-down, #EF4444)';

    return (
        <div style={{ height, width }}>
            <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                    <defs>
                        <linearGradient id={`gradient-${isPositive}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={fillColor} stopOpacity={0.3} />
                            <stop offset="95%" stopColor={fillColor} stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <XAxis dataKey="i" hide />
                    <YAxis hide domain={['dataMin', 'dataMax']} />
                    <Area
                        type="monotone"
                        dataKey="v"
                        stroke={strokeColor}
                        fill={`url(#gradient-${isPositive})`}
                        strokeWidth={2}
                        isAnimationActive={false} // Performance
                    />
                </AreaChart>
            </ResponsiveContainer>
        </div>
    );
};

export default TrendSparkline;
