import React, { useEffect, useState } from 'react';
import { Plus, Target } from 'lucide-react';
import { getFinancialGoals, createGoal } from '../../api/financialApi';
import styles from './Dashboard.module.css';
import DashboardCTA from '../common/DashboardCTA';

interface GoalsSectionProps {
    variant?: 'finance' | 'time' | 'health' | 'all';
}

const GoalsSection: React.FC<GoalsSectionProps> = ({ variant = 'all' }) => {
    const [showAdd, setShowAdd] = useState(false);
    const [goals, setGoals] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [newGoal, setNewGoal] = useState({
        title: '',
        target_amount: 0,
        target_date: '',
        monthly_contribution_target: 0,
        pillar: variant === 'all' ? 'finance' : variant
    });

    useEffect(() => {
        loadGoals();
    }, [variant]);

    const loadGoals = async () => {
        setLoading(true);
        try {
            const pillarParam = variant === 'all' ? undefined : variant;
            const data = await getFinancialGoals(pillarParam);
            setGoals(data);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async () => {
        try {
            const pillarToSave = variant === 'all' ? newGoal.pillar : variant;
            await createGoal({ ...newGoal, type: 'custom', priority: 'medium', pillar: pillarToSave });
            setShowAdd(false);
            setNewGoal({ title: '', target_amount: 0, target_date: '', monthly_contribution_target: 0, pillar: variant === 'all' ? 'finance' : variant });
            loadGoals();
        } catch (e) {
            console.error(e);
        }
    };

    const getEmptyCopy = () => {
        switch (variant) {
            case 'time': return { title: 'Master your time', text: 'Set clear focus goals to reclaim your schedule.' };
            case 'health': return { title: 'Optimize your bio-engine', text: 'Track specific health targets to boost longevity.' };
            default: return { title: 'Your goals give your numbers meaning', text: 'People with a clear financial goal save up to 2× more consistently.' };
        }
    };

    const calculateTimeToReach = (goal: any) => {
        const remaining = goal.target_amount - (goal.saved_amount || 0);
        if (remaining <= 0) return 'Target reached!';
        if (goal.monthly_contribution_target <= 0) return 'Indefinite (Set monthly target)';

        const months = Math.ceil(remaining / goal.monthly_contribution_target);
        if (months >= 12) {
            const years = Math.floor(months / 12);
            const remainingMonths = months % 12;
            return `${years} year${years > 1 ? 's' : ''} ${remainingMonths > 0 ? `& ${remainingMonths} month${remainingMonths > 1 ? 's' : ''}` : ''}`;
        }
        return `${months} month${months > 1 ? 's' : ''}`;
    };

    const getPillarColor = (pillar: string) => {
        switch (pillar) {
            case 'finance': return 'var(--color-accent-green)';
            case 'time': return 'var(--color-accent-blue)';
            case 'health': return 'var(--color-accent-red)';
            default: return 'var(--color-accent-blue)';
        }
    };

    const copy = getEmptyCopy();

    if (loading) return <div style={{ padding: '20px', color: 'var(--text-secondary)' }}>Loading goals...</div>;

    // --- A) EMPTY STATE ---
    if (goals.length === 0 && !showAdd) {
        return (
            <div className={styles.emptyState}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                    <div style={{
                        width: '48px', height: '48px', borderRadius: '50%',
                        backgroundColor: 'rgba(55, 147, 209, 0.1)', display: 'flex', alignItems: 'center',
                        justifyContent: 'center', marginBottom: '16px'
                    }}>
                        <Target size={24} color="var(--color-accent-blue)" />
                    </div>
                    <h2 style={{ fontSize: '20px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '8px' }}>{copy.title}</h2>
                    <p style={{ color: 'var(--text-secondary)', maxWidth: '400px', margin: '0 auto 24px auto', fontSize: '14px' }}>{copy.text}</p>
                    <button
                        onClick={() => setShowAdd(true)}
                        style={{
                            padding: '12px 24px', backgroundColor: 'var(--color-accent-blue)', color: 'white',
                            borderRadius: '8px', fontWeight: 500, border: 'none', cursor: 'pointer',
                            display: 'flex', alignItems: 'center', gap: '8px'
                        }}
                    >
                        Add Your First Goal <Plus size={18} />
                    </button>
                </div>
            </div>
        );
    }

    // --- B) ACTIVE STATE ---
    if (!showAdd && goals.length > 0) {
        return (
            <div style={{ marginBottom: '32px' }}>
                <div className={styles.sectionHeader}>
                    <h3 className={styles.sectionTitle}>Active Goals</h3>
                    <button
                        onClick={() => setShowAdd(true)}
                        className={styles.createButton}
                    >
                        <Plus size={16} /> Add Goal
                    </button>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {goals.map((goal) => (
                        <div
                            key={goal.id}
                            className={styles.goalCard}
                            style={{
                                borderLeft: `4px solid ${getPillarColor(goal.pillar)}`,
                                flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px'
                            }}
                        >
                            <div style={{ flex: 1, minWidth: '200px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <h3 className={styles.goalTitle} style={{ fontSize: '16px', fontWeight: 600 }}>{goal.title}</h3>
                                    </div>
                                    {variant === 'all' && (
                                        <span style={{
                                            fontSize: '10px', textTransform: 'uppercase', fontWeight: 700,
                                            padding: '2px 6px', borderRadius: '4px',
                                            color: getPillarColor(goal.pillar),
                                            backgroundColor: `color-mix(in srgb, ${getPillarColor(goal.pillar)} 10%, transparent)`,
                                            border: `1px solid color-mix(in srgb, ${getPillarColor(goal.pillar)} 30%, transparent)`
                                        }}>
                                            {goal.pillar}
                                        </span>
                                    )}
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '12px', fontSize: '13px' }}>
                                    <div>
                                        <span style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '2px' }}>Target</span>
                                        <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>${goal.target_amount.toLocaleString()}</span>
                                    </div>
                                    <div>
                                        <span style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '2px' }}>Current</span>
                                        <span style={{ color: 'var(--color-accent-green)', fontWeight: 500 }}>${(goal.saved_amount || 0).toLocaleString()}</span>
                                    </div>
                                    <div style={{ borderLeft: '1px solid var(--border-color)', paddingLeft: '12px' }}>
                                        <span style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: '2px' }}>Time to Goal</span>
                                        <span style={{ color: 'var(--color-accent-blue)', fontWeight: 500 }}>{calculateTimeToReach(goal)}</span>
                                    </div>
                                </div>
                            </div>
                            <div style={{ width: '100%', maxWidth: '120px' }}>
                                <DashboardCTA label="View Details" targetTab={goal.pillar === 'finance' ? 'financial' : goal.pillar} targetAnchor="goals" variant="ghost" />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className={styles.newGoalForm}>
            <h3 className={styles.sectionTitle} style={{ marginBottom: '16px' }}>Set a New {variant === 'all' ? 'Life' : variant.charAt(0).toUpperCase() + variant.slice(1)} Goal</h3>
            <div style={{ maxWidth: '480px' }}>
                {variant === 'all' && (
                    <div style={{ marginBottom: '12px' }}>
                        <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Category</label>
                        <select
                            className={styles.formInput}
                            value={newGoal.pillar}
                            onChange={e => setNewGoal({ ...newGoal, pillar: e.target.value as any })}
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
                        value={newGoal.title}
                        onChange={e => setNewGoal({ ...newGoal, title: e.target.value })}
                    />
                </div>
                <div className={styles.formRow}>
                    <div>
                        <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Target Amount ($)</label>
                        <input
                            type="number"
                            placeholder="0"
                            className={styles.formInput}
                            value={newGoal.target_amount || ''}
                            onChange={e => setNewGoal({ ...newGoal, target_amount: parseFloat(e.target.value) })}
                        />
                    </div>
                    <div>
                        <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>Monthly Saving ($)</label>
                        <input
                            type="number"
                            placeholder="0"
                            className={styles.formInput}
                            value={newGoal.monthly_contribution_target || ''}
                            onChange={e => setNewGoal({ ...newGoal, monthly_contribution_target: parseFloat(e.target.value) })}
                        />
                    </div>
                </div>

                <div className={styles.formActions} style={{ marginTop: '24px' }}>
                    <button
                        onClick={handleCreate}
                        disabled={!newGoal.title || !newGoal.target_amount}
                        className={styles.saveButton}
                    >
                        Save Goal
                    </button>
                    <button onClick={() => setShowAdd(false)} className={styles.cancelButton}>Cancel</button>
                </div>
            </div>
        </div>
    );
};

export default GoalsSection;


