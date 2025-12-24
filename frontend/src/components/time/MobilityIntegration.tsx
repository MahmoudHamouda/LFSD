import React from 'react';
import { Stack, Text, IStackStyles, Icon } from '@fluentui/react';

const containerStyles: IStackStyles = {
    root: {
        background: 'white',
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        marginTop: '20px',
    },
};

const rideStyles: IStackStyles = {
    root: {
        padding: '10px',
        border: '1px solid #e0e0e0',
        borderRadius: '4px',
        marginBottom: '10px',
    },
};

interface Ride {
    id: string;
    provider: 'Uber' | 'Lyft';
    pickupTime: string;
    destination: string;
    status: 'scheduled' | 'arriving';
}

const mockRides: Ride[] = [
    { id: '1', provider: 'Uber', pickupTime: '05:30 PM', destination: 'Gym', status: 'scheduled' },
];

export const MobilityIntegration: React.FC = () => {
    return (
        <Stack styles={containerStyles}>
            <Stack horizontal horizontalAlign="space-between" verticalAlign="center" style={{ marginBottom: '15px' }}>
                <Text variant="xLarge">Upcoming Rides</Text>
                <Icon iconName="Car" style={{ fontSize: '20px' }} />
            </Stack>

            {mockRides.length > 0 ? (
                <Stack>
                    {mockRides.map((ride) => (
                        <Stack key={ride.id} styles={rideStyles} horizontal horizontalAlign="space-between" verticalAlign="center">
                            <Stack>
                                <Text variant="medium" style={{ fontWeight: 600 }}>{ride.destination}</Text>
                                <Text variant="small" style={{ color: '#666' }}>{ride.provider} • {ride.pickupTime}</Text>
                            </Stack>
                            <Text variant="small" style={{ color: ride.status === 'arriving' ? 'green' : 'orange', fontWeight: 600 }}>
                                {ride.status.toUpperCase()}
                            </Text>
                        </Stack>
                    ))}
                </Stack>
            ) : (
                <Text>No upcoming rides scheduled.</Text>
            )}
        </Stack>
    );
};
