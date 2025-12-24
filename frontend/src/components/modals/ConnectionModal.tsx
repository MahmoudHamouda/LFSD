import React, { useState } from 'react';
import { connectPartner, disconnectPartner, updatePartnerPermissions } from '../../api/api';
import styles from './ConnectionModal.module.css';

interface ConnectionModalProps {
    isOpen: boolean;
    onClose: () => void;
    connector: any; // Replace 'any' with proper type if available, e.g., Connector
}

const ConnectionModal: React.FC<ConnectionModalProps> = ({ isOpen, onClose, connector }) => {
    const [permissions, setPermissions] = useState({
        read: true,
        write: false,
        notifications: true
    });
    const [isLoading, setIsLoading] = useState(false);

    if (!isOpen || !connector) return null;

    const isActive = connector.status === 'active';

    const handleToggle = (key: keyof typeof permissions) => {
        setPermissions(prev => ({
            ...prev,
            [key]: !prev[key]
        }));
    };

    const handleConnect = async () => {
        setIsLoading(true);
        try {
            await connectPartner(connector.id);
            // In a real app, we'd refresh the connector list here
            onClose();
        } catch (error) {
            console.error("Failed to connect", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDisconnect = async () => {
        if (confirm(`Are you sure you want to disconnect ${connector.name}?`)) {
            setIsLoading(true);
            try {
                await disconnectPartner(connector.id);
                onClose();
            } catch (error) {
                console.error("Failed to disconnect", error);
            } finally {
                setIsLoading(false);
            }
        }
    };

    const handleSavePermissions = async () => {
        setIsLoading(true);
        try {
            await updatePartnerPermissions(connector.id, permissions);
            onClose();
        } catch (error) {
            console.error("Failed to update permissions", error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={styles.overlay} onClick={onClose}>
            <div className={styles.modal} onClick={e => e.stopPropagation()}>
                <div className={styles.header}>
                    <div className={styles.titleContainer}>
                        <span className={styles.icon}>
                            {isActive ? '🟢' : '⚪'}
                        </span>
                        <h2 className={styles.title}>{connector.name}</h2>
                    </div>
                    <button className={styles.closeButton} onClick={onClose}>✕</button>
                </div>

                <div className={styles.content}>
                    <div className={`${styles.statusBadge} ${isActive ? styles.statusActive : styles.statusInactive}`}>
                        <span className={styles.statusDot}></span>
                        {isActive ? 'Connected' : 'Not Connected'}
                    </div>

                    {isActive ? (
                        <>
                            <p className={styles.description}>
                                Manage what {connector.name} can do on your behalf.
                            </p>

                            <div className={styles.sectionTitle}>Model Capabilities</div>
                            <div className={styles.permissionsList}>
                                <div className={styles.permissionItem}>
                                    <div className={styles.permissionInfo}>
                                        <span className={styles.permissionLabel}>Read Data</span>
                                        <span className={styles.permissionDesc}>Allow access to view your information</span>
                                    </div>
                                    <label className={styles.toggle}>
                                        <input
                                            type="checkbox"
                                            checked={permissions.read}
                                            onChange={() => handleToggle('read')}
                                        />
                                        <span className={styles.slider}></span>
                                    </label>
                                </div>

                                <div className={styles.permissionItem}>
                                    <div className={styles.permissionInfo}>
                                        <span className={styles.permissionLabel}>Perform Actions</span>
                                        <span className={styles.permissionDesc}>Allow model to make changes</span>
                                    </div>
                                    <label className={styles.toggle}>
                                        <input
                                            type="checkbox"
                                            checked={permissions.write}
                                            onChange={() => handleToggle('write')}
                                        />
                                        <span className={styles.slider}></span>
                                    </label>
                                </div>

                                <div className={styles.permissionItem}>
                                    <div className={styles.permissionInfo}>
                                        <span className={styles.permissionLabel}>Notifications</span>
                                        <span className={styles.permissionDesc}>Receive updates from this connection</span>
                                    </div>
                                    <label className={styles.toggle}>
                                        <input
                                            type="checkbox"
                                            checked={permissions.notifications}
                                            onChange={() => handleToggle('notifications')}
                                        />
                                        <span className={styles.slider}></span>
                                    </label>
                                </div>
                            </div>
                        </>
                    ) : (
                        <>
                            <p className={styles.description}>
                                Connect {connector.name} to unlock powerful features and automation.
                            </p>

                            <ul className={styles.featureList}>
                                <li className={styles.featureItem}>
                                    <span className={styles.checkIcon}>✓</span>
                                    <span>Sync your data automatically</span>
                                </li>
                                <li className={styles.featureItem}>
                                    <span className={styles.checkIcon}>✓</span>
                                    <span>Enable smart recommendations</span>
                                </li>
                                <li className={styles.featureItem}>
                                    <span className={styles.checkIcon}>✓</span>
                                    <span>Personalized insights</span>
                                </li>
                            </ul>
                        </>
                    )}
                </div>

                <div className={styles.footer}>
                    {isActive ? (
                        <>
                            <button className={styles.dangerButton} onClick={handleDisconnect} disabled={isLoading}>
                                {isLoading ? '...' : 'Disconnect'}
                            </button>
                            <button className={styles.primaryButton} onClick={handleSavePermissions} disabled={isLoading}>
                                {isLoading ? 'Saving...' : 'Save Changes'}
                            </button>
                        </>
                    ) : (
                        <>
                            <button className={styles.cancelButton} onClick={onClose}>
                                Cancel
                            </button>
                            <button className={styles.primaryButton} onClick={handleConnect} disabled={isLoading}>
                                {isLoading ? 'Connecting...' : 'Connect Account'}
                            </button>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ConnectionModal;
