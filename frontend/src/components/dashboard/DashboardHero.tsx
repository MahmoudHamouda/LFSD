import React from 'react';
import styles from './DashboardHero.module.css';
import { ArrowUp, ArrowDown, Minus, Plus, Target } from 'lucide-react';

export interface DashboardHeroProps {
    title: string;
    icon: React.ReactNode;
    color: string; // CSS variable e.g. 'var(--color-accent-green)'
    score: number;
    trend?: number;
    goals?: any[] | null;
    onAddGoal?: () => void;
    variant?: 'finance' | 'time' | 'health';
}

export const DashboardHero: React.FC<DashboardHeroProps> = ({
    title,
    icon,
    color,
    score,
    trend,
    goals,
    onAddGoal,
    variant
}) => {

    // Helper for trend
    const renderTrend = (val?: number) => {
        if (val === undefined || val === null) return null;
        if (val === 0) return <span className={styles.trendNeutral}><Minus size={16} /> 0.0%</span>;

        const isPositive = val > 0;
        const trendClass = isPositive ? styles.trendPositive : styles.trendNegative;
        const TrendIcon = isPositive ? ArrowUp : ArrowDown;

        return (
            <span className={`${styles.trendRow} ${trendClass}`}>
                <TrendIcon size={18} />
                {Math.abs(val).toFixed(1)}%
            </span>
        );
    };

    const calculateTimeToReach = (goal: any) => {
        const remaining = goal.target_amount - (goal.saved_amount || 0);
        if (remaining <= 0) return 'Done';
        if (goal.monthly_contribution_target <= 0) return null;

        const months = Math.ceil(remaining / goal.monthly_contribution_target);
        if (months >= 12) {
            const years = Math.floor(months / 12);
            const remainingMonths = months % 12;
            return `${years}y ${remainingMonths > 0 ? `${remainingMonths}m` : ''}`;
        }
        return `${months}m`;
    };

    return (
        <div
            className={styles.heroContainer}
            style={{ '--icon-color': color } as React.CSSProperties}
        >
            {/* Left 1/3: Score */}
            <div className={styles.scoreSection}>
                <div className={styles.scoreHeader}>
                    <div className={styles.pillarIcon}>
                        {icon}
                    </div>
                    <span className={styles.pillarLabel}>{title}</span>
                </div>

                <div className={styles.scoreRow}>
                    <span className={styles.scoreValue}>{Math.round(score)}</span>
                    {renderTrend(trend)}
                </div>
            </div>

            {/* Right 2/3: Goal */}
            <div className={styles.goalSection}>
                {goals && goals.length > 0 ? (
                    <div className={styles.goalsListContainer}>
                        <div className={styles.goalsHeader}>
                            <span className={styles.goalLabel}>Active Goals</span>
                            <button className={styles.miniAddButton} onClick={onAddGoal}>
                                <Plus size={14} /> Add
                            </button>
                        </div>
                        <div className={styles.goalsList}>
                            {goals.map(g => (
                                <div key={g.id} className={styles.goalItem}>
                                    <div className={styles.goalItemMain}>
                                        <Target size={14} className={styles.goalIcon} />
                                        <span className={styles.goalItemTitle}>{g.title}</span>
                                    </div>
                                    <div className={styles.goalItemMeta}>
                                        <span>Target: ${g.target_amount?.toLocaleString()}</span>
                                        {g.saved_amount !== undefined && (
                                            <span className={styles.goalProgress}>
                                                • {Math.round((g.saved_amount / g.target_amount) * 100)}%
                                            </span>
                                        )}
                                        {calculateTimeToReach(g) && (
                                            <span style={{ opacity: 0.6 }}> • {calculateTimeToReach(g)}</span>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className={styles.emptyGoal}>
                        <span>No goal active for this pillar.</span>
                        <button className={styles.addGoalButton} onClick={onAddGoal}>
                            <Plus size={18} /> Add Goal
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DashboardHero;
