import React, { useState } from 'react';
import { TimelineView } from '../../components/time/TimelineView';
import { TimePillarCard } from '../../components/time/TimePillarCard';
import { TIME_PILLARS } from '../../constants/timeConstants';
import { SignalType } from '../../components/time/DirectionalSignal';
import DashboardCTA from '../../components/common/DashboardCTA';

import { Clock } from 'lucide-react';
import { UnifiedDashboardLayout } from '../../components/layout/UnifiedDashboardLayout';
import { DashboardHero } from '../../components/dashboard/DashboardHero';
import { getFinancialScore } from '../../api/financialApi';

const TimeDashboard: React.FC = () => {
    const [scoreData, setScoreData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    const isLearningMode = false; // Forced false to show data
    const mockCoverageDays = 20; // Forced high to unlock cards

    React.useEffect(() => {
        const loadData = async () => {
            try {
                const [sData] = await Promise.all([
                    getFinancialScore('month')
                ]);
                setScoreData(sData);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, []);

    // State for pillars
    const [pillars, setPillars] = useState<any[]>([]);

    React.useEffect(() => {
        const loadData = async () => {
            try {
                const [sData] = await Promise.all([
                    getFinancialScore('month')
                ]);
                setScoreData(sData);

                // Fetch real Time Score Breakdown
                // Assuming getFinancialScore returns the unified score response which includes time data, 
                // OR we need to call getTimeScore separately. 
                // Let's rely on the breakdown from the unified score response first for consistency across dashboards.
                if (sData?.breakdown?.productivity?.subscores) {
                    const subscores = sData.breakdown.productivity.subscores;
                    const mapPillar = (key: string, dataKey: string) => {
                        const score = subscores[dataKey] !== undefined ? Math.round(subscores[dataKey]) : 0;
                        const p = TIME_PILLARS[key];
                        return {
                            ...p,
                            score: score,
                            coverageDays: 20, // Default unlocked for now
                            trendData: [65, 68, 70, 72, 68, 75, 78, 80, 82, 85], // Mock trend until API provides it
                            earlySignal: 'Improving' as SignalType
                        };
                    };

                    const realPillars = [
                        mapPillar('SCHEDULE_COVERAGE', 'schedule_coverage'),
                        mapPillar('PLANNING_HABIT', 'planning_habit'),
                        mapPillar('FOCUS_BLOCKS', 'focus_blocks'),
                        mapPillar('MEETING_LOAD', 'meeting_load'),
                        mapPillar('CONTEXT_SWITCHING', 'context_switching'),
                        mapPillar('WEEKLY_RHYTHM', 'weekly_rhythm'),
                        mapPillar('TIME_ALIGNMENT', 'time_alignment')
                    ];
                    setPillars(realPillars);
                } else if (sData?.breakdown?.productivity?.dimensions) {
                    // Legacy fallback
                    const dims = sData.breakdown.productivity.dimensions;
                    const mapPillarLegacy = (key: string, dimKey: string) => {
                        const d = dims[dimKey] || { score: 0, max: 25 };
                        const normalizedScore = d.max ? Math.round((d.score / d.max) * 100) : 0;
                        const p = TIME_PILLARS[key];
                        return { ...p, score: normalizedScore, coverageDays: 20, trendData: [], earlySignal: 'Neutral' as SignalType };
                    };
                    const realPillars = [
                        mapPillarLegacy('SCHEDULE_COVERAGE', 'structure'),
                        mapPillarLegacy('PLANNING_HABIT', 'structure'),
                        mapPillarLegacy('FOCUS_BLOCKS', 'focus'),
                        mapPillarLegacy('MEETING_LOAD', 'load'),
                        mapPillarLegacy('CONTEXT_SWITCHING', 'friction'),
                        mapPillarLegacy('WEEKLY_RHYTHM', 'stress')
                    ];
                    setPillars(realPillars);
                } else {
                    // Fallback if data missing
                    const fallbackPillars = [
                        'SCHEDULE_COVERAGE', 'PLANNING_HABIT', 'FOCUS_BLOCKS',
                        'MEETING_LOAD', 'CONTEXT_SWITCHING', 'WEEKLY_RHYTHM'
                    ].map(key => {
                        const pillar = TIME_PILLARS[key];
                        return { ...pillar, score: 0, coverageDays: 0, trendData: [], earlySignal: 'Neutral' };
                    });
                    setPillars(fallbackPillars);
                }

            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        loadData();
    }, []);

    if (loading) return <div className="p-8 text-white">Loading focus data...</div>;

    const productivityScore = scoreData?.productivity_score !== undefined ? Math.round(scoreData.productivity_score) : 0;

    const heroSection = (
        <DashboardHero
            title="Time & Focus"
            icon={<Clock size={24} />}
            color="var(--color-accent-blue)"
            score={productivityScore}
            trend={scoreData?.productivity_trend || 0}
            // goals={goals} // Handled internally
            variant="time"
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
            {/* Connection redirect banner */}
            {pillars.every(p => p.score === 0) && (
                <div style={{
                    padding: '20px',
                    backgroundColor: 'var(--bg-surface)',
                    borderRadius: '12px',
                    border: '1px solid var(--color-accent-blue, #3b82f6)',
                    textAlign: 'center'
                }}>
                    <span style={{ display: 'block', marginBottom: '4px', fontWeight: 600, color: 'var(--text-primary)' }}>
                        No calendar data yet
                    </span>
                    <span style={{ display: 'block', marginBottom: '12px', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
                        Connect Google Calendar to unlock real-time time &amp; focus insights.
                    </span>
                    <DashboardCTA
                        label="Connect Google Calendar"
                        targetTab="time"
                        targetAnchor="connections-time"
                        variant="primary"
                        fullWidth
                    />
                </div>
            )}


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
