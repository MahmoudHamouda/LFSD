/**
 * SummaryIndexBar Component
 * 
 * Displays key user indexes (Financial Wellbeing, Time Saved, Balance)
 * prominently at the top of key screens.
 */

import React from 'react';
import styles from './SummaryIndexBar.module.css';

// ============================================================================
// Types
// ============================================================================

export interface IndexData {
    id: string;
    label: string;
    value: number;        // 0-100
    trend?: number;       // +/- percentage change
    variant?: 'primary' | 'secondary';
    icon?: React.ReactNode; // Changed from string to ReactNode
    onClick?: () => void;
}

export interface SummaryIndexBarProps {
    indexes: IndexData[];
    variant?: 'default' | 'compact';
}

// ============================================================================
// Component
// ============================================================================

export const SummaryIndexBar: React.FC<SummaryIndexBarProps> = ({
    indexes,
    variant = 'default'
}) => {
    const formatValue = (value: number): string => {
        return Math.round(value).toString();
    };

    const formatTrend = (trend: number): string => {
        const sign = trend >= 0 ? '+' : '';
        return `${sign}${trend.toFixed(1)}%`;
    };

    const getTrendColor = (trend: number): string => {
        if (trend > 0) return styles.trendPositive;
        if (trend < 0) return styles.trendNegative;
        return styles.trendNeutral;
    };

    const getIndexColor = (value: number): string => {
        if (value >= 75) return styles.indexHigh;
        if (value >= 50) return styles.indexMedium;
        return styles.indexLow;
    };

    return (
        <div className={`${styles.container} ${variant === 'compact' ? styles.compact : ''}`}>
            {indexes.map((index) => (
                <div
                    key={index.id}
                    className={`${styles.indexCard} ${index.variant === 'primary' ? styles.primary : styles.secondary} ${index.onClick ? styles.clickable : ''}`}
                    onClick={index.onClick}
                >
                    {index.icon && (
                        <div className={styles.iconContainer}>
                            {index.icon}
                        </div>
                    )}

                    <div className={styles.content}>
                        <div className={styles.label}>{index.label}</div>

                        <div className={styles.valueContainer}>
                            <span className={`${styles.value} ${getIndexColor(index.value)}`}>
                                {formatValue(index.value)}
                            </span>

                            {index.trend !== undefined && (
                                <span className={`${styles.trend} ${getTrendColor(index.trend)}`}>
                                    {formatTrend(index.trend)}
                                </span>
                            )}
                        </div>
                    </div>

                    {/* Progress bar */}
                    <div className={styles.progressBar}>
                        <div
                            className={`${styles.progressFill} ${getIndexColor(index.value)}`}
                            style={{ width: `${index.value}%` }}
                        />
                    </div>
                </div>
            ))}
        </div>
    );
};

export default SummaryIndexBar;
