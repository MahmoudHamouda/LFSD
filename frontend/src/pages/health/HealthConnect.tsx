/**
 * Health Connect Component
 * 
 * Manage health provider connections (WHOOP, Apple Health, Android Health).
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useHealthConnections } from '../../hooks/useUser';
import styles from './HealthConnect.module.css';

const HealthConnect: React.FC = () => {
    const navigate = useNavigate();
    const { connections, isConnected } = useHealthConnections();
    const [connecting, setConnecting] = useState<string | null>(null);

    const handleConnect = async (provider: string) => {
        setConnecting(provider);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/health/connections', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify({
                    provider,
                    permissions: ['read_sleep', 'read_activity', 'read_heart_rate']
                })
            });

            if (!response.ok) throw new Error('Failed to connect');

            // For demo, we just reload/refetch
            window.location.reload();
        } catch (error) {
            console.error(error);
            alert('Failed to connect provider');
        } finally {
            setConnecting(null);
        }
    };

    const handleDisconnect = async (provider: string) => {
        if (!confirm(`Are you sure you want to disconnect ${provider}?`)) return;

        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`/api/health/connections/${provider}`, {
                method: 'DELETE',
                headers: {
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                }
            });

            if (!response.ok) throw new Error('Failed to disconnect');
            window.location.reload();
        } catch (error) {
            console.error(error);
            alert('Failed to disconnect');
        }
    };

    const handleSync = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/health/sync', {
                method: 'POST',
                headers: {
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                }
            });
            if (!response.ok) throw new Error('Failed to sync');
            alert('Synced mock health data successfully!');
        } catch (error) {
            console.error(error);
            alert('Failed to sync data');
        }
    };

    const providers = [
        {
            id: 'whoop',
            name: 'WHOOP',
            icon: '⌚',
            description: 'Track sleep, recovery, and strain with WHOOP wearable',
            benefits: ['Sleep tracking', 'Recovery score', 'Activity load', 'Heart rate variability'],
            available: true,
        },
        {
            id: 'apple_health',
            name: 'Apple Health',
            icon: '',
            description: 'Sync health data from your iPhone and Apple Watch',
            benefits: ['Steps', 'Heart rate', 'Sleep data', 'Workouts'],
            available: true,
        },
        {
            id: 'android_health',
            name: 'Android Health',
            icon: '🤖',
            description: 'Connect Google Fit and Health Connect data',
            benefits: ['Steps', 'Activity', 'Sleep', 'Heart rate'],
            available: true,
        },
    ];

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <button className={styles.backButton} onClick={() => navigate('/health')}>
                    ← Back to Health
                </button>
                <h1 className={styles.title}>Connect Health Providers</h1>
                <p className={styles.subtitle}>
                    Connect your health devices to unlock personalized insights and track your wellbeing
                </p>
            </div>

            <div className={styles.providersList}>
                {providers.map((provider) => {
                    const connected = isConnected(provider.id);
                    const isConnecting = connecting === provider.id;

                    return (
                        <div key={provider.id} className={styles.providerCard}>
                            <div className={styles.providerHeader}>
                                <div className={styles.providerInfo}>
                                    <div className={styles.providerIcon}>{provider.icon}</div>
                                    <div>
                                        <h3 className={styles.providerName}>{provider.name}</h3>
                                        <p className={styles.providerDescription}>{provider.description}</p>
                                    </div>
                                </div>

                                {connected ? (
                                    <div className={styles.connectedBadge}>✓ Connected</div>
                                ) : (
                                    <div className={styles.connectWrapper}>
                                        <button
                                            className={styles.connectButton}
                                            onClick={() => handleConnect(provider.id)}
                                            disabled={isConnecting || !provider.available}
                                        >
                                            {isConnecting ? 'Connecting...' : 'Connect'}
                                        </button>
                                        <p className={styles.privacyNote}>
                                            By connecting, you agree to share {provider.name} data for AI analysis.
                                            <span className={styles.privacyLink} onClick={() => alert("Privacy Policy: Data is encrypted and used only for health insights.")}> Learn more</span>
                                        </p>
                                    </div>
                                )}
                            </div>

                            <div className={styles.benefitsList}>
                                <div className={styles.benefitsTitle}>What you'll get:</div>
                                <ul className={styles.benefits}>
                                    {provider.benefits.map((benefit, index) => (
                                        <li key={index} className={styles.benefit}>
                                            <span className={styles.benefitIcon}>✓</span>
                                            {benefit}
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            {connected && (
                                <div className={styles.connectedActions}>
                                    <div className={styles.connectionDetails}>
                                        <div className={styles.detailItem}>
                                            <span className={styles.detailLabel}>Status:</span>
                                            <span className={styles.detailValue}>Active</span>
                                        </div>
                                        <div className={styles.detailItem}>
                                            <span className={styles.detailLabel}>Last synced:</span>
                                            <span className={styles.detailValue}>2 hours ago</span>
                                        </div>
                                    </div>

                                    <div className={styles.actionButtons}>
                                        <button className={styles.syncButton} onClick={handleSync}>Sync Now</button>
                                        <button
                                            className={styles.disconnectButton}
                                            onClick={() => handleDisconnect(provider.id)}
                                        >
                                            Disconnect
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            <div className={styles.infoSection}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h2 className={styles.infoTitle}>Privacy & Security</h2>
                    <button
                        className={styles.buttonSecondary}
                        style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}
                        onClick={() => alert("Viv: 'I only use your heart rate data to calculate your recovery score and suggest better times for deep work. Your raw data is encrypted and never sold.'")}
                    >
                        Ask Viv about Privacy
                    </button>
                </div>
                <div className={styles.infoGrid}>
                    <div className={styles.infoCard}>
                        <div className={styles.infoIcon}>🔒</div>
                        <h3 className={styles.infoCardTitle}>Encrypted Storage</h3>
                        <p className={styles.infoCardText}>
                            All health data is encrypted and stored securely
                        </p>
                    </div>

                    <div className={styles.infoCard}>
                        <div className={styles.infoIcon}>🎯</div>
                        <h3 className={styles.infoCardTitle}>Your Control</h3>
                        <p className={styles.infoCardText}>
                            You can disconnect any provider at any time
                        </p>
                    </div>

                    <div className={styles.infoCard}>
                        <div className={styles.infoIcon}>📊</div>
                        <h3 className={styles.infoCardTitle}>Better Insights</h3>
                        <p className={styles.infoCardText}>
                            Health data enhances your wellbeing recommendations
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default HealthConnect;
