import React, { useEffect, useState } from 'react';
import { Stack, Text, IStackStyles, ProgressIndicator, TextField, PrimaryButton, IconButton } from '@fluentui/react';
import { getLifeGoals, createLifeGoal, LifeGoal } from '../../api/lifestyleApi';

const cardStyles: IStackStyles = {
    root: {
        background: 'white',
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        minWidth: '300px',
    },
};

export const GoalSetter: React.FC = () => {
    const [goals, setGoals] = useState<LifeGoal[]>([]);
    const [newGoalTitle, setNewGoalTitle] = useState('');
    const [isAdding, setIsAdding] = useState(false);

    useEffect(() => {
        loadGoals();
    }, []);

    const loadGoals = async () => {
        const data = await getLifeGoals();
        setGoals(data);
    };

    const handleAddGoal = async () => {
        if (!newGoalTitle) return;
        const success = await createLifeGoal({
            title: newGoalTitle,
            category: 'personal',
            target_date: new Date().toISOString() // Default to today for now
        });
        if (success) {
            setNewGoalTitle('');
            setIsAdding(false);
            loadGoals();
        }
    };

    return (
        <Stack styles={cardStyles} tokens={{ childrenGap: 15 }}>
            <Stack horizontal horizontalAlign="space-between" verticalAlign="center">
                <Text variant="large" style={{ fontWeight: 600 }}>Life Goals</Text>
                <IconButton iconProps={{ iconName: 'Add' }} onClick={() => setIsAdding(!isAdding)} />
            </Stack>

            {isAdding && (
                <Stack tokens={{ childrenGap: 10 }}>
                    <TextField
                        placeholder="Enter a new goal..."
                        value={newGoalTitle}
                        onChange={(_, val) => setNewGoalTitle(val || '')}
                    />
                    <PrimaryButton text="Add Goal" onClick={handleAddGoal} />
                </Stack>
            )}

            <Stack tokens={{ childrenGap: 15 }}>
                {goals.length > 0 ? (
                    goals.map((goal) => (
                        <Stack key={goal.id} tokens={{ childrenGap: 5 }}>
                            <Stack horizontal horizontalAlign="space-between">
                                <Text variant="medium">{goal.title}</Text>
                                <Text variant="small">{goal.progress}%</Text>
                            </Stack>
                            <ProgressIndicator percentComplete={goal.progress / 100} />
                        </Stack>
                    ))
                ) : (
                    <Text>No active goals. Set one today!</Text>
                )}
            </Stack>
        </Stack>
    );
};
