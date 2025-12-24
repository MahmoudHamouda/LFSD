import React, { useState } from 'react';
import { Target, TrendingUp, MoreHorizontal, Edit2, Trash, Check } from 'lucide-react';
import styles from './Dashboard.module.css';

interface GoalCardProps {
    goal: any;
    onUpdate: (goalId: string, updates: any) => void;
    onDelete: (goalId: string) => void;
}

const GoalCard: React.FC<GoalCardProps> = ({ goal, onUpdate, onDelete }) => {
    const [isEditing, setIsEditing] = useState(false);
    const [editValue, setEditValue] = useState(goal.saved_amount || 0);

    const progress = Math.min(100, (goal.saved_amount / goal.target_amount) * 100);
    const isCompleted = progress >= 100;

    // Calculate months left
    const now = new Date();
    const target = new Date(goal.target_date);
    const monthsLeft = Math.max(0, (target.getFullYear() - now.getFullYear()) * 12 + target.getMonth() - now.getMonth());

    const handleSave = () => {
        onUpdate(goal.id, { saved_amount: parseFloat(editValue) });
        setIsEditing(false);
    };

    return (
        <div className={styles.goalCard}>
            <div className={styles.goalHeader}>
                <div className={styles.goalHeaderLeft}>
                    <div className={`${styles.goalIconWrapper} ${isCompleted ? styles.goalIconWrapperCompleted : ''}`}>
                        <Target className={styles.goalIcon} />
                    </div>
                    <div className={styles.goalTitleBlock}>
                        <h3 className={styles.goalTitle}>{goal.title}</h3>
                        <p className={styles.goalMeta}>
                            Target: {new Date(goal.target_date).toLocaleDateString()} ({monthsLeft}mo left)
                        </p>
                    </div>
                </div>

                <div className={styles.goalActions}>
                    <button onClick={() => onDelete(goal.id)} className={`${styles.actionButton} ${styles.actionButtonDelete}`}>
                        <Trash className="w-3 h-3" />
                    </button>
                </div>
            </div>

            <div className={styles.goalBody}>
                <div className={styles.amountRow}>
                    <div className={styles.currentAmount}>
                        {isEditing ? (
                            <input
                                type="number"
                                value={editValue}
                                onChange={(e) => setEditValue(e.target.value)}
                                className={styles.amountInput}
                                autoFocus
                            />
                        ) : (
                            <span onClick={() => setIsEditing(true)} className={styles.editableAmount}>
                                ${goal.saved_amount?.toLocaleString()}
                            </span>
                        )}
                        <span className={styles.targetAmount}>
                            of ${goal.target_amount?.toLocaleString()}
                        </span>
                    </div>
                    {isEditing && (
                        <button onClick={handleSave} className={styles.actionButton}>
                            <Check className="w-3 h-3" />
                        </button>
                    )}
                </div>

                <div className={styles.progressBarContainer}>
                    <div
                        className={`${styles.progressBarFill} ${isCompleted ? styles.progressBarComplete : ''}`}
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </div>

            <div className={styles.goalFooter}>
                <span>{Math.round(progress)}% Funded</span>
                <span>${goal.monthly_contribution_target}/mo needed</span>
            </div>
        </div>
    );
};

export default GoalCard;
