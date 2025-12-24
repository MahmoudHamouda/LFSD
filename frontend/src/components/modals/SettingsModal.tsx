import React, { useState } from 'react';
import { Dialog, DialogType, DialogFooter } from '@fluentui/react/lib/Dialog';
import { PrimaryButton, DefaultButton } from '@fluentui/react/lib/Button';
import { Toggle } from '@fluentui/react/lib/Toggle';
import styles from './SettingsModal.module.css';

interface SettingsModalProps {
    isOpen: boolean;
    onDismiss: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onDismiss }) => {
    const [activeTab, setActiveTab] = useState('general');
    const [isDarkMode, setIsDarkMode] = useState(true);

    const dialogContentProps = {
        type: DialogType.normal,
        title: 'Settings',
        closeButtonAriaLabel: 'Close',
    };

    return (
        <Dialog
            hidden={!isOpen}
            onDismiss={onDismiss}
            dialogContentProps={dialogContentProps}
            minWidth={600}
        >
            <div className={styles.container}>
                <div className={styles.sidebar}>
                    <button
                        className={`${styles.tab} ${activeTab === 'general' ? styles.active : ''}`}
                        onClick={() => setActiveTab('general')}
                    >
                        General
                    </button>
                    <button
                        className={`${styles.tab} ${activeTab === 'data' ? styles.active : ''}`}
                        onClick={() => setActiveTab('data')}
                    >
                        Data controls
                    </button>
                    <button
                        className={`${styles.tab} ${activeTab === 'personalization' ? styles.active : ''}`}
                        onClick={() => setActiveTab('personalization')}
                    >
                        Personalization
                    </button>
                </div>

                <div className={styles.content}>
                    {activeTab === 'general' && (
                        <div className={styles.section}>
                            <h3>Theme</h3>
                            <div className={styles.settingRow}>
                                <span>Dark Mode</span>
                                <Toggle checked={isDarkMode} onChange={(_, checked) => setIsDarkMode(!!checked)} />
                            </div>
                            <div className={styles.settingRow}>
                                <span>Clear all chats</span>
                                <DefaultButton text="Clear" className={styles.dangerButton} />
                            </div>
                        </div>
                    )}

                    {activeTab === 'data' && (
                        <div className={styles.section}>
                            <h3>Data Controls</h3>
                            <p className={styles.description}>Manage your data and privacy settings.</p>
                            <div className={styles.settingRow}>
                                <span>Export data</span>
                                <DefaultButton text="Export" />
                            </div>
                            <div className={styles.settingRow}>
                                <span>Delete account</span>
                                <DefaultButton text="Delete" className={styles.dangerButton} />
                            </div>
                        </div>
                    )}
                </div>
            </div>
            <DialogFooter>
                <PrimaryButton onClick={onDismiss} text="Done" />
            </DialogFooter>
        </Dialog>
    );
};

export default SettingsModal;
