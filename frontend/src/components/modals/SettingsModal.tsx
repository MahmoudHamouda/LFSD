import React, { useState, useEffect, useCallback } from 'react';
import { Dialog, DialogType, DialogFooter } from '@fluentui/react/lib/Dialog';
import { PrimaryButton, DefaultButton } from '@fluentui/react/lib/Button';
import { Toggle } from '@fluentui/react/lib/Toggle';
import styles from './SettingsModal.module.css';
import { getConsent, setConsent, getConsentHistory, ConsentHistoryItem } from '../../api/api';

interface SettingsModalProps {
    isOpen: boolean;
    onDismiss: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onDismiss }) => {
    const [activeTab, setActiveTab] = useState('general');

    const [consent, setConsentState] = useState<boolean | null>(null);
    const [history, setHistory] = useState<ConsentHistoryItem[]>([]);
    const [busy, setBusy] = useState(false);

    const loadConsent = useCallback(async () => {
        const status = await getConsent();
        setConsentState(status ? status.has_consent : null);
        setHistory(await getConsentHistory());
    }, []);

    useEffect(() => {
        if (isOpen && activeTab === 'data') loadConsent();
    }, [isOpen, activeTab, loadConsent]);

    const toggleConsent = async (value: boolean) => {
        setBusy(true);
        const ok = await setConsent(value);
        setBusy(false);
        if (ok) {
            setConsentState(value);
            loadConsent();
        }
    };

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
                            <h3>General</h3>
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

                            {/* AI advisory consent */}
                            <div style={{ borderTop: '1px solid var(--border-color, #e5e5e5)', paddingTop: 12, marginTop: 4 }}>
                                <Toggle
                                    label="Allow AI to analyze my financial data"
                                    inlineLabel
                                    checked={consent === true}
                                    disabled={busy}
                                    onText="On"
                                    offText="Off"
                                    onChange={(_e, checked) => toggleConsent(!!checked)}
                                />
                                <p className={styles.description} style={{ marginTop: 4 }}>
                                    Required for financial questions in chat. Your data is minimized and
                                    personal identifiers are redacted before any AI processing. Turning this
                                    off withdraws consent immediately.
                                </p>

                                {history.length > 0 && (
                                    <details style={{ marginTop: 6 }}>
                                        <summary style={{ cursor: 'pointer', fontSize: 13, opacity: 0.85 }}>
                                            Consent history ({history.length})
                                        </summary>
                                        <ul style={{ margin: '8px 0 0', paddingLeft: 18, fontSize: 12, opacity: 0.8 }}>
                                            {history.slice().reverse().map((h, i) => (
                                                <li key={i}>
                                                    {h.granted ? 'Granted' : 'Withdrawn'} —{' '}
                                                    {new Date(h.timestamp).toLocaleString()}
                                                </li>
                                            ))}
                                        </ul>
                                    </details>
                                )}
                            </div>

                            <div className={styles.settingRow} style={{ marginTop: 14 }}>
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
