
import React, { useEffect, useState } from 'react';
import { getFinancialScore, getFinancialGoals } from '../../api/financialApi';
import ProgressivePillarCard from '../../components/finance/ProgressivePillarCard';
// import TrendCard from '../../components/dashboard/TrendCard'; // Removed in favor of TrendPanel
import TrendPanel from '../../components/common/TrendPanel';

import { ShieldCheck, Lock } from 'lucide-react';
import styles from './FinanceDashboard.module.css';
import { Wallet } from 'lucide-react';
import RecentTransactionsWidget from '../../components/finance/RecentTransactionsWidget';
import { UnifiedDashboardLayout } from '../../components/layout/UnifiedDashboardLayout';
import { DashboardHero } from '../../components/dashboard/DashboardHero';
import { useNavigate } from 'react-router-dom';

const FinanceDashboard: React.FC = () => {
    const [scoreData, setScoreData] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
    const [goals, setGoals] = useState<any[]>([]);
    const navigate = useNavigate();

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [score, goalsData] = await Promise.all([
                getFinancialScore('month'),
                getFinancialGoals('finance')
            ]);
            setScoreData(score);
            setGoals(goalsData);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div className="p-8 text-white">Loading financial data...</div>;
    }

    const categories = scoreData?.categories || {};

    // Ordered list of pillars to display
    const pillarsList = [
        { id: 'cashflow_stability', title: 'Cashflow Stability', desc: 'Consistency of income vs outflows.' },
        { id: 'bills_coverage', title: 'Bills Coverage', desc: 'Ability to cover fixed costs.' },
        { id: 'discretionary_control', title: 'Discretionary Control', desc: 'Spending on wants vs needs.' },
        { id: 'savings_rate', title: 'Savings Rate', desc: 'Percentage of income saved.' },
        { id: 'emergency_buffer', title: 'Emergency Buffer', desc: 'Liquid assets vs monthly burn.' },
        { id: 'debt_load', title: 'Debt Load', desc: 'Debt payments relative to income.' },
        { id: 'networth_momentum', title: 'Net Worth Momentum', desc: 'Growth of total assets over time.' },
        { id: 'investment_health', title: 'Investment Health', desc: 'Asset allocation and diversity.' },
    ];

    const overallScore = scoreData?.financial_score !== undefined ? Math.round(scoreData.financial_score) : 0;

    const heroSection = (
        <DashboardHero
            title="Financial Health"
            icon={<Wallet size={24} />}
            color="var(--color-accent-green)"
            score={overallScore}
            trend={+2.5}
            goals={goals}
            variant="finance"
            onAddGoal={() => {
                navigate('/profile?tab=financial&anchor=goals');
            }}
        />
    );

    const pillarsSection = (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>


            {/* Core Pillars Grid */}
            <div className={styles.section}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
                    <h2 className={styles.sectionHeader} style={{ margin: 0 }}>
                        <ShieldCheck className={styles.infoIcon} />
                        Core Pillars
                    </h2>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-tertiary)', backgroundColor: 'var(--bg-secondary)', padding: '4px 8px', borderRadius: '6px' }}>
                        <Lock size={10} />
                        <span>Trends unlock after ~20 days of consistent data — this keeps insights accurate.</span>
                    </div>
                </div>

                <div className={styles.grid}>
                    {pillarsList.map(pillar => {
                        const catData = categories[pillar.id] || { score: 0 };
                        const simulatedCoverage = catData.score > 0 ? 30 : 5;
                        const trendData = [65, 68, 66, 70, 72, 71, 75, 78, 80, 82, 81, 85, 88, 87, 90];

                        return (
                            <ProgressivePillarCard
                                key={pillar.id}
                                title={pillar.title}
                                description={pillar.desc}
                                score={catData.score}
                                coverageDays={simulatedCoverage}
                                requiredDays={20}
                                riskThreshold={50}
                                profileLink={`/profile#${pillar.id}`}
                                trendData={trendData}
                                onClick={() => {
                                    if (simulatedCoverage >= 20) {
                                        setSelectedCategory(pillar.id);
                                    } else {
                                        window.location.href = `/profile?tab=financial&anchor=connections`;
                                    }
                                }}
                            />
                        );
                    })}
                </div>
            </div>
        </div>
    );

    return (
        <div className={styles.container}>
            <UnifiedDashboardLayout
                hero={heroSection}
                indicators={<RecentTransactionsWidget />}
                pillars={pillarsSection}
            />

            {/* Trend Panel Overlay */}
            {selectedCategory && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    backgroundColor: 'rgba(0,0,0,0.7)', zIndex: 1000,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', p: 4
                }} onClick={() => setSelectedCategory(null)}>
                    <div style={{ width: '90%', maxWidth: '600px' }} onClick={e => e.stopPropagation()}>
                        <TrendPanel
                            title={pillarsList.find(p => p.id === selectedCategory)?.title || ''}
                            data={[
                                { date: 'Jan 1', value: 65 }, { date: 'Jan 5', value: 68 },
                                { date: 'Jan 10', value: 66 }, { date: 'Jan 15', value: 70 },
                                { date: 'Jan 20', value: 72 }, { date: 'Jan 25', value: 71 },
                                { date: 'Jan 30', value: 75 }, { date: 'Feb 1', value: 78 },
                                { date: 'Feb 5', value: 80 }, { date: 'Feb 10', value: 82 },
                                { date: 'Feb 15', value: 81 }, { date: 'Feb 20', value: 85 },
                                { date: 'Feb 25', value: 88 }, { date: 'Feb 28', value: 87 },
                                { date: 'Mar 1', value: 90 }
                            ]}
                            onClose={() => setSelectedCategory(null)}
                        />
                    </div>
                </div>
            )}
        </div >
    );
};

export default FinanceDashboard;


