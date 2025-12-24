import React from 'react';
import { Stack, Text, IStackStyles } from '@fluentui/react';

const cardStyles: IStackStyles = {
    root: {
        background: 'white',
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        minWidth: '300px',
    },
};

interface NutritionWidgetProps {
    caloriesIn: number;
    caloriesGoal: number;
    protein: number;
    carbs: number;
    fat: number;
}

export const NutritionWidget: React.FC<NutritionWidgetProps> = ({ caloriesIn, caloriesGoal, protein, carbs, fat }) => {
    const percentage = Math.min((caloriesIn / caloriesGoal) * 100, 100);

    return (
        <Stack styles={cardStyles} tokens={{ childrenGap: 15 }}>
            <Text variant="large" style={{ fontWeight: 600 }}>Nutrition</Text>

            <Stack horizontal horizontalAlign="space-between" verticalAlign="center">
                <Stack>
                    <Text variant="xxLarge" style={{ fontWeight: 'bold' }}>{caloriesIn}</Text>
                    <Text variant="small" style={{ color: '#666' }}>/ {caloriesGoal} kcal</Text>
                </Stack>
                {/* Simple Circle Chart Placeholder */}
                <div style={{ width: '60px', height: '60px', borderRadius: '50%', border: '4px solid #f3f2f1', borderTop: '4px solid #0078d4', transform: 'rotate(-45deg)' }}></div>
            </Stack>

            <Stack horizontal tokens={{ childrenGap: 10 }} horizontalAlign="space-between">
                <Stack horizontalAlign="center">
                    <Text variant="small" style={{ fontWeight: 600 }}>Protein</Text>
                    <Text variant="medium">{protein}g</Text>
                </Stack>
                <Stack horizontalAlign="center">
                    <Text variant="small" style={{ fontWeight: 600 }}>Carbs</Text>
                    <Text variant="medium">{carbs}g</Text>
                </Stack>
                <Stack horizontalAlign="center">
                    <Text variant="small" style={{ fontWeight: 600 }}>Fat</Text>
                    <Text variant="medium">{fat}g</Text>
                </Stack>
            </Stack>
        </Stack>
    );
};
