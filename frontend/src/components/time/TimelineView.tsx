import React, { useEffect, useState } from 'react';
import { Stack, Text, IStackStyles, Spinner, SpinnerSize } from '@fluentui/react';
import { getTimeEvents } from '../../api/api';

const containerStyles: IStackStyles = {
    root: {
        background: 'white',
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    },
};

const eventStyles: IStackStyles = {
    root: {
        padding: '10px',
        borderLeft: '4px solid #0078d4',
        background: '#f3f2f1',
        borderRadius: '0 4px 4px 0',
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
            <Text variant="xLarge" style={{ marginBottom: '15px' }}>Today's Schedule</Text>
            <Stack>
                {events.length > 0 ? (
                    events.map((event) => (
                        <Stack key={event.id} styles={eventStyles}>
                            <Text variant="medium" style={{ fontWeight: 600 }}>{event.title}</Text>
                            <Text variant="small" style={{ color: '#666' }}>
                                {new Date(event.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {event.event_type}
                            </Text>
                        </Stack>
                    ))
                ) : (
                    <Text>No events scheduled for today.</Text>
                )}
            </Stack>
        </Stack>
    );
};
