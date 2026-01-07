import React, { useEffect, useState } from 'react';

import { getHealthDailySummaries, getRecentSleepSessions, getRecoveryScore } from '../../api/healthApi';
import { HealthDailySummary, SleepSession } from '../../types/health';
import HealthPillarCard from '../../components/health/HealthPillarCard';
import TrendPanel from '../../components/common/TrendPanel';
import { Heart } from 'lucide-react';

import HealthHighlightsWidget from '../../components/health/HealthHighlightsWidget';
import { UnifiedDashboardLayout } from '../../components/layout/UnifiedDashboardLayout';
import { DashboardHero } from '../../components/dashboard/DashboardHero';
import { getFinancialScore } from '../../api/financialApi';

const HealthDashboard: React.FC = () => {
    const [summary, setSummary] = useState<HealthDailySummary | null>(null);
    const [sleepSessions, setSleepSessions] = useState<SleepSession[]>([]);
    const [recoveryScore, setRecoveryScore] = useState<number>(0);
    const [loading, setLoading] = useState(true);
    const [selectedPillar, setSelectedPillar] = useState<any | null>(null);
    const [scoreData, setScoreData] = useState<any>(null);

    useEffect(() => {
        const loadData = async () => {
            try {
                const [summaries, sleep, recovery, sData, gData] = await Promise.all([
                    getHealthDailySummaries(),
                    getRecentSleepSessions(),
                    getRecoveryScore(),
                    getFinancialScore('month')
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
        sleep: summary ? 5 : 7, // Default to 7 (unlocked) if summary missing but user logged in
        recovery: summary?.hrvAverage ? 4 : 5,
        activity: summary?.stepsCount ? 7 : 7,
        nutrition: 2,
        consistency: 7,
        strain: 1
    };

    const getTrend = () => [65, 68, 70, 72, 75, 78, 80, 82, 85, 83, 85, 88, 90, 89, 92];

    // Map subscores from API if available
    const subscores = scoreData?.breakdown?.health?.subscores || {};

    // Helper to get score safely
    const getScore = (key: string, heuristic: number | null) => {
        if (subscores[key] !== undefined) return subscores[key];
        return heuristic;
    };

    const pillars = [
        {
            title: "Sleep Performance",
            score: getScore('sleep', summary ? summary.sleepQualityScore : null),
            coverageDays: coverageMap.sleep,
            requiredDays: REQUIRED_DAYS,
            riskThreshold: THRESHOLDS.sleep,
            trendDirection: 'improving' as const,
            trendData: getTrend()
        },
        {
            title: "Recovery",
            score: getScore('recovery', recoveryScore),
            coverageDays: coverageMap.recovery,
            requiredDays: REQUIRED_DAYS,
            riskThreshold: THRESHOLDS.recovery,
            trendDirection: (summary?.hrvAverage || 0) > 40 ? 'stable' as const : 'declining' as const,
            trendData: [40, 42, 45, 43, 48, 50, 52, 49, 55]
        },
        {
            title: "Activity Load",
            score: getScore('activity', summary ? Math.min((summary.stepsCount / 10000) * 100, 100) : null),
            coverageDays: coverageMap.activity,
            requiredDays: REQUIRED_DAYS,
            riskThreshold: THRESHOLDS.activity,
            trendDirection: 'improving' as const,
            trendData: getTrend()
        },
        {
            title: "Nutrition Balance",
            score: getScore('nutrition', null),
            coverageDays: coverageMap.nutrition,
            requiredDays: REQUIRED_DAYS,
            riskThreshold: THRESHOLDS.nutrition,
            trendDirection: 'unknown' as const,
            trendData: []
        },
        {
            title: "Lifestyle & Consistency",
            score: getScore('lifestyle', 85),
            coverageDays: coverageMap.consistency,
            requiredDays: REQUIRED_DAYS,
            riskThreshold: THRESHOLDS.consistency,
            trendDirection: 'stable' as const,
            trendData: [85, 85, 85, 85, 85, 88, 85]
        },
        {
            title: "Strain vs Recovery",
            score: getScore('strain', null),
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
            // goals={goals} // Handled internally
            variant="health"
        />
    );

    const rightColumn = (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', minWidth: 0 }}>


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
