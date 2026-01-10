import React, { useState, useEffect } from 'react';
import {
    getTiers,
    updateTier,
    getUserLimits,
    setUserLimits,
    updateUserTier,
    TierConfig,
    UserLimits
} from '../../api/adminApi';

const SubscriptionManagement: React.FC = () => {
    const [tiers, setTiers] = useState<TierConfig[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const [searchUserEmail, setSearchUserEmail] = useState('');
    const [selectedUserLimits, setSelectedUserLimits] = useState<UserLimits | null>(null);
    const [userSearchLoading, setUserSearchLoading] = useState(false);

    useEffect(() => {
        fetchTiers();
    }, []);

    const fetchTiers = async () => {
        try {
            setLoading(true);
            const data = await getTiers();
            setTiers(data);
        } catch (err) {
            setError('Failed to fetch tiers');
        } finally {
            setLoading(false);
        }
    };

    const handleUpdateTierLimit = async (planId: string, key: string, value: number) => {
        const tier = tiers.find(t => t.plan_id === planId);
        if (!tier) return;

        const newConfig = { ...tier.config_json };
        newConfig.limits[key] = value;

        try {
            await updateTier(planId, { config_json: newConfig });
            await fetchTiers();
        } catch (err) {
            alert('Failed to update tier');
        }
    };

    const handleSearchUser = async () => {
        if (!searchUserEmail) return;
        setUserSearchLoading(true);
        try {
            // Note: In a real app we'd search by email and get ID first. 
            // For now, assuming searched text is userId or we'd need an API to search users.
            // Simplified: Fetch user list and find by email.
            const userLimits = await getUserLimits(searchUserEmail); // Reusing userId field as search target
            setSelectedUserLimits(userLimits);
        } catch (err) {
            alert('User not found or error fetching limits');
        } finally {
            setUserSearchLoading(false);
        }
    };

    const handleSetUserOverride = async (key: string, value: number) => {
        if (!selectedUserLimits) return;
        try {
            const newOverrides = { ...selectedUserLimits.overrides, [key]: value };
            await setUserLimits(selectedUserLimits.user_id, newOverrides);
            const updated = await getUserLimits(selectedUserLimits.user_id);
            setSelectedUserLimits(updated);
        } catch (err) {
            alert('Failed to set override');
        }
    };

    if (loading) return <div style={{ padding: 20 }}>Loading Tiers...</div>;

    return (
        <div style={{ padding: '24px' }}>
            <h1 style={{ marginBottom: '24px' }}>Subscription & Tier Management</h1>

            <section style={{ marginBottom: '48px' }}>
                <h2>Global Tiers</h2>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
                    {tiers.map(tier => (
                        <div key={tier.plan_id} style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', background: 'white' }}>
                            <h3 style={{ textTransform: 'capitalize' }}>{tier.name}</h3>
                            <p style={{ color: '#666', fontSize: '14px' }}>{tier.description || 'Global settings for ' + tier.plan_id}</p>

                            <div style={{ marginTop: '16px' }}>
                                <strong>Limits:</strong>
                                <ul style={{ listStyle: 'none', padding: 0 }}>
                                    {Object.entries(tier.config_json.limits).map(([key, val]) => (
                                        <li key={key} style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px' }}>
                                            <span>{key}:</span>
                                            <input
                                                type="number"
                                                value={val}
                                                onChange={(e) => handleUpdateTierLimit(tier.plan_id, key, parseInt(e.target.value))}
                                                style={{ width: '60px', borderRadius: '4px', border: '1px solid #ccc' }}
                                            />
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            <section>
                <h2>User-Specific Overrides</h2>
                <div style={{ marginBottom: '16px' }}>
                    <input
                        type="text"
                        placeholder="User ID..."
                        value={searchUserEmail}
                        onChange={(e) => setSearchUserEmail(e.target.value)}
                        style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', marginRight: '8px' }}
                    />
                    <button
                        onClick={handleSearchUser}
                        style={{ padding: '8px 16px', borderRadius: '4px', background: '#007bff', color: 'white', border: 'none' }}
                        disabled={userSearchLoading}
                    >
                        {userSearchLoading ? 'Searching...' : 'Manage User Limits'}
                    </button>
                </div>

                {selectedUserLimits && (
                    <div style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', background: '#f9f9f9' }}>
                        <h3>Managing Limits for: {selectedUserLimits.user_id}</h3>
                        <p><strong>Current Plan:</strong> {selectedUserLimits.plan}</p>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '40px', marginTop: '20px' }}>
                            <div>
                                <h4>Current Effective Limits</h4>
                                <ul style={{ listStyle: 'none', padding: 0 }}>
                                    {Object.entries(selectedUserLimits.current_limits).map(([key, val]) => (
                                        <li key={key} style={{ marginTop: '4px' }}>
                                            {key}: <strong>{val === -1 ? 'Unlimited' : val}</strong>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                            <div>
                                <h4>Apply Overrides</h4>
                                {Object.entries(selectedUserLimits.current_limits).map(([key, _]) => (
                                    <div key={key} style={{ marginBottom: '12px' }}>
                                        <label style={{ display: 'block', fontSize: '12px' }}>{key}</label>
                                        <input
                                            type="number"
                                            value={selectedUserLimits.overrides[key] || ''}
                                            placeholder="Override value..."
                                            onChange={(e) => handleSetUserOverride(key, parseInt(e.target.value))}
                                            style={{ width: '100px', padding: '4px', borderRadius: '4px', border: '1px solid #ccc' }}
                                        />
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </section>
        </div>
    );
};

export default SubscriptionManagement;
