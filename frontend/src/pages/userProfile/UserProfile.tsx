
import React, { useEffect, useState } from 'react';
import { Trash2, Sun, Moon } from 'lucide-react';
import { historyDeleteAll } from '../../api/api';
import styles from './UserProfile.module.css';
import { getUserProfile, updateUserProfile } from '../../api/userApi';
import { getStoredTheme, setStoredTheme } from '../../utils/theme';
import { User, UserIdentity, VivPreferences, OnboardingData } from '../../types/user';
import { CurrencyInput, Pill, SectionCard } from '../onboarding/OnboardingSteps';
import ConnectionModal from '../../components/modals/ConnectionModal';
import StatementUploadModal from '../../components/modals/StatementUploadModal';
import { useLocation } from 'react-router-dom';

type Tab = 'account' | 'financial' | 'health' | 'time' | 'updates' | 'faq';

interface Connector {
    id: string;
    name: string;
    category: 'financial' | 'health' | 'time' | 'mobility';
    status: 'active' | 'inactive' | 'pending' | 'failed';
    icon?: string;
}

const CONNECTIONS_DATA: Connector[] = [
    { id: 'plaid', name: 'Bank Accounts (Plaid)', category: 'financial', status: 'inactive' },
    { id: 'stripe', name: 'Stripe', category: 'financial', status: 'inactive' },
    { id: 'statements', name: 'Bank Statements', category: 'financial', status: 'active' },
    { id: 'apple_health', name: 'Apple Health', category: 'health', status: 'active' },
    { id: 'google_health', name: 'Google Health', category: 'health', status: 'active' },
    { id: 'whoop', name: 'Whoop', category: 'health', status: 'inactive' },
    { id: 'google_calendar', name: 'Google Calendar', category: 'time', status: 'active' },
    { id: 'outlook', name: 'Outlook Calendar', category: 'time', status: 'inactive' },
    { id: 'uber', name: 'Uber', category: 'mobility', status: 'active' },
    { id: 'talabaat', name: 'Talabaat', category: 'time', status: 'inactive' },
];

