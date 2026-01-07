import React, { useEffect, useState } from 'react';
import { Plus, Target } from 'lucide-react';
import { getFinancialGoals, createGoal, updateGoal } from '../../api/financialApi';
import styles from './Dashboard.module.css';
import DashboardCTA from '../common/DashboardCTA';
import GoalForm from './GoalForm';
import GoalCard from './GoalCard';

interface GoalsSectionProps {
    variant?: 'finance' | 'time' | 'health' | 'all';
}

const GoalsSection: React.FC<GoalsSectionProps> = ({ variant = 'all' }) => {
    const [showAdd, setShowAdd] = useState(false);
    const [goals, setGoals] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [editingGoal, setEditingGoal] = useState<any>(null);

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

    const handleCreate = async (goalData: any) => {
        try {
            const pillarToSave = variant === 'all' ? goalData.pillar : variant;
            await createGoal({ ...goalData, type: 'custom', priority: 'medium', pillar: pillarToSave });
            setShowAdd(false);
            loadGoals();
        } catch (e) {
            console.error(e);
        }
    };

    const handleUpdate = async (goalData: any) => {
        try {
            await updateGoal(goalData.id, {
                title: goalData.title,
                target_amount: goalData.target_amount,
                monthly_contribution_target: goalData.monthly_contribution_target
            });
            setEditingGoal(null);
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

    // --- FORM VIEW (CREATE OR EDIT) ---
    if (showAdd || editingGoal) {
        return (
            <div style={{ marginBottom: '32px' }}>
                <GoalForm
                    initialData={editingGoal}
                    variant={variant}
                    onSave={editingGoal ? handleUpdate : handleCreate}
                    onCancel={() => { setShowAdd(false); setEditingGoal(null); }}
                />
            </div>
        );
    }

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
                        <GoalCard
                            key={goal.id}
                            goal={goal}
                            pillar={goal.pillar}
                            onUpdate={async (id, updates) => {
                                // Wrapper to match signature if needed, or handle direct update
                                // GoalsSection uses handleUpdate for full obj
                                // But GoalCard calls onUpdate with partial
                                // We can ignore onUpdate if we use onEdit for everything,
                                // but GoalCard might use onUpdate for quick amount.
                                // Let's support it:
                                await updateGoal(id, updates);
                                loadGoals();
                            }}
                            onDelete={async (id) => {
                                // Implement delete if API supports it?
                                // GoalsSection props didn't pass onDelete logic before, 
                                // but standard GoalCard has it.
                                // For now, pass undefined or simple log if no delete API ready
                                console.log("Delete not implemented in GoalsSection yet");
                            }}
                            onEdit={(g) => setEditingGoal(g)}
                        />
                    ))}
                </div>
            </div>
        );
    }

    return null;
};

export default GoalsSection;
