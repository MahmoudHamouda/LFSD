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
        if (val === undefined || val === null) return null;
        if (val === 0) return <span className={styles.trendNeutral}><Minus size={14} /> 0.0%</span>;

        const isPositive = val > 0;
        // For some metrics (like debt), positive might be bad, but assuming standard scores for now.
        // If standardized score (0-100), higher is better.
        const TrendIcon = isPositive ? ArrowUp : ArrowDown;
        const trendClass = isPositive ? styles.trendPositive : styles.trendNegative;

        return (
            <span className={`${styles.trendContainer} ${trendClass}`}>
                <TrendIcon size={16} />
                {Math.abs(val).toFixed(1)}%
            </span>
        );
    };

    return (
        <div
            className={styles.card}
            style={{ '--icon-color': color } as React.CSSProperties}
            onClick={onNavigate}
        >
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
    );
};

export default PillarSummaryCard;
