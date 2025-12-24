import React, { useEffect, useState } from 'react';
import { Plus, ArrowRight, Target } from 'lucide-react';
import { getFinancialGoals, createGoal } from '../../api/financialApi';
import styles from './Dashboard.module.css';
import DashboardCTA from '../common/DashboardCTA';

interface GoalsSectionProps {
    variant?: 'finance' | 'time' | 'health';
}

const GoalsSection: React.FC<GoalsSectionProps> = ({ variant = 'finance' }) => {
    // Shared State
    const [showAdd, setShowAdd] = useState(false);

    // FINANCE STATE
    const [financeGoals, setFinanceGoals] = useState<any[]>([]);
    const [newFinanceGoal, setNewFinanceGoal] = useState({
        title: '',
        target_amount: 0,
        target_date: '',
        monthly_contribution_target: 0
    });

    // MOCK STATE FOR TIME/HEALTH
    const [mockGoals, setMockGoals] = useState<any[]>([
        variant === 'time' ? { title: '40 Continuous Focus Hours', target: '40h', current: '22h', unit: 'hours' } :
            variant === 'health' ? { title: 'Maintain 90% Sleep Score', target: '90%', current: '85%', unit: 'score' } : {}
    ]); // Initial mock goal
    // If we want empty state to show first for demo: setMockGoals([]) and let user add?
    // User requested "in all three there should be a goals section". 
    // I'll leave one mock goal so it looks populated, or empty one if we want consistency.
    // The finance one uses empty state if length is 0.
    // Let's toggle mockGoals to [] if we want to show the "Add Goal" empty state first.
    // But for "Time" and "Health" better to show what it looks like? 
    // I'll initialize with ONE mock goal so the "Active State" is visible as per the Finance active state example.

    useEffect(() => {
        if (variant === 'finance') loadFinanceGoals();
        else {
            // Reset mock goals based on variant
            if (variant === 'time') setMockGoals([{ title: 'Deep Work: 20h/week', target: 20, current: 12, unit: 'h' }]);
            if (variant === 'health') setMockGoals([{ title: 'Sleep 8h nightly', target: 8, current: 6.5, unit: 'h' }]);
        }
    }, [variant]);

    const loadFinanceGoals = async () => {
        const data = await getFinancialGoals();
        setFinanceGoals(data);
    };

    const handleFinanceCreate = async () => {
        try {
            await createGoal({ ...newFinanceGoal, type: 'custom', priority: 'medium' });
            setShowAdd(false);
            setNewFinanceGoal({ title: '', target_amount: 0, target_date: '', monthly_contribution_target: 0 });
            loadFinanceGoals();
        } catch (e) { console.error(e); }
    };

    const handleMockCreate = () => {
        // Just mock adding it
        setMockGoals([...mockGoals, { title: 'New Goal', target: 100, current: 0, unit: 'units' }]);
        setShowAdd(false);
    };

    // --- RENDER HELPERS ---

    const getEmptyCopy = () => {
        switch (variant) {
            case 'time': return { title: 'Master your time', text: 'Set clear focus goals to reclaim your schedule.' };
            case 'health': return { title: 'Optimize your bio-engine', text: 'Track specific health targets to boost longevity.' };
            default: return { title: 'Your goals give your numbers meaning', text: 'People with a clear financial goal save up to 2× more consistently.' };
        }
    };

    const copy = getEmptyCopy();
    const activeGoals = variant === 'finance' ? financeGoals : mockGoals;

    // --- A) EMPTY STATE ---
    if (activeGoals.length === 0 && !showAdd) {
        return (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-8 text-center relative overflow-hidden">
                <div className="relative z-10 flex flex-col items-center">
                    <div className="w-12 h-12 rounded-full bg-blue-500/10 flex items-center justify-center mb-4">
                        <Target className="w-6 h-6 text-blue-400" />
                    </div>
                    <h2 className="text-xl font-semibold text-white mb-2">{copy.title}</h2>
                    <p className="text-gray-400 max-w-md mx-auto mb-6 text-sm">{copy.text}</p>
                    <div className="flex flex-col gap-3 w-full max-w-xs">
                        <button
                            onClick={() => setShowAdd(true)}
                            style={{
                                padding: '12px 24px',
                                backgroundColor: 'var(--color-accent-blue)',
                                color: 'white',
                                borderRadius: 'var(--radius-md)',
                                border: 'none',
                                fontWeight: 500,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                                cursor: 'pointer',
                                alignSelf: 'center'
                            }}
                        >
                            Add Goal <ArrowRight size={16} />
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // --- B) ACTIVE STATE ---
    if (!showAdd && activeGoals.length > 0) {
        // Finance Active
        if (variant === 'finance') {
            const primaryGoal = financeGoals[0];
            const targetAmount = primaryGoal?.target_amount || 0;
            const monthlyNeed = primaryGoal?.monthly_contribution_target || (targetAmount / 12);
            const currentCapacity = monthlyNeed * 0.6;

            return (
                <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                            <span className="text-xl">🎯</span>
                            <h3 className="font-semibold text-white">Goal: {primaryGoal.title}</h3>
                        </div>
                        <div className="flex flex-col gap-1 text-sm text-gray-400">
                            <div className="flex items-center gap-2">
                                <span>Need: <span className="text-white font-medium">${monthlyNeed.toLocaleString()}/mo</span></span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span>Capacity: <span className="text-white font-medium">${currentCapacity.toLocaleString()}/mo</span></span>
                            </div>
                        </div>
                    </div>
                    <div className="w-full md:w-auto p-4 bg-gray-800/50 rounded-lg border border-gray-700/50">
                        <DashboardCTA label="Unlock cashflow trends" targetTab="financial" targetAnchor="connections" variant="ghost" />
                    </div>
                </div>
            );
        }

        // Time/Health Active (Mock)
        const primary = activeGoals[0];
        return (
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                        <span className="text-xl">🎯</span>
                        <h3 className="font-semibold text-white">Goal: {primary.title}</h3>
                    </div>
                    <div className="flex flex-col gap-1 text-sm text-gray-400">
                        <div className="flex items-center gap-2">
                            <span>Target: <span className="text-white font-medium">{primary.target}{primary.unit}</span></span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span>Current: <span className="text-white font-medium">{primary.current}{primary.unit}</span></span>
                        </div>
                    </div>
                </div>
                <div className="w-full md:w-auto p-4 bg-gray-800/50 rounded-lg border border-gray-700/50">
                    <DashboardCTA label="View Details" targetTab={variant === 'time' ? 'time' : 'health'} targetAnchor="goals" variant="ghost" />
                </div>
            </div>
        );
    }

    // --- ADD FORM ---
    return (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-8">
            <h3 className="text-lg font-semibold text-white mb-4">Set a {variant === 'finance' ? 'Financial' : variant === 'time' ? 'Time' : 'Health'} Goal</h3>
            <div className="space-y-4 max-w-md">
                {variant === 'finance' ? (
                    <>
                        <input type="text" placeholder="Goal Name" className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg p-3" value={newFinanceGoal.title} onChange={e => setNewFinanceGoal({ ...newFinanceGoal, title: e.target.value })} />
                        <div className="flex gap-4">
                            <input type="number" placeholder="Target Amount" className="flex-1 bg-gray-800 border border-gray-700 text-white rounded-lg p-3" value={newFinanceGoal.target_amount || ''} onChange={e => setNewFinanceGoal({ ...newFinanceGoal, target_amount: parseFloat(e.target.value) })} />
                            <input type="number" placeholder="Monthly Target" className="flex-1 bg-gray-800 border border-gray-700 text-white rounded-lg p-3" value={newFinanceGoal.monthly_contribution_target || ''} onChange={e => setNewFinanceGoal({ ...newFinanceGoal, monthly_contribution_target: parseFloat(e.target.value) })} />
                        </div>
                    </>
                ) : (
                    <>
                        <input type="text" placeholder="Goal Name" className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg p-3" />
                        <div className="flex gap-4">
                            <input type="text" placeholder="Target" className="flex-1 bg-gray-800 border border-gray-700 text-white rounded-lg p-3" />
                            <input type="text" placeholder="Current" className="flex-1 bg-gray-800 border border-gray-700 text-white rounded-lg p-3" />
                        </div>
                    </>
                )}

                <div className="flex gap-3 pt-2">
                    <button onClick={variant === 'finance' ? handleFinanceCreate : handleMockCreate} className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-500 transition-colors">Save Goal</button>
                    <button onClick={() => setShowAdd(false)} className="px-6 py-2 bg-gray-800 text-gray-300 rounded-lg font-medium hover:bg-gray-700 transition-colors">Cancel</button>
                </div>
            </div>
        </div>
    );
};

export default GoalsSection;


