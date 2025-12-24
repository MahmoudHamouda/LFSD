
export interface TimePillarConfig {
    key: string;
    title: string;
    description: string;
    requiredDays: number;
    riskThreshold: number; // Score below this is AT_RISK (if coverage met)
}

export const TIME_PILLARS: Record<string, TimePillarConfig> = {
    SCHEDULE_COVERAGE: {
        key: 'schedule_coverage',
        title: 'Schedule Coverage',
        description: 'Consistency of calendar data usage.',
        requiredDays: 14,
        riskThreshold: 50,
    },
    PLANNING_HABIT: {
        key: 'planning_habit',
        title: 'Planning Habit',
        description: 'Frequency of planning sessions.',
        requiredDays: 14,
        riskThreshold: 60,
    },
    FOCUS_BLOCKS: {
        key: 'focus_blocks',
        title: 'Focus Blocks',
        description: 'Dedicated time for deep work.',
        requiredDays: 20, // Slower unlock
        riskThreshold: 30, // Lower threshold might be acceptable depending on role
    },
    MEETING_LOAD: {
        key: 'meeting_load',
        title: 'Meeting Load',
        description: 'Hours spent in meetings vs. makers time.',
        requiredDays: 14,
        riskThreshold: 40, // High meeting load might be risky (inverted logic handled in score calc, here we just check score)
    },
    CONTEXT_SWITCHING: {
        key: 'context_switching',
        title: 'Context Switching',
        description: 'Frequency of task switching.',
        requiredDays: 14,
        riskThreshold: 50,
    },
    PUNCTUALITY_BUFFER: { // Optional/Advanced
        key: 'punctuality_buffer',
        title: 'Punctuality Buffer',
        description: 'Space between meetings.',
        requiredDays: 14,
        riskThreshold: 50,
    },
    WEEKLY_RHYTHM: {
        key: 'weekly_rhythm',
        title: 'Weekly Rhythm',
        description: 'Consistency of week-over-week patterns.',
        requiredDays: 28, // Longest unlock
        riskThreshold: 60,
    },
};
