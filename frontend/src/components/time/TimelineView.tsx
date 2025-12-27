import React, { useEffect, useState } from 'react';
import { Stack, Text, IStackStyles, Spinner, SpinnerSize } from '@fluentui/react';
import { getTimeEvents } from '../../api/api';

const containerStyles: IStackStyles = {
    root: {
        background: 'var(--bg-surface)',
        borderRadius: '12px',
        padding: '20px',
        border: '1px solid var(--border-color)',
    },
};

const eventStyles: IStackStyles = {
    root: {
        padding: '12px',
        borderLeft: '4px solid var(--color-accent-blue)',
        background: 'var(--bg-secondary)',
        borderRadius: '0 8px 8px 0',
        marginBottom: '10px',
    },
};

interface Event {
    id: string;
    title: string;
    start_time: string;
    event_type: string;
}

export const TimelineView: React.FC = () => {
    const [events, setEvents] = useState<Event[]>([]);
    const [loading, setLoading] = useState<boolean>(true);

    useEffect(() => {
        const fetchEvents = async () => {
            try {
                const data = await getTimeEvents();
                setEvents(data);
            } catch (error) {
                console.error("Error loading events", error);
            } finally {
                setLoading(false);
            }
        };
        fetchEvents();
    }, []);

    if (loading) {
        return (
            <Stack styles={containerStyles} horizontalAlign="center" verticalAlign="center" style={{ minHeight: '200px' }}>
                <Spinner size={SpinnerSize.large} label="Loading schedule..." />
            </Stack>
        );
    }

    return (
        <Stack styles={containerStyles}>
            <Text variant="xLarge" style={{ marginBottom: '15px', color: 'var(--text-primary)', fontWeight: 600 }}>Today's Schedule</Text>
            <Stack>
                {events.length > 0 ? (
                    events.map((event) => (
                        <Stack key={event.id} styles={eventStyles}>
                            <Text variant="medium" style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{event.title}</Text>
                            <Text variant="small" style={{ color: 'var(--text-secondary)' }}>
                                {new Date(event.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {event.event_type}
                            </Text>
                        </Stack>
                    ))
                ) : (
                    <Text style={{ color: 'var(--text-secondary)' }}>No events scheduled for today.</Text>
                )}
            </Stack>
        </Stack>
    );
};
