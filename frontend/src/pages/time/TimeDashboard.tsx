import React, { useState } from 'react';
import { TimelineView } from '../../components/time/TimelineView';
import { TimePillarCard } from '../../components/time/TimePillarCard';
import { TIME_PILLARS } from '../../constants/timeConstants';
import { SignalType } from '../../components/time/DirectionalSignal';
import DashboardCTA from '../../components/common/DashboardCTA';

import { Clock } from 'lucide-react';
import { UnifiedDashboardLayout } from '../../components/layout/UnifiedDashboardLayout';
import { DashboardHero } from '../../components/dashboard/DashboardHero';
import { getFinancialScore, getFinancialGoals } from '../../api/financialApi';

const TimeDashboard: React.FC = () => {
    const [scoreData, setScoreData] = useState<any>(null);
    const [goals, setGoals] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const isLearningMode = false;
    const mockCoverageDays = 20;

    React.useEffect(() => {
        const loadData = async () => {
            try {
                const [sData, gData] = await Promise.all([
                    getFinancialScore('month'),
                    getFinancialGoals('time')
                ]);
                setScoreData(sData);
                setGoals(gData);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, []);

    // Helper to generate mock pillar data
    const getPillarData = (key: string) => {
        const pillar = TIME_PILLARS[key];
        const score = isLearningMode ? null : Math.floor(Math.random() * 40) + 60;
        const trendData = [65, 68, 70, 72, 68, 75, 78, 80, 82, 85];
        const earlySignal: SignalType = 'Improving';

        return {
            ...pillar,
            score,
            coverageDays: mockCoverageDays,
            trendData: isLearningMode ? [] : trendData,
            earlySignal
        };
    };

    const pillars = [
        'SCHEDULE_COVERAGE',
        'PLANNING_HABIT',
        'FOCUS_BLOCKS',
        'MEETING_LOAD',
        'CONTEXT_SWITCHING',
        'WEEKLY_RHYTHM'
    ].map(key => getPillarData(key));

    if (loading) return <div className="p-8 text-white">Loading focus data...</div>;

    const productivityScore = scoreData?.productivity_score !== undefined ? Math.round(scoreData.productivity_score) : 0;

    const heroSection = (
        <DashboardHero
            title="Time & Focus"
            icon={<Clock size={24} />}
            color="var(--color-accent-blue)"
            score={productivityScore}
            trend={scoreData?.productivity_trend || 0}
            goals={goals}
            variant="time"
            onAddGoal={() => {
                window.location.href = '/profile?tab=time&anchor=goals';
            }}
        />
    );

    const leftColumn = (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <TimelineView />
            {/* Ingestion Actions */}
            <div style={{
                padding: '20px',
                backgroundColor: 'var(--bg-surface)',
                borderRadius: '12px',
                border: '1px solid var(--border-color)',
                textAlign: 'center'
            }}>
                <span style={{ display: 'block', marginBottom: '12px', color: 'var(--text-secondary)' }}>
                    Manage your schedule & sources
                </span>
                <DashboardCTA
                    label="Manage Calendar Connections"
                    targetTab="time"
                    targetAnchor="connections-time"
                    variant="secondary"
                    fullWidth
                />
            </div>
        </div>
    );

    const rightColumn = (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>


            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
                gap: '24px'
            }}>
                {pillars.map((p) => (
                    <TimePillarCard
                        key={p.key}
                        title={p.title}
                        score={p.score}
                        coverageDays={p.coverageDays}
                        requiredDays={p.requiredDays}
                        riskThreshold={p.riskThreshold}
                        trendData={p.trendData}
                        earlySignal={p.earlySignal}
                        onClick={() => {
                            // Navigation logic...
                            if (p.coverageDays < p.requiredDays) {
                                window.location.href = `/profile?tab=time&anchor=connections-time`;
                            }
                        }}
                    />
                ))}
            </div>
        </div>
    );

    return (
        <UnifiedDashboardLayout
            hero={heroSection}
            indicators={leftColumn}
            pillars={rightColumn}
        />
    );
};

export default TimeDashboard;
