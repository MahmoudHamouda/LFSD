import React, { useEffect, useState } from 'react';
import { Stack, Text, IStackStyles, Spinner, SpinnerSize } from '@fluentui/react';
import { getHealthDailySummaries, getRecentSleepSessions, getRecoveryScore } from '../../api/healthApi';
import { HealthDailySummary, SleepSession } from '../../types/health';
// import { ConnectHealth, LogWorkout, LogMeal } from '../../components/health/DataIngestion'; // Removed inline forms
import HealthPillarCard from '../../components/health/HealthPillarCard';
import DashboardCTA from '../../components/common/DashboardCTA';
import TrendPanel from '../../components/common/TrendPanel';
import { SummaryIndexBar } from '../../components/indexes';
import { Heart } from 'lucide-react';
import GoalsSection from '../../components/dashboard/GoalsSection';
import HealthHighlightsWidget from '../../components/health/HealthHighlightsWidget';

const containerStyles: IStackStyles = {
    root: {
        height: '100%',
        width: '100%',
        padding: '24px',
        boxSizing: 'border-box',
        overflowY: 'auto',
        backgroundColor: '#f8f9fa',
    },
};

const HealthDashboard: React.FC = () => {
    const [summary, setSummary] = useState<HealthDailySummary | null>(null);
    const [sleepSessions, setSleepSessions] = useState<SleepSession[]>([]);
    const [recoveryScore, setRecoveryScore] = useState<number>(0);
    const [loading, setLoading] = useState(true);
    const [selectedPillar, setSelectedPillar] = useState<any | null>(null);

    useEffect(() => {
        const loadData = async () => {
            try {
                const [summaries, sleep, recovery] = await Promise.all([
                    getHealthDailySummaries(),
                    getRecentSleepSessions(),
                    getRecoveryScore()
                ]);

                if (summaries.length > 0) {
                    setSummary(summaries[0]);
                }
                setSleepSessions(sleep);
                setRecoveryScore(recovery.score || 0);
            } catch (error) {
                console.error("Failed to load health data", error);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, []);

    if (loading) {
        return (
            <Stack styles={containerStyles} horizontalAlign="center" verticalAlign="center">
                <Spinner size={SpinnerSize.large} label="Loading Health Insights..." />
            </Stack>
        );
    }

    // --- Helper Models ---

    // REQUIRED_DAYS for Stable state default
    const REQUIRED_DAYS = 7;

    // Risk thresholds (examples)
    const THRESHOLDS = {
        sleep: 70, // Score < 70 is risk
        recovery: 33, // WHOOP style red recovery
        activity: 50, // Arbitrary low activity score
        nutrition: 50,
        consistency: 60,
        strain: 80 // Maybe high strain is risk? Or low? Context dependent. Let's say < 40 recovery is risk.
    };

    // Calculate "Consistency" based on available data (Mock logic)
    // If we have summary data, we assume at least 1 day.
    // Real app would calculate coverage over last 30 days.
    const coverageMap = {
        sleep: summary ? 5 : 0, // Mock: 5 days collected
        recovery: summary?.hrvAverage ? 4 : 0,
        activity: summary?.stepsCount ? 7 : 0, // Mock: 7 days (Stable)
        nutrition: 2, // Mock: Learning
        consistency: 7, // Mock: Stable
        strain: 1 // Mock: Learning
    };

    // Mock trend data generator
    const getTrend = () => [65, 68, 70, 72, 75, 78, 80, 82, 85, 83, 85, 88, 90, 89, 92];

    // --- 1. Sleep Performance ---
    const sleepPillar = {
        title: "Sleep Performance",
        score: summary ? summary.sleepQualityScore : null,
        coverageDays: coverageMap.sleep,
        requiredDays: REQUIRED_DAYS,
        riskThreshold: THRESHOLDS.sleep,
        trendDirection: 'improving' as const,
        trendData: getTrend()
    };

    // --- 2. Recovery ---
    const recoveryPillar = {
        title: "Recovery",
        score: recoveryScore,
        coverageDays: coverageMap.recovery,
        requiredDays: REQUIRED_DAYS,
        riskThreshold: THRESHOLDS.recovery,
        // Calculate basic trend
        trendDirection: (summary?.hrvAverage || 0) > 40 ? 'stable' as const : 'declining' as const,
        trendData: [40, 42, 45, 43, 48, 50, 52, 49, 55]
    };

    // --- 3. Activity Load ---
    // Map steps to a 0-100 score for consistency in the UI
    const activityScore = summary ? Math.min((summary.stepsCount / 10000) * 100, 100) : null;
    const activityPillar = {
        title: "Activity Load",
        score: activityScore,
        coverageDays: coverageMap.activity,
        requiredDays: REQUIRED_DAYS,
        riskThreshold: THRESHOLDS.activity,
        trendDirection: 'improving' as const,
        trendData: getTrend()
    };

    // --- 4. Nutrition Balance ---
    // Fully Mocked for now
    const nutritionPillar = {
        title: "Nutrition Balance",
        score: null, // No score yet
        coverageDays: coverageMap.nutrition,
        requiredDays: REQUIRED_DAYS,
        riskThreshold: THRESHOLDS.nutrition,
        trendDirection: 'unknown' as const,
        trendData: []
    };

    // --- 5. Consistency ---
    // Mocked
    const consistencyPillar = {
        title: "Consistency",
        score: 85, // Good consistency
        coverageDays: coverageMap.consistency,
        requiredDays: REQUIRED_DAYS,
        riskThreshold: THRESHOLDS.consistency,
        trendDirection: 'stable' as const,
        trendData: [85, 85, 85, 85, 85, 88, 85]
    };

    // --- 6. Strain vs Recovery ---
    // Mocked / Advanced Unlock
    const strainPillar = {
        title: "Strain vs Recovery",
        score: null,
        coverageDays: coverageMap.strain,
        requiredDays: 14, // Harder to unlock
        riskThreshold: THRESHOLDS.strain,
        trendDirection: 'unknown' as const,
        trendData: []
    };

    const pillars = [
        sleepPillar,
        recoveryPillar,
        activityPillar,
        nutritionPillar,
        consistencyPillar,
        strainPillar
    ];

    return (
        <Stack styles={containerStyles} tokens={{ childrenGap: 24 }}>


            <Stack tokens={{ childrenGap: 16 }}>
                <Stack>
                    <Text variant="xxLarge" styles={{ root: { fontWeight: 700, color: '#111827' } }}>Deep Health</Text>
                    <Text variant="medium" styles={{ root: { color: '#6b7280' } }}>
                        Optimize your biological baseline. The system learns your patterns over time.
                    </Text>
                </Stack>

                <SummaryIndexBar
                    indexes={[{
                        id: 'health',
                        label: 'Health & Recovery Score',
                        value: summary?.health_score || 0,
                        trend: summary?.health_trend || 0,
                        variant: 'primary',
                        icon: <div style={{ padding: '8px', background: 'rgba(255,255,255,0.2)', borderRadius: '8px', display: 'flex' }}><Heart size={24} color="white" /></div>
                    }]}
                />
            </Stack>

            {/* Main Content - Split Layout */}
            <Stack horizontal tokens={{ childrenGap: 32 }} styles={{ root: { flexWrap: 'wrap', alignItems: 'flex-start' } }}>

                {/* LEFT COLUMN: Highlights (Operational) */}
                <Stack.Item grow={1} styles={{ root: { minWidth: '350px', maxWidth: '400px' } }}>
                    <HealthHighlightsWidget summary={summary} />
                </Stack.Item>

                {/* RIGHT COLUMN: Goals & Pillars (Analytical) */}
                <Stack.Item grow={3} styles={{ root: { minWidth: '600px', width: '100%' } }}>
                    <Stack tokens={{ childrenGap: 24 }}>
                        <GoalsSection variant="health" />

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
                    </Stack>
                </Stack.Item>
            </Stack>

            {/* Trend Panel Overlay */}
            {selectedPillar && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    backgroundColor: 'rgba(0,0,0,0.7)', zIndex: 1000,
                    display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '16px'
                }} onClick={() => setSelectedPillar(null)}>
                    <div style={{ width: '90%', maxWidth: '600px' }} onClick={e => e.stopPropagation()}>
                        <TrendPanel
                            title={selectedPillar.title}
                            data={
                                // Map trendData to date/value format if needed by TrendPanel, or TrendPanel handles it.
                                // TrendPanel expects { date: string, value: number }[]
                                (selectedPillar.trendData || []).map((val: number, i: number) => ({ date: `Day ${i + 1}`, value: val }))
                            }
                            onClose={() => setSelectedPillar(null)}
                        />
                    </div>
                </div>
            )}
        </Stack>
    );
};

export default HealthDashboard;
