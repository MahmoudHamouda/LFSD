import React, { useEffect, useState } from 'react';
import { Stack, Text, IStackStyles, PrimaryButton, Icon } from '@fluentui/react';
import { getLifestyleRecommendations, LifestyleRecommendation } from '../../api/lifestyleApi';

const cardStyles: IStackStyles = {
    root: {
        background: 'white',
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
        minWidth: '300px',
    },
};

const itemStyles: IStackStyles = {
    root: {
        padding: '15px',
        border: '1px solid #edebe9',
        borderRadius: '6px',
        background: '#faf9f8',
    },
};

export const LifestyleWidget: React.FC = () => {
    const [recommendations, setRecommendations] = useState<LifestyleRecommendation[]>([]);

    useEffect(() => {
        const loadData = async () => {
            const data = await getLifestyleRecommendations();
            setRecommendations(data);
        };
        loadData();
    }, []);

    return (
        <Stack styles={cardStyles} tokens={{ childrenGap: 15 }}>
            <Stack horizontal horizontalAlign="space-between" verticalAlign="center">
                <Text variant="large" style={{ fontWeight: 600 }}>Treat Yourself</Text>
                <Icon iconName="Giftbox" style={{ fontSize: '20px', color: '#d83b01' }} />
            </Stack>
            <Text variant="small">Rewards based on your recent achievements.</Text>

            <Stack tokens={{ childrenGap: 10 }}>
                {recommendations.length > 0 ? (
                    recommendations.map((rec) => (
                        <Stack key={rec.id} styles={itemStyles} tokens={{ childrenGap: 5 }}>
                            <Stack horizontal horizontalAlign="space-between">
                                <Text variant="medium" style={{ fontWeight: 600 }}>{rec.title}</Text>
                                {rec.cost && <Text variant="small" style={{ color: '#0078d4' }}>${rec.cost}</Text>}
                            </Stack>
                            <Text variant="small" style={{ color: '#666' }}>{rec.description}</Text>
                            <PrimaryButton text="Claim Reward" styles={{ root: { marginTop: '10px' } }} />
                        </Stack>
                    ))
                ) : (
                    <Text>No recommendations yet. Keep up the good work!</Text>
                )}
            </Stack>
        </Stack>
    );
};