const UserProfile: React.FC = () => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [activeTab, setActiveTab] = useState<Tab>('account');
    const [theme, setTheme] = useState<'light' | 'dark'>(getStoredTheme());
    const location = useLocation();

    // Connection Logic
    const [selectedConnector, setSelectedConnector] = useState<Connector | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

    // Form states
    const [identityForm, setIdentityForm] = useState<Partial<UserIdentity>>({});
    const [prefForm, setPrefForm] = useState<Partial<VivPreferences>>({});
    const [onboardingForm, setOnboardingForm] = useState<OnboardingData>({});

    // Load Profile Effect
    useEffect(() => {
        loadProfile();

        // Handle redirect actions (tabs)
        const params = new URLSearchParams(location.search);
        if (params.get('tab')) {
            setActiveTab(params.get('tab') as Tab);
        }
        if (params.get('action') === 'upload') {
            setActiveTab('financial');
            setIsUploadModalOpen(true);
        }
    }, [location]);

    // Scroll Effect for Anchors
    useEffect(() => {
        if (!loading && location.hash) {
            const id = location.hash.replace('#', '');
            // Small timeout to allow tab switch/render
            setTimeout(() => {
                const element = document.getElementById(id);
                if (element) {
                    element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }, 600);
        }
    }, [loading, location.hash, activeTab]);

    const loadProfile = async () => {
        try {
            const userData = await getUserProfile();
            if (userData) {
                setUser(userData);
                setIdentityForm(userData.identity);
                setPrefForm(userData.identity.vivPreferences || {});
                const existingOnboarding = userData.identity.profile?.onboarding_data || {};
                setOnboardingForm(existingOnboarding);
            }
        } catch (error) {
            console.error("Failed to load profile", error);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            const updatedUser = await updateUserProfile({
                identity: identityForm,
                vivPreferences: prefForm,
                onboarding_data: onboardingForm
            });
            if (updatedUser) {
                setUser(updatedUser);
                alert('Profile updated and scores recalculated!');
            }
        } catch (error) {
            console.error("Failed to update profile", error);
            alert('Failed to update profile.');
        } finally {
            setSaving(false);
        }
    };

    const toggleTheme = (newTheme: 'light' | 'dark') => {
        setTheme(newTheme);
        setStoredTheme(newTheme);
    };

    const updateOnboarding = (key: string, value: any) => {
        setOnboardingForm(prev => ({ ...prev, [key]: value }));
    };

    const handleConnectorClick = (connector: Connector) => {
        if (connector.id === 'statements') {
            setIsUploadModalOpen(true);
        } else {
            setSelectedConnector(connector);
            setIsModalOpen(true);
        }
    };

    const handleBack = () => {
        window.location.href = '/finance';
    };

    const renderConnections = (categories: string[]) => {
        const items = CONNECTIONS_DATA.filter(c => categories.includes(c.category));
        if (items.length === 0) return null;

        return (
            <div id={`connections-${categories.join('-')}`}>
                <SectionCard title="Integrations & Data Sources">
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
                        {items.map(item => {
                            const isInactive = item.status === 'inactive';
                            return (
                                <div
                                    key={item.id}
                                    onClick={() => !isInactive && handleConnectorClick(item)}
                                    className={`${styles.connectorCard} ${isInactive ? styles.inactiveCard : styles.activeCard}`}
                                >
                                    <span className={styles.connectorName}>
                                        {item.name}
                                    </span>
                                    {isInactive ? (
                                        <span className={styles.soonBadge}>
                                            Soon
                                        </span>
                                    ) : (
                                        <span
                                            className={styles.statusDot}
                                            style={{
                                                backgroundColor:
                                                    item.status === 'active' ? 'var(--color-accent-blue)' :
                                                        item.status === 'failed' ? 'var(--color-accent-red)' :
                                                            item.status === 'pending' ? 'var(--status-warning)' : 'var(--text-secondary)'
                                            }}
                                        />
                                    )}
                                </div>
                            );
                        })}
                    </div>
                </SectionCard>
            </div>
        );
    };

    if (loading) return <div className={styles.container}>Loading Profile...</div>;
    if (!user) return <div className={styles.container}>Please Log In</div>;

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h1 className={styles.title}>My Account</h1>
                        <p className={styles.subtitle}>Manage your profile, preferences, and HELM data.</p>
                    </div>
                    <button
                        onClick={handleBack}
                        className={styles.saveButton}
                        style={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }}
                    >
                        Return to Dashboard
                    </button>
                </div>
            </div>

            <div className={styles.tabsContainer}>
                {(['account', 'financial', 'health', 'time', 'updates', 'faq'] as const).map(tab => {
                    const label = {
                        account: 'Account',
                        financial: 'Finances',
                        health: 'Energy',
                        time: 'Focus',
                        updates: 'Updates',
                        faq: 'FAQ'
                    }[tab];
                    return (
                        <button
                            key={tab}
                            className={`${styles.tab} ${activeTab === tab ? styles.activeTab : ''}`}
                            onClick={() => setActiveTab(tab)}
                        >
                            {label}
                        </button>
                    );
                })}
            </div>

            {/* Account Tab */}
            {activeTab === 'account' && (
                <div className={styles.section}>
                    <SectionCard title="Personal Details">
                        <div className={styles.formGrid}>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>First Name</label>
                                <input className={styles.input} value={identityForm.firstName || ''} onChange={e => setIdentityForm({ ...identityForm, firstName: e.target.value })} />
                            </div>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>Last Name</label>
                                <input className={styles.input} value={identityForm.lastName || ''} onChange={e => setIdentityForm({ ...identityForm, lastName: e.target.value })} />
                            </div>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>Email</label>
                                <input className={styles.input} value={identityForm.email || ''} disabled style={{ backgroundColor: 'var(--bg-secondary)' }} />
                            </div>
                        </div>
                    </SectionCard>
                    <div style={{ height: '20px' }} />
                    <SectionCard title="Preferences">
                        <div className={styles.formGrid}>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>Risk Tolerance</label>
                                <select className={styles.select} value={prefForm.riskTolerance || 'medium'} onChange={e => setPrefForm({ ...prefForm, riskTolerance: e.target.value as any })}>
                                    <option value="low">Low (Conservative)</option>
                                    <option value="medium">Medium (Balanced)</option>
                                    <option value="high">High (Aggressive)</option>
                                </select>
                            </div>

                            <div className={styles.formGroup}>
                                <label className={styles.label}>Appearance</label>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                    <button
                                        onClick={() => toggleTheme('light')}
                                        className={`${styles.themeButton} ${theme === 'light' ? styles.activeTheme : ''}`}
                                        style={{
                                            display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px',
                                            borderRadius: '8px', border: '1px solid var(--border-color)',
                                            background: theme === 'light' ? 'var(--color-accent-blue)' : 'var(--bg-card)',
                                            color: theme === 'light' ? 'white' : 'var(--text-primary)',
                                            cursor: 'pointer', flex: 1, justifyContent: 'center', fontWeight: 500
                                        }}
                                    >
                                        <Sun size={16} /> Light
                                    </button>
                                    <button
                                        onClick={() => toggleTheme('dark')}
                                        className={`${styles.themeButton} ${theme === 'dark' ? styles.activeTheme : ''}`}
                                        style={{
                                            display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 16px',
                                            borderRadius: '8px', border: '1px solid var(--border-color)',
                                            background: theme === 'dark' ? 'var(--color-accent-blue)' : 'var(--bg-card)',
                                            color: theme === 'dark' ? 'white' : 'var(--text-primary)',
                                            cursor: 'pointer', flex: 1, justifyContent: 'center', fontWeight: 500
                                        }}
                                    >
                                        <Moon size={16} /> Dark
                                    </button>
                                </div>
                            </div>
                        </div>
                    </SectionCard>

                    <div style={{ height: '20px' }} />
                    <SectionCard title="Data Management">
                        <div className={styles.formGrid}>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Conversation History</label>
                                <div>
                                    <button
                                        onClick={async () => {
                                            if (confirm('Are you sure you want to clear all conversations from your view? This action cannot be undone.')) {
                                                try {
                                                    // Soft clear: Set timestamp
                                                    localStorage.setItem('lastClearedHistory', new Date().toISOString());
                                                    alert('Conversation history cleared from view.');
                                                    window.location.reload();
                                                } catch (e) {
                                                    console.error("Failed to clear history", e);
                                                    alert('Failed to clear history.');
                                                }
                                            }
                                        }}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '8px',
                                            padding: '8px 16px',
                                            backgroundColor: 'var(--bg-badge-error)',
                                            color: 'var(--color-accent-red)',
                                            border: '1px solid var(--border-light)',
                                            borderRadius: '6px',
                                            cursor: 'pointer',
                                            fontSize: '14px',
                                            fontWeight: 500
                                        }}
                                    >
                                        <Trash2 size={16} />
                                        Clear all conversations
                                    </button>
                                    <p style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                                        Permanently remove all chat history from this device and the server.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </SectionCard>
                </div>
            )}

            {/* Financial Tab */}
            {activeTab === 'financial' && (
                <div className={styles.section} id="logging">
                    {renderConnections(['financial'])}
                    <div style={{ height: '24px' }} />
                    <SectionCard title="Income & Employment">
                        <div className={styles.formGrid}>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>Monthly Income (Net)</label>
                                <CurrencyInput
                                    className={styles.input}
                                    value={onboardingForm.monthly_income || 0}
                                    onChange={val => updateOnboarding('monthly_income', val)}
                                />
                            </div>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>Frequency</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['Weekly', 'Bi-Weekly', 'Monthly', 'Irregular'].map(freq => (
                                        <Pill
                                            key={freq}
                                            label={freq}
                                            selected={onboardingForm.income_frequency === freq}
                                            onClick={() => updateOnboarding('income_frequency', freq)}
                                        />
                                    ))}
                                </div>
                            </div>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Employment Type</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['Full-time', 'Part-time', 'Freelance', 'Business Owner', 'Student', 'Retired', 'Not Working'].map(type => (
                                        <Pill
                                            key={type}
                                            label={type}
                                            selected={onboardingForm.employment_type === type}
                                            onClick={() => updateOnboarding('employment_type', type)}
                                        />
                                    ))}
                                </div>
                            </div>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Other Income Sources</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['Bonus', 'Commission', 'Freelance', 'Rental', 'Family Support', 'Pension', 'Dividends'].map(source => (
                                        <Pill
                                            key={source}
                                            label={source}
                                            selected={(onboardingForm.other_income_sources || []).includes(source)}
                                            onClick={() => {
                                                const current = onboardingForm.other_income_sources || [];
                                                const updated = current.includes(source)
                                                    ? current.filter(s => s !== source)
                                                    : [...current, source];
                                                updateOnboarding('other_income_sources', updated);
                                            }}
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    </SectionCard>

                    <div style={{ height: '24px' }} />

                    <div id="bills">
                        <SectionCard title="Monthly Commitments">
                            <div className={styles.formGrid}>
                                <div className={styles.formGroup}>
                                    <label className={styles.label}>Monthly Expenses (Approx)</label>
                                    <CurrencyInput
                                        className={styles.input}
                                        value={onboardingForm.monthly_expenses || 0}
                                        onChange={val => updateOnboarding('monthly_expenses', val)}
                                    />
                                </div>
                                <div className={styles.formGroup}>
                                    <label className={styles.label}>Debt Payments (Monthly)</label>
                                    <CurrencyInput
                                        className={styles.input}
                                        value={onboardingForm.monthly_debt_payments || 0}
                                        onChange={val => updateOnboarding('monthly_debt_payments', val)}
                                    />
                                </div>
                                <div className={styles.formGroup}>
                                    <label className={styles.label}>Housing Status</label>
                                    <select className={styles.select} value={onboardingForm.housing_status || 'rent'} onChange={e => updateOnboarding('housing_status', e.target.value)}>
                                        <option value="rent">Rent</option>
                                        <option value="own">Own</option>
                                        <option value="family">Family</option>
                                        <option value="other">Other</option>
                                    </select>
                                </div>
                                {onboardingForm.housing_status === 'rent' ? (
                                    <div className={styles.formGroup}>
                                        <label className={styles.label}>Rent Amount</label>
                                        <CurrencyInput
                                            className={styles.input}
                                            value={onboardingForm.rent_amount || 0}
                                            onChange={val => updateOnboarding('rent_amount', val)}
                                        />
                                    </div>
                                ) : onboardingForm.housing_status === 'own' ? (
                                    <div className={styles.formGroup}>
                                        <label className={styles.label}>Home Value (Approx)</label>
                                        <CurrencyInput
                                            className={styles.input}
                                            value={onboardingForm.housing_value || 0}
                                            onChange={val => updateOnboarding('housing_value', val)}
                                        />
                                    </div>
                                ) : null}

                                <div className={styles.formGroup}>
                                    <label className={styles.label}>Car Status</label>
                                    <select className={styles.select} value={onboardingForm.car_status || 'no_car'} onChange={e => updateOnboarding('car_status', e.target.value)}>
                                        <option value="no_car">No Car</option>
                                        <option value="own">Own</option>
                                        <option value="lease">Lease</option>
                                    </select>
                                </div>
                                {onboardingForm.car_status === 'own' && (
                                    <div className={styles.formGroup}>
                                        <label className={styles.label}>Car Value</label>
                                        <CurrencyInput
                                            className={styles.input}
                                            value={onboardingForm.car_value || 0}
                                            onChange={val => updateOnboarding('car_value', val)}
                                        />
                                    </div>
                                )}
                                {onboardingForm.car_status === 'lease' && (
                                    <div className={styles.formGroup}>
                                        <label className={styles.label}>Lease Amount</label>
                                        <CurrencyInput
                                            className={styles.input}
                                            value={onboardingForm.car_lease_amount || 0}
                                            onChange={val => updateOnboarding('car_lease_amount', val)}
                                        />
                                    </div>
                                )}
                            </div>
                        </SectionCard>
                    </div>

                    <div style={{ height: '24px' }} />

                    <SectionCard title="Financial Habits & Assets">
                        <div className={styles.formGrid}>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>Monthly Savings</label>
                                <CurrencyInput
                                    className={styles.input}
                                    value={onboardingForm.monthly_savings || 0}
                                    onChange={val => updateOnboarding('monthly_savings', val)}
                                />
                            </div>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>Discretionary Spend</label>
                                <CurrencyInput
                                    className={styles.input}
                                    value={onboardingForm.discretionary_spend || 0}
                                    onChange={val => updateOnboarding('discretionary_spend', val)}
                                />
                            </div>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>Investments Value</label>
                                <CurrencyInput
                                    className={styles.input}
                                    value={onboardingForm.investments_value || 0}
                                    onChange={val => updateOnboarding('investments_value', val)}
                                />
                            </div>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>Investment Types</label>
                                <input
                                    type="text"
                                    className={styles.input}
                                    placeholder="Stocks, crypto, etc."
                                    value={(onboardingForm.investments_types || []).join(', ')}
                                    onChange={(e) => updateOnboarding('investments_types', e.target.value.split(',').map(s => s.trim()))}
                                />
                            </div>
                        </div>
                    </SectionCard>
                </div>
            )}


            {/* Health (Energy) Tab */}
            {activeTab === 'health' && (
                <div className={styles.section}>
                    {renderConnections(['health'])}
                    <div style={{ height: '24px' }} />

                    <SectionCard title="Sleep">
                        <div className={styles.formGrid}>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Daily Sleep Hours</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['<5', '5-6', '6-7', '7-8', '8-9', '9+'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.sleep_hours === opt}
                                            onClick={() => updateOnboarding('sleep_hours', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Sleep Consistency</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['Consistent', 'Mostly', 'Not really'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.sleep_consistency === opt}
                                            onClick={() => updateOnboarding('sleep_consistency', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Wake up tired?</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['Yes', 'Sometimes', 'No'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.wake_tired === opt}
                                            onClick={() => updateOnboarding('wake_tired', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    </SectionCard>

                    <div style={{ height: '24px' }} />

                    <SectionCard title="Activity & Recovery">
                        <div className={styles.formGrid}>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Activity Level</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['Sedentary', 'Lightly active', 'Moderate', 'High'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.activity_level === opt}
                                            onClick={() => updateOnboarding('activity_level', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Primary Activity</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['Walking', 'Running', 'Gym', 'Yoga', 'Sports', 'None'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.activity_type === opt}
                                            onClick={() => updateOnboarding('activity_type', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Stress Level</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['Rarely', 'Sometimes', 'Often', 'Almost always'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.stress_level === opt}
                                            onClick={() => updateOnboarding('stress_level', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    </SectionCard>

                    <div style={{ height: '24px' }} />

                    <SectionCard title="Nutrition & Lifestyle">
                        <div className={styles.formGrid}>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Diet Style</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['Balanced', 'Mediterranean', 'High-carb', 'High-protein', 'Vegetarian', 'Vegan', 'Whatever'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.diet_style === opt}
                                            onClick={() => updateOnboarding('diet_style', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Water Intake</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['<1L', '1-2L', '2-3L', '3L+'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.water_intake === opt}
                                            onClick={() => updateOnboarding('water_intake', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Alcohol</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['Never', 'Occasionally', 'Regularly'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.alcohol_pattern === opt}
                                            onClick={() => updateOnboarding('alcohol_pattern', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Eating Out Freq</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['Rarely', '1-2x week', '3-5x week', 'Daily'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.eating_out_frequency === opt}
                                            onClick={() => updateOnboarding('eating_out_frequency', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    </SectionCard>
                </div>
            )}


            {/* Time (Focus) Tab */}
            {activeTab === 'time' && (
                <div className={styles.section}>
                    {renderConnections(['time', 'mobility'])}
                    <div style={{ height: '24px' }} />

                    <SectionCard title="Work & Structure">
                        <div className={styles.formGrid}>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Work Status</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['Full-time', 'Part-time', 'Freelance', 'Business Owner', 'Student', 'Not Working'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.work_status === opt}
                                            onClick={() => updateOnboarding('work_status', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Work Hours/Week</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['<20', '20-35', '35-45', '45-55', '55+'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.work_hours_per_week === opt}
                                            onClick={() => updateOnboarding('work_hours_per_week', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Digital Calendar</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['Yes - Google', 'Yes - Outlook', 'Yes - Apple', 'Yes - Other', 'No'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.uses_digital_calendar === opt}
                                            onClick={() => updateOnboarding('uses_digital_calendar', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    </SectionCard>

                    <div style={{ height: '24px' }} />

                    <SectionCard title="Mobility & Commute">
                        <div className={styles.formGrid}>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Commute Duration</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['WFH', '<15 min', '15-30 min', '30-45 min', '45-60 min', '1 hr+'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.commute_duration === opt}
                                            onClick={() => updateOnboarding('commute_duration', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    </SectionCard>

                    <div style={{ height: '24px' }} />

                    <SectionCard title="Time Use & Drains">
                        <div className={styles.formGrid}>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Meals/House (Daily)</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['<30 min', '30-60 min', '1-2 hours', '2+ hours'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.time_meals_house_daily === opt}
                                            onClick={() => updateOnboarding('time_meals_house_daily', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Admin (Weekly)</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['<1 hour', '1-3 hours', '3-5 hours', '5+ hours'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.time_admin_weekly === opt}
                                            onClick={() => updateOnboarding('time_admin_weekly', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Main Time Drains</label>
                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                                    {[
                                        "Commuting", "Emails", "Meetings", "Kids schedules", "Errands",
                                        "Bills & admin", "Last-minute tasks", "Finding services", "Not sure"
                                    ].map(option => (
                                        <Pill
                                            key={option}
                                            label={option}
                                            selected={(onboardingForm.main_time_drains || []).includes(option)}
                                            onClick={() => {
                                                const current = onboardingForm.main_time_drains || [];
                                                const updated = current.includes(option)
                                                    ? current.filter(d => d !== option)
                                                    : [...current, option];
                                                updateOnboarding('main_time_drains', updated);
                                            }}
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    </SectionCard>

                    <div style={{ height: '24px' }} />

                    <SectionCard title="Style & Pressure">
                        <div className={styles.formGrid}>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Routine Style</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['I follow a routine', 'I try', 'Not really', 'Spontaneous'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.routine_style === opt}
                                            onClick={() => updateOnboarding('routine_style', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                            <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                                <label className={styles.label}>Time Overwhelm</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['Rarely', 'Sometimes', 'Often', 'Almost always'].map(opt => (
                                        <Pill
                                            key={opt}
                                            label={opt}
                                            selected={onboardingForm.time_overwhelm_level === opt}
                                            onClick={() => updateOnboarding('time_overwhelm_level', opt)}
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    </SectionCard>
                </div>
            )}

            {/* Updates Tab */}
            {activeTab === 'updates' && (
                <div className={styles.section}>
                    <SectionCard title="Product Updates">
                        <div className={styles.updateList}>
                            <div className={styles.updateItem}>
                                <h4 style={{ margin: '0 0 8px 0', color: 'var(--text-primary)' }}>v1.2.0 - Personal Benchmarks</h4>
                                <p style={{ margin: '0', fontSize: '14px', color: 'var(--text-secondary)' }}>
                                    We've added personal benchmarking for your Focus and Energy scores.
                                    See how you compare to your own averages over the last 90 days.
                                </p>
                                <span style={{ fontSize: '12px', color: 'var(--color-accent-blue)', fontWeight: 500 }}>December 2025</span>
                            </div>
                            <div style={{ height: '20px', borderBottom: '1px solid var(--border-color)', margin: '16px 0' }} />
                            <div className={styles.updateItem}>
                                <h4 style={{ margin: '0 0 8px 0', color: 'var(--text-primary)' }}>v1.1.5 - New Mobility Connectors</h4>
                                <p style={{ margin: '0', fontSize: '14px', color: 'var(--text-secondary)' }}>
                                    Uber and local public transit integrations are now more robust,
                                    providing better cost-vs-time trade-off analysis.
                                </p>
                                <span style={{ fontSize: '12px', color: 'var(--color-accent-blue)', fontWeight: 500 }}>November 2025</span>
                            </div>
                        </div>
                    </SectionCard>
                </div>
            )}

            {/* FAQ Tab */}
            {activeTab === 'faq' && (
                <div className={styles.section}>
                    <SectionCard title="Frequently Asked Questions">
                        <div className={styles.faqList}>
                            {[
                                { q: "How are my scores calculated?", a: "Scores are derived from a combination of your connected data (Plaid, Google Health, etc.) and your onboarding profile, processed through our proprietary wellbeing engine." },
                                { q: "Is my data secure?", a: "Yes. We use industry-standard encryption and never sell your personal data. You can clear your conversation history at any time." },
                                { q: "Can I connect multiple bank accounts?", a: "Currently, we support one primary bank connection via Plaid and manual statement uploads for others." },
                                { q: "What is 'Energy Score'?", a: "It's a holistic view of your physical state, combining sleep quality, activity levels, and recovery metrics." }
                            ].map((faq, i) => (
                                <div key={i} style={{ marginBottom: '24px' }}>
                                    <h4 style={{ margin: '0 0 8px 0', color: 'var(--text-primary)' }}>{faq.q}</h4>
                                    <p style={{ margin: '0', fontSize: '14px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>{faq.a}</p>
                                </div>
                            ))}
                        </div>
                    </SectionCard>
                </div>
            )}


            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '24px', paddingBottom: '40px' }}>
                <button className={styles.saveButton} onClick={handleSave} disabled={saving}>
                    {saving ? 'Saving...' : 'Save Changes'}
                </button>
            </div>

            <ConnectionModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                connector={selectedConnector}
            />
            <StatementUploadModal
                isOpen={isUploadModalOpen}
                onClose={() => setIsUploadModalOpen(false)}
            />
        </div>
    );
};

export default UserProfile;
