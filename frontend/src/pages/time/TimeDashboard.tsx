import React from 'react';
import { Stack, Text, IStackStyles } from '@fluentui/react';
import { TimelineView } from '../../components/time/TimelineView';
import { ProductivityScore } from '../../components/time/ProductivityScore';
// import { ConnectCalendar, AddEventForm, UploadSchedule } from '../../components/time/DataIngestion'; // Removed inline forms
import { TimePillarCard } from '../../components/time/TimePillarCard';
import { TIME_PILLARS } from '../../constants/timeConstants';
import { SignalType } from '../../components/time/DirectionalSignal';
import DashboardCTA from '../../components/common/DashboardCTA';
import TrendPanel from '../../components/common/TrendPanel';
import { useState } from 'react';
import { SummaryIndexBar } from '../../components/indexes';
import { Clock } from 'lucide-react';
import GoalsSection from '../../components/dashboard/GoalsSection';

const containerStyles: IStackStyles = {
    root: {
        height: '100%',
        width: '100%',
        padding: '32px', // Increased padding for better spacing
        boxSizing: 'border-box',
        overflowY: 'auto',
        backgroundColor: '#FAFAFA', // Very light gray, cleaner than #f8f9fa
    },
};

const TimeDashboard: React.FC = () => {
    // MOCK DATA STATE
    // Toggle this to test different states (Learning vs Stable)
    const isLearningMode = true;

    const mockCoverageDays = isLearningMode ? 5 : 20;

    // Helper to generate mock pillar data
    const getPillarData = (key: string) => {
        const pillar = TIME_PILLARS[key];
        // Mock values
        const score = isLearningMode ? null : Math.floor(Math.random() * 40) + 60; // 60-100 range
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

    return (
        <Stack styles={containerStyles} tokens={{ childrenGap: 32 }}>

            {/* HEADER */}
            <Stack tokens={{ childrenGap: 16 }}>
                <Stack>
                    <Text variant="xxLarge" style={{ fontWeight: 700, color: 'var(--text-primary)' }}>Deep Time</Text>
                    <Text variant="medium" style={{ color: 'var(--text-secondary)' }}>
                        Your rhythm, learned over time. Not just checked off.
                    </Text>
                    <Text variant="small" style={{ color: 'var(--text-tertiary)', marginTop: '4px' }}>
                        🔒 Time trends unlock after ~14–20 days of consistent data.
                    </Text>
                </Stack>

                <SummaryIndexBar
                    indexes={[{
                        id: 'time',
                        label: 'Time & Focus Score',
                        value: isLearningMode ? 0 : 82, // Mocked 82 or 0 if learning
                        trend: 12, // Mocked trend
                        variant: 'secondary',
                        icon: <div style={{ padding: '8px', background: 'rgba(255,255,255,0.2)', borderRadius: '8px', display: 'flex' }}><Clock size={24} color="white" /></div>
                    }]}
                />
            </Stack>

            <Stack horizontal tokens={{ childrenGap: 32 }} styles={{ root: { flexWrap: 'wrap', alignItems: 'stretch' } }}>

                {/* LEFT COLUMN: Timeline & Operational (Operational Layer) */}
                <Stack.Item grow={1} styles={{ root: { minWidth: '350px', maxWidth: '400px' } }}>
                    <Stack tokens={{ childrenGap: 24 }}>
                        <TimelineView />
                        {/* Ingestion Actions - REDIRECT TO PROFILE */}
                        <div style={{
                            padding: '20px',
                            backgroundColor: 'white',
                            borderRadius: '12px',
                            border: '1px solid var(--border-color)',
                            textAlign: 'center'
                        }}>
                            <Text variant="medium" style={{ display: 'block', marginBottom: '12px', color: 'var(--text-secondary)' }}>
                                Manage your schedule & sources
                            </Text>
                            <DashboardCTA
                                label="Manage Calendar Connections"
                                targetTab="time"
                                targetAnchor="connections-time"
                                variant="secondary"
                                fullWidth
                            />
                        </div>
                    </Stack>
                </Stack.Item>

                {/* RIGHT COLUMN: Analytical Layer (Pillars) */}
                <Stack.Item grow={2} styles={{ root: { minWidth: '500px' } }}>
                    <Stack tokens={{ childrenGap: 24 }}>

                        <GoalsSection variant="time" />

                        {/* Pillars Grid */}
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
                                        if (p.coverageDays >= p.requiredDays) {
                                            setSelectedPillar(p);
                                        } else {
                                            window.location.href = `/profile?tab=time&anchor=connections-time`;
                                        }
                                    }}
                                />
                            ))}
                        </div>

                    </Stack>
                </Stack.Item>

            </Stack>
        </Stack>
    );
};

export default TimeDashboard;
