import React, { useState } from 'react';
import { X, Calendar } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

interface TrendPanelProps {
    title: string;
    data: { date: string; value: number }[];
    onClose: () => void;
    unit?: string;
}

const TrendPanel: React.FC<TrendPanelProps> = ({ title, data, onClose, unit = '' }) => {
    const [range, setRange] = useState<30 | 90>(30);

    // Filter data based on range (assuming strictly ordered data for now, or just limit count)
    // In a real app, this would filter by date. Here we just take suffix.
    const displayData = data.slice(-range);
    const isPositive = displayData.length > 1 && displayData[displayData.length - 1].value >= displayData[0].value;
    const color = isPositive ? 'var(--color-trend-up, #10B981)' : 'var(--color-trend-down, #EF4444)';

    return (
        <div style={{
            marginTop: '16px',
            background: 'var(--bg-secondary)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-color)',
            padding: '24px',
            animation: 'slideDown 0.2s ease-out'
        }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
                <div>
                    <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '4px' }}>
                        {title}
                    </h3>
                    <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                        {range} Day Trend
                    </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {/* Range Toggle */}
                    <div style={{
                        display: 'flex',
                        background: 'var(--bg-card)',
                        borderRadius: '8px',
                        padding: '2px',
                        border: '1px solid var(--border-color)'
                    }}>
                        <button
                            onClick={() => setRange(30)}
                            style={{
                                padding: '4px 8px',
                                fontSize: '12px',
                                borderRadius: '6px',
                                border: 'none',
                                background: range === 30 ? 'var(--bg-hover)' : 'transparent',
                                color: range === 30 ? 'var(--text-primary)' : 'var(--text-secondary)',
                                cursor: 'pointer'
                            }}
                        >30D</button>
                        <button
                            onClick={() => setRange(90)}
                            style={{
                                padding: '4px 8px',
                                fontSize: '12px',
                                borderRadius: '6px',
                                border: 'none',
                                background: range === 90 ? 'var(--bg-hover)' : 'transparent',
                                color: range === 90 ? 'var(--text-primary)' : 'var(--text-secondary)',
                                cursor: 'pointer'
                            }}
                        >90D</button>
                    </div>

                    <button
                        onClick={onClose}
                        style={{
                            background: 'transparent',
                            border: 'none',
                            color: 'var(--text-secondary)',
                            cursor: 'pointer',
                            padding: '4px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            borderRadius: '50%',
                            transition: 'background 0.2s'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                        onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                    >
                        <X size={20} />
                    </button>
                </div>
            </div>

            {/* Chart */}
            <div style={{ height: '300px', width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={displayData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                        <defs>
                            <linearGradient id="colorGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor={color} stopOpacity={0.2} />
                                <stop offset="95%" stopColor={color} stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" opacity={0.5} />
                        <XAxis
                            dataKey="date"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fontSize: 12, fill: 'var(--text-tertiary)' }}
                            minTickGap={30}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fontSize: 12, fill: 'var(--text-tertiary)' }}
                            width={40}
                        />
                        <Tooltip
                            contentStyle={{
                                background: 'var(--bg-card)',
                                border: '1px solid var(--border-color)',
                                borderRadius: '8px',
                                boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
                            }}
                            itemStyle={{ color: 'var(--text-primary)' }}
                            labelStyle={{ color: 'var(--text-secondary)', marginBottom: '4px' }}
                            cursor={{ stroke: 'var(--text-tertiary)', strokeDasharray: '3 3' }}
                        />
                        <Area
                            type="monotone"
                            dataKey="value"
                            stroke={color}
                            strokeWidth={2}
                            fillOpacity={1}
                            fill="url(#colorGradient)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default TrendPanel;
