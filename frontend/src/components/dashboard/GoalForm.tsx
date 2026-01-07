import React, { useState, useEffect } from 'react';
import styles from './Dashboard.module.css';

interface GoalFormProps {
    initialData?: any;
    variant?: 'finance' | 'time' | 'health' | 'all';
    onSave: (goal: any) => void;
    onCancel: () => void;
}

const GoalForm: React.FC<GoalFormProps> = ({ initialData, variant = 'all', onSave, onCancel }) => {
    const [goal, setGoal] = useState({
        title: '',
        target_amount: 0,
        target_date: '',
        monthly_contribution_target: 0,
        pillar: variant === 'all' ? 'finance' : variant,
        ...initialData
    });

    const handleSave = () => {
        onSave(goal);
    };

    return (
        <div className={styles.newGoalForm}>
            <h3 className={styles.sectionTitle} style={{ marginBottom: '16px' }}>
                {initialData ? 'Edit Goal' : `Set a New ${variant === 'all' ? 'Life' : variant.charAt(0).toUpperCase() + variant.slice(1)} Goal`}
            </h3>
            <div style={{ maxWidth: '480px' }}>
                {variant === 'all' && (
                    <div style={{ marginBottom: '12px' }}>
                        <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Category</label>
                        <select
                            className={styles.formInput}
                            value={goal.pillar}
                            onChange={e => setGoal({ ...goal, pillar: e.target.value as any })}
                            disabled={!!initialData} // Lock category on edit
                        >
                            <option value="finance">Finance</option>
                            <option value="time">Time</option>
                            <option value="health">Health</option>
                        </select>
                    </div>
                )}
                <div style={{ marginBottom: '12px' }}>
                    <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Goal Name</label>
                    <input
                        type="text"
                        placeholder="e.g. Emergency Fund"
                        className={styles.formInput}
                        value={goal.title}
                        onChange={e => setGoal({ ...goal, title: e.target.value })}
                    />
                </div>
                <div className={styles.formRow}>
                    <div>
                        <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Target Amount ($)</label>
                        <input
                            type="number"
                            placeholder="0"
                            className={styles.formInput}
                            value={goal.target_amount || ''}
                            onChange={e => setGoal({ ...goal, target_amount: parseFloat(e.target.value) })}
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Monthly Saving ($)</label>
                        <input
                            type="number"
                            placeholder="0"
                            className={styles.formInput}
                            value={goal.monthly_contribution_target || ''}
                            onChange={e => setGoal({ ...goal, monthly_contribution_target: parseFloat(e.target.value) })}
                        />
                    </div>
                </div>

                <div className={styles.formActions} style={{ marginTop: '24px' }}>
                    <button
                        onClick={handleSave}
                        disabled={!goal.title || !goal.target_amount}
                        className={styles.saveButton}
                    >
                        {initialData ? 'Update Goal' : 'Save Goal'}
                    </button>
                    <button onClick={onCancel} className={styles.cancelButton}>Cancel</button>
                </div>
            </div>
        </div>
    );
};

export default GoalForm;
