import React, { useEffect, useState } from 'react';

import { getHealthDailySummaries, getRecentSleepSessions, getRecoveryScore } from '../../api/healthApi';
import { HealthDailySummary, SleepSession } from '../../types/health';
import HealthPillarCard from '../../components/health/HealthPillarCard';
import TrendPanel from '../../components/common/TrendPanel';
import { Heart } from 'lucide-react';

import HealthHighlightsWidget from '../../components/health/HealthHighlightsWidget';
import { UnifiedDashboardLayout } from '../../components/layout/UnifiedDashboardLayout';
import { DashboardHero } from '../../components/dashboard/DashboardHero';
import { getFinancialScore, getFinancialGoals } from '../../api/financialApi';

const HealthDashboard: React.FC = () => {
    const [summary, setSummary] = useState<HealthDailySummary | null>(null);
    const [sleepSessions, setSleepSessions] = useState<SleepSession[]>([]);
    const [recoveryScore, setRecoveryScore] = useState<number>(0);
    const [loading, setLoading] = useState(true);
    const [selectedPillar, setSelectedPillar] = useState<any | null>(null);
    const [scoreData, setScoreData] = useState<any>(null);
    const [goals, setGoals] = useState<any[]>([]);

    useEffect(() => {
        const loadData = async () => {
            try {
                const [summaries, sleep, recovery, sData, gData] = await Promise.all([
                    getHealthDailySummaries(),
                    getRecentSleepSessions(),
                    getRecoveryScore(),
                    getFinancialScore('month'),
                    getFinancialGoals('health')
                ]);

                if (summaries.length > 0) {
                    setSummary(summaries[0]);
                }
                setSleepSessions(sleep);
                setRecoveryScore(recovery.score || 0);
                setScoreData(sData);
                setGoals(gData);
            } catch (error) {
                console.error("Failed to load health data", error);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, []);

    if (loading) {
        return <div className="p-8 text-white">Loading health insights...</div>;
    }

    // --- Helper Models ---
    const REQUIRED_DAYS = 7;
    const THRESHOLDS = {
        sleep: 70,
        recovery: 33,
        activity: 50,
        nutrition: 50,
        consistency: 60,
        strain: 80
    };

    const coverageMap = {
        sleep: summary ? 5 : 0,
        recovery: summary?.hrvAverage ? 4 : 0,
        activity: summary?.stepsCount ? 7 : 0,
        nutrition: 2,
        consistency: 7,
        strain: 1
    };

    const getTrend = () => [65, 68, 70, 72, 75, 78, 80, 82, 85, 83, 85, 88, 90, 89, 92];

    const pillars = [
        {
            title: "Sleep Performance",
            score: summary ? summary.sleepQualityScore : null,
            coverageDays: coverageMap.sleep,
            requiredDays: REQUIRED_DAYS,
            riskThreshold: THRESHOLDS.sleep,
            trendDirection: 'improving' as const,
            trendData: getTrend()
        },
        {
            title: "Recovery",
            score: recoveryScore,
            coverageDays: coverageMap.recovery,
            requiredDays: REQUIRED_DAYS,
            riskThreshold: THRESHOLDS.recovery,
            trendDirection: (summary?.hrvAverage || 0) > 40 ? 'stable' as const : 'declining' as const,
            trendData: [40, 42, 45, 43, 48, 50, 52, 49, 55]
        },
        {
            title: "Activity Load",
            score: summary ? Math.min((summary.stepsCount / 10000) * 100, 100) : null,
            coverageDays: coverageMap.activity,
            requiredDays: REQUIRED_DAYS,
            riskThreshold: THRESHOLDS.activity,
            trendDirection: 'improving' as const,
            trendData: getTrend()
        },
        {
            title: "Nutrition Balance",
            score: null,
            coverageDays: coverageMap.nutrition,
            requiredDays: REQUIRED_DAYS,
            riskThreshold: THRESHOLDS.nutrition,
            trendDirection: 'unknown' as const,
            trendData: []
        },
        {
            title: "Consistency",
            score: 85,
            coverageDays: coverageMap.consistency,
            requiredDays: REQUIRED_DAYS,
            riskThreshold: THRESHOLDS.consistency,
            trendDirection: 'stable' as const,
            trendData: [85, 85, 85, 85, 85, 88, 85]
        },
        {
            title: "Strain vs Recovery",
            score: null,
            coverageDays: coverageMap.strain,
            requiredDays: 14,
            riskThreshold: THRESHOLDS.strain,
            trendDirection: 'unknown' as const,
            trendData: []
        }
    ];

    const healthScore = scoreData?.health_score !== undefined ? Math.round(scoreData.health_score) : (summary?.health_score || 0);

    const heroSection = (
        <DashboardHero
            title="Health & Recovery"
            icon={<Heart size={24} />}
            color="var(--color-accent-red)"
            score={healthScore}
            trend={scoreData?.health_trend || 0}
            goals={goals}
            variant="health"
            onAddGoal={() => {
                window.location.href = '/profile?tab=health&anchor=goals';
            }}
        />
    );

    const rightColumn = (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>


            <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                gap: '20px'
            }}>
                {pillars.map((p, idx) => (
                    <HealthPillarCard
                        key={idx}
                        title={p.title}
                        score={p.score}
                        coverageDays={p.coverageDays}
                        requiredDays={p.requiredDays}
                        riskThreshold={p.riskThreshold}
                        trendDirection={p.trendDirection}
                        trendData={p.trendData}
                        onClick={() => {
                            if (p.coverageDays >= p.requiredDays) {
                                setSelectedPillar(p);
                            } else {
                                window.location.href = `/profile?tab=health&anchor=connections-health`;
                            }
                        }}
                    />
                ))}
            </div>
        </div>
    );

    return (
        <div style={{ height: '100%' }}>
            <UnifiedDashboardLayout
                hero={heroSection}
                indicators={<HealthHighlightsWidget summary={summary} />}
                pillars={rightColumn}
            />

            {selectedPillar && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    backgroundColor: 'rgba(0,0,0,0.7)', zIndex: 1000,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px'
                }} onClick={() => setSelectedPillar(null)}>
                    <div style={{ width: '90%', maxWidth: '600px' }} onClick={e => e.stopPropagation()}>
                        <TrendPanel
                            title={selectedPillar.title}
                            data={(selectedPillar.trendData || []).map((val: number, i: number) => ({ date: `Day ${i + 1}`, value: val }))}
                            onClose={() => setSelectedPillar(null)}
                        />
                    </div>
                </div>
            )}
        </div>
    );
};

export default HealthDashboard;
