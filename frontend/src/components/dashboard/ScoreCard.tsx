import React from 'react';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';
import styles from './Dashboard.module.css';

interface ScoreCardProps {
    title: string;
    score: number;
    description: string;
    status: 'success' | 'warning' | 'danger' | 'neutral';
    trend?: 'up' | 'down' | 'flat';
    onClick?: () => void;
    locked?: boolean;
}

const ScoreCard: React.FC<ScoreCardProps> = ({ title, score, description, status, trend, onClick, locked }) => {

    const getStatusClass = (s: string) => {
        switch (s) {
            case 'success': return styles.statusSuccess;
            case 'warning': return styles.statusWarning;
            case 'danger': return styles.statusDanger;
            default: return styles.statusNeutral;
        }
    };

    const getScoreClass = (score: number) => {
        if (score >= 80) return styles.cardValueGreen;
        if (score >= 60) return styles.cardValueYellow;
        return styles.cardValueRed;
    };

    return (
        <div
            onClick={onClick}
            className={`${styles.scoreCard} ${locked ? styles.scoreCardLocked : ''}`}
        >
            <div className={styles.cardHeader}>
                <h3 className={styles.cardTitle}>{title}</h3>
                <div className={`${styles.cardStatusBadge} ${getStatusClass(status)}`}>
                    {locked ? 'Locked' : status.toUpperCase()}
                </div>
            </div>

            <div className={styles.cardValueContainer}>
                <span className={`${styles.cardValue} ${locked ? styles.cardValueBlurred : getScoreClass(score)}`}>
                    {locked ? '??.?' : score.toFixed(1)}
                </span>
                {trend && !locked && (
                    <div className={styles.trendIndicator}>
                        {trend === 'up' && <ArrowUpRight className={`${styles.trendIcon} ${styles.trendUp}`} />}
                        {trend === 'down' && <ArrowDownRight className={`${styles.trendIcon} ${styles.trendDown}`} />}
                        {trend === 'flat' && <Minus className={`${styles.trendIcon} ${styles.trendFlat}`} />}
                        vs last month
                    </div>
                )}
            </div>

            <p className={styles.cardDesc}>
                {description}
            </p>
        </div>
    );
};

export default ScoreCard;
