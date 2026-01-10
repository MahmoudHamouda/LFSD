import React, { useState } from 'react';
import styles from './PillarSummaryCard.module.css';
import { ArrowUp, ArrowDown, ArrowRight, Minus } from 'lucide-react';

export interface PillarData {
    value: number | string;
    trend?: number;
    metricLabel?: string; // Optional label if value needs context (e.g. "Savings Rate")
    subtext?: string;     // e.g. "vs last week"
}

export interface PillarSummaryCardProps {
    title: string;
    icon: React.ReactNode;
    color: string; // Expecting a CSS variable string like 'var(--color-accent-green)' or hex
    overallData: PillarData;
    weekData: PillarData;
    onNavigate: () => void;
}

export const PillarSummaryCard: React.FC<PillarSummaryCardProps> = ({
    title,
    icon,
    color,
    overallData,
    weekData,
    onNavigate
}) => {
    const [view, setView] = useState<'overall' | 'week'>('overall');

    const activeData = view === 'overall' ? overallData : weekData;
    const { value, trend, metricLabel, subtext } = activeData;

    // Helper to format trend
    const renderTrend = (val?: number) => {
        // If undefined/null or 0, showing neutral -- as requested
        if (val === undefined || val === null || val === 0) {
            // User said: "if there is no precentage change calculated show --"
            // Assuming this means literally "--" text, maybe neutral color.
            return <span className={styles.trendNeutral}>--</span>;
        }

        const isPositive = val > 0;
        const TrendIcon = isPositive ? ArrowUp : ArrowDown;
        const trendClass = isPositive ? styles.trendPositive : styles.trendNegative;

        return (
            <span className={`${styles.trendContainer} ${trendClass}`}>
                <TrendIcon size={16} />
                {Math.abs(val).toFixed(1)}%
            </span>
        );
    };

    // Helper to render circle progress
    const radius = 36;
    const circumference = 2 * Math.PI * radius;
    // Ensure value is a number for progress, default to 0 if string
    const numValue = typeof value === 'number' ? value : parseFloat(value as string) || 0;
    const progressOffset = circumference - (Math.min(numValue, 100) / 100) * circumference;

    return (
        <div
            className={styles.card}
            style={{ '--icon-color': color } as React.CSSProperties}
            onClick={onNavigate}
        >
            {/* Mobile Ring View */}
            <div className={styles.mobileRingContainer}>
                <div style={{ position: 'relative', width: '88px', height: '88px' }}>
                    <svg className={styles.progressRing} width="88" height="88">
                        <circle
                            className={styles.progressRingBackground}
                            stroke="#333"
                            strokeWidth="6"
                            fill="transparent"
                            r={radius}
                            cx="44"
                            cy="44"
                        />
                        <circle
                            className={styles.progressRingCircle}
                            stroke={color}
                            strokeWidth="6"
                            fill="transparent"
                            r={radius}
                            cx="44"
                            cy="44"
                            style={{
                                strokeDasharray: `${circumference} ${circumference}`,
                                strokeDashoffset: progressOffset
                            }}
                        />
                    </svg>
                    <div className={styles.mobileRingValue}>
                        {Math.round(numValue)}
                    </div>
                </div>
                <div className={styles.mobileRingLabel}>{title}</div>
                <div className={styles.mobileTrend}>
                    {renderTrend(trend)}
                </div>
            </div>

            {/* Desktop / Card View */}
            <div className={styles.desktopContent}>
                <div className={styles.header}>
                    <div className={styles.iconContainer}>
                        {icon}
                    </div>
                    <div className={styles.title}>{title}</div>
                </div>

                <div className={styles.mainMetric}>
                    {metricLabel && <span className={styles.scoreLabel}>{metricLabel}</span>}
                    <div className={styles.scoreRow}>
                        <span className={styles.scoreValue}>
                            {typeof value === 'number' ? Math.round(value) : value}
                        </span>
                        {renderTrend(trend)}
                    </div>
                    {subtext && <div className={styles.metricContext}>{subtext}</div>}
                </div>

                <div className={styles.toggleContainer}>
                    <span
                        className={`${styles.toggleOption} ${view === 'overall' ? styles.active : ''}`}
                        onClick={(e) => { e.stopPropagation(); setView('overall'); }}
                    >
                        Overall
                    </span>
                    <span className={styles.divider}>|</span>
                    <span
                        className={`${styles.toggleOption} ${view === 'week' ? styles.active : ''}`}
                        onClick={(e) => { e.stopPropagation(); setView('week'); }}
                    >
                        This Week
                    </span>
                </div>

                <div className={styles.footer}>
                    <button
                        className={styles.ctaButton}
                        onClick={onNavigate}
                    >
                        View details <ArrowRight size={16} />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default PillarSummaryCard;
