import React, { useState } from 'react';
import { Target, Edit2, Trash, Check } from 'lucide-react';
import styles from './Dashboard.module.css';

interface GoalCardProps {
    goal: any;
    onUpdate?: (goalId: string, updates: any) => void;
    onDelete?: (goalId: string) => void;
    onEdit?: (goal: any) => void;
    pillar?: string; // e.g. 'finance', 'time', 'health'
}

const GoalCard: React.FC<GoalCardProps> = ({ goal, onUpdate, onDelete, onEdit, pillar }) => {
    // Only use internal state if onUpdate is provided AND onEdit is NOT (legacy mode)
    // But we prefer onEdit for standardization.
    const [isEditingAmount, setIsEditingAmount] = useState(false);
    const [editValue, setEditValue] = useState(goal.saved_amount || 0);

    const progress = Math.min(100, ((goal.saved_amount || 0) / goal.target_amount) * 100);
    const isCompleted = progress >= 100;

    const getPillarColor = (p?: string) => {
        switch (p || goal.pillar) {
            case 'finance': return 'var(--color-accent-green)';
            case 'time': return 'var(--color-accent-blue)';
            case 'health': return 'var(--color-accent-red)';
            default: return 'var(--color-accent-blue)';
        }
    };

    const color = getPillarColor(pillar);

    // Calculate Time to Reach
    const calculateTimeToReach = () => {
        const remaining = goal.target_amount - (goal.saved_amount || 0);
        if (remaining <= 0) return 'Target reached!';
        if ((goal.monthly_contribution_target || 0) <= 0) return 'Indefinite';

        const months = Math.ceil(remaining / goal.monthly_contribution_target);
        if (months >= 12) {
            const years = Math.floor(months / 12);
            const remainingMonths = months % 12;
            return `${years}y ${remainingMonths > 0 ? `${remainingMonths}m` : ''}`;
        }
        return `${months}m`;
    };

    const handleQuickSave = (e: React.FormEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (onUpdate) {
            onUpdate(goal.id, { saved_amount: parseFloat(editValue) });
            setIsEditingAmount(false);
        }
    };

    const handleEditClick = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (onEdit) {
            onEdit(goal);
        } else {
            setIsEditingAmount(true);
        }
    };

    return (
        <div
            className={styles.goalCard}
            style={{ borderLeft: `4px solid ${color}` }}
            onClick={(e) => {
                if (onEdit) onEdit(goal);
            }}
        >
            <div className={styles.goalHeader}>
                <div className={styles.goalHeaderLeft}>
                    <div className={`${styles.goalIconWrapper} ${isCompleted ? styles.goalIconWrapperCompleted : ''}`}>
                        <Target className={styles.goalIcon} style={{ color: color }} />
                    </div>
                    <div className={styles.goalTitleBlock}>
                        <h3 className={styles.goalTitle}>{goal.title}</h3>
                        <p className={styles.goalMeta}>
                            Target: {new Date(goal.target_date || Date.now()).toLocaleDateString()}
                        </p>
                    </div>
                </div>

                <div className={styles.goalActions}>
                    <button onClick={handleEditClick} className={styles.actionButton}>
                        <Edit2 className="w-3 h-3" />
                    </button>
                    {onDelete && (
                        <button onClick={(e) => { e.stopPropagation(); onDelete(goal.id); }} className={`${styles.actionButton} ${styles.actionButtonDelete}`}>
                            <Trash className="w-3 h-3" />
                        </button>
                    )}
                </div>
            </div>

            <div className={styles.goalBody}>
                <div className={styles.amountRow}>
                    <div className={styles.currentAmount}>
                        {isEditingAmount ? (
                            <div onClick={e => e.stopPropagation()}>
                                <input
                                    type="number"
                                    value={editValue}
                                    onChange={(e) => setEditValue(e.target.value)}
                                    className={styles.amountInput}
                                    autoFocus
                                    onBlur={() => setIsEditingAmount(false)}
                                    onKeyDown={e => { if (e.key === 'Enter') handleQuickSave(e as any); }}
                                />
                            </div>
                        ) : (
                            <span className={styles.editableAmount} style={{ color }}>
                                {(pillar === 'finance' || goal.pillar === 'finance') ? '$' : ''}{(goal.saved_amount || 0).toLocaleString()}
                            </span>
                        )}
                        <span className={styles.targetAmount}>
                            of {(pillar === 'finance' || goal.pillar === 'finance') ? '$' : ''}{goal.target_amount?.toLocaleString()}
                        </span>
                    </div>
                </div>

                <div className={styles.progressBarContainer}>
                    <div
                        className={`${styles.progressBarFill} ${isCompleted ? styles.progressBarComplete : ''}`}
                        style={{ width: `${progress}%`, backgroundColor: color }}
                    />
                </div>

                <div className={styles.goalFooter}>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {calculateTimeToReach()} left
                    </span>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {(pillar === 'finance' || goal.pillar === 'finance' ? '$' : '')}{goal.monthly_contribution_target}/mo
                    </span>
                </div>
            </div>
        </div >
    );
};

export default GoalCard;
