import React from 'react';
import { Stack, Text, PrimaryButton, DefaultButton, TextField, IStackStyles, Icon } from '@fluentui/react';

const sectionStyles: IStackStyles = {
    root: {
        background: 'white',
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        marginTop: '20px',
    },
};

export const ConnectHealth: React.FC = () => {
    return (
        <Stack styles={sectionStyles} tokens={{ childrenGap: 10 }}>
            <Text variant="large" style={{ fontWeight: 600 }}>Connect Health Providers</Text>
            <Text variant="small">Sync your wearable data for deeper insights.</Text>
            <Stack horizontal tokens={{ childrenGap: 10 }}>
                <PrimaryButton text="Connect Whoop" />
                <DefaultButton text="Connect Apple Health" />
            </Stack>
        </Stack>
    );
};

export const LogWorkout: React.FC = () => {
    return (
        <Stack styles={sectionStyles} tokens={{ childrenGap: 10 }}>
            <Text variant="large" style={{ fontWeight: 600 }}>Log Workout</Text>
            <Stack tokens={{ childrenGap: 10 }}>
                <TextField label="Activity Type" placeholder="e.g., Running, Lifting" />
                <Stack horizontal tokens={{ childrenGap: 10 }}>
                    <TextField label="Duration (min)" type="number" />
                    <TextField label="Calories" type="number" />
                </Stack>
                <PrimaryButton text="Save Workout" />
            </Stack>
        </Stack>
    );
};

export const LogMeal: React.FC = () => {
    return (
        <Stack styles={sectionStyles} tokens={{ childrenGap: 10 }}>
            <Text variant="large" style={{ fontWeight: 600 }}>Log Meal</Text>
            <Stack tokens={{ childrenGap: 10 }}>
                <TextField label="Meal Name" placeholder="e.g., Oatmeal" />
                <Stack horizontal tokens={{ childrenGap: 10 }}>
                    <TextField label="Calories" type="number" />
                    <TextField label="Protein (g)" type="number" />
                </Stack>
                <PrimaryButton text="Save Meal" />
            </Stack>
        </Stack>
    );
};
