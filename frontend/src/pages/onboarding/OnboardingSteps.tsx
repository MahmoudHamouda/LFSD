import React from 'react';
import styles from './Onboarding.module.css';
import { FileUploadProgress, FileUploadStatus } from '../../components/FileUploadProgress';
import { Activity, Heart, Calendar, Check, Loader2, FileCheck } from 'lucide-react';

export interface CurrencyInputProps {
    value: number;
    onChange: (value: number) => void;
    placeholder?: string;
    className?: string;
    style?: React.CSSProperties;
}

export const CurrencyInput: React.FC<CurrencyInputProps> = ({ value, onChange, placeholder, className, style }) => {
    // Initialize display value from prop
    const [displayValue, setDisplayValue] = React.useState(() =>
        value ? new Intl.NumberFormat('en-US').format(value) : ''
    );
    const [isFocused, setIsFocused] = React.useState(false);

    // Sync with external value changes ONLY when not focused to avoid cursor jumping
    React.useEffect(() => {
        if (!isFocused) {
            setDisplayValue(value ? new Intl.NumberFormat('en-US').format(value) : '');
        }
    }, [value, isFocused]);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = e.target.value;

        // Allow digits, commas, and one decimal point
        if (/^[0-9,]*\.?[0-9]*$/.test(val)) {
            setDisplayValue(val);

            // Parse and notify parent
            const rawValue = val.replace(/,/g, '');
            const num = parseFloat(rawValue);
            onChange(isNaN(num) ? 0 : num);
        }
    };

    const handleFocus = () => {
        setIsFocused(true);
        // On focus, show raw number for easier editing, or empty string if 0/null
        setDisplayValue(value ? value.toString() : '');
    };

    const handleBlur = () => {
        setIsFocused(false);
        // On blur, format back to currency
        setDisplayValue(value ? new Intl.NumberFormat('en-US').format(value) : '');
    };

    return (
        <input
            type="text"
            className={className}
            placeholder={placeholder}
            value={displayValue}
            onChange={handleChange}
            onFocus={handleFocus}
            onBlur={handleBlur}
            style={style}
        />
    );
};

export interface StepProps {
    onNext: () => void;
    onBack?: () => void;
    backLabel?: string;
    data: any;
    updateData: (key: string, value: any) => void;
    onSocialSuccess?: (userId: string) => void;
}

export const WelcomeStep: React.FC<StepProps> = ({ onNext, onBack, data, updateData }) => {
    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Welcome — let's make your life a little lighter.</h1>
                <p className={styles.subtitle}>
                    "Think of this app as your everyday co-pilot.
                    <br />
                    Here to help you save money, save time, and feel better — one small step at a time."
                </p>
            </div>

            <div className={styles.formGroup}>
                <label className={styles.label}>What should we call you? (Optional)</label>
                <input
                    type="text"
                    className={styles.input}
                    value={data.name || ''}
                    onChange={(e) => updateData('name', e.target.value)}
                    placeholder="Your Name"
                />
            </div>

            <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
                {onBack && (
                    <button
                        className={styles.button}
                        onClick={onBack}
                        style={{ backgroundColor: 'var(--bg-primary)', color: 'var(--text-secondary)', border: '1px solid var(--border-light)' }}
                    >
                        Log Out
                    </button>
                )}
                <button className={styles.button} onClick={onNext} style={{ flex: 1 }}>
                    Next →
                </button>
            </div>
        </div>
    );
};

export const Pill = ({ label, selected, onClick }: { label: string, selected: boolean, onClick: () => void }) => (
    <div
        onClick={onClick}
        style={{
            padding: '0.5rem 1rem',
            borderRadius: 'var(--radius-full)',
            border: `1px solid ${selected ? 'var(--color-accent-blue)' : 'var(--border-light)'}`,
            background: selected ? 'var(--bg-badge-success)' : 'var(--bg-card)',
            color: selected ? 'var(--color-accent-blue)' : 'var(--text-secondary)',
            cursor: 'pointer',
            fontSize: '0.9rem',
            fontWeight: 500,
            transition: 'all 0.2s'
        }}
    >
        {label}
    </div>
);

export const SectionCard = ({ title, children }: { title: string, children: React.ReactNode }) => (
    <div style={{
        background: 'var(--bg-secondary)',
        padding: '1.5rem',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-light)',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem'
    }}>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>{title}</h3>
        {children}
    </div>
);

export const FinancialStep1: React.FC<StepProps> = ({ onNext, onBack, backLabel, data, updateData }) => {
    console.log('FinancialStep1 Render');
    React.useEffect(() => {
        console.log('FinancialStep1 MOUNT');
        return () => console.log('FinancialStep1 UNMOUNT');
    }, []);
    const [uploadComplete, setUploadComplete] = React.useState(() => !!data.onboarding_session_id);
    const [isUploadFinished, setIsUploadFinished] = React.useState(() => (data.financial?.session_ids || []).length > 0);
    const [sessionIds, setSessionIds] = React.useState<string[]>(() => data.financial?.session_ids || []);
    const [files, setFiles] = React.useState<FileUploadStatus[]>(() => {
        if (data.financial?.session_ids && data.financial.session_ids.length > 0) {
            return data.financial.session_ids.map((sid: string, i: number) => ({
                filename: `Uploaded Statement ${i + 1}`,
                status: 'complete',
                progress: 100,
                sessionId: sid
            }));
        }
        return [];
    });
    const [incomeInputMode, setIncomeInputMode] = React.useState<'amount' | 'range'>('amount');
    const [showIncomeInput, setShowIncomeInput] = React.useState(() => {
        return !!data.financial?.is_manual_mode || (
            !data.onboarding_session_id && (
                (data.financial?.monthly_income || 0) > 0 ||
                data.financial?.monthly_income_type === 'range'
            )
        );
    });

    const updateFin = (key: string, val: any) => {
        updateData('financial', { ...data.financial, [key]: val });
    };

    const handleUploadComplete = (ids: string[]) => {
        if (ids.length === 0) {
            return;
        }
        setSessionIds(ids);
        setIsUploadFinished(true);
        updateFin('is_manual_mode', false);
        updateFin('session_ids', ids); // Persist immediately
    };

    const handleContinue = () => {
        // Update parent state only when moving forward
        if (sessionIds.length > 0) {
            updateFin('onboarding_session_id', sessionIds[0]);
        }
        updateFin('session_ids', sessionIds);

        setUploadComplete(true);
        setShowIncomeInput(true);
    };

    const handleRemoveFile = (fileToRemove: any) => {
        const newFiles = files.filter(f => f !== fileToRemove);
        setFiles(newFiles);

        // Update session IDs
        const newSessionIds = sessionIds.filter(sid => sid !== fileToRemove.sessionId);
        setSessionIds(newSessionIds);
        updateFin('session_ids', newSessionIds);

        if (newSessionIds.length === 0) {
            setIsUploadFinished(false);
            setUploadComplete(false); // If they removed all, they aren't done.
        }
    };

    const handleUploadError = (error: string) => {
        alert(`Upload failed: ${error}`);
    };

    const toggleIncomeMode = () => {
        setIncomeInputMode(prev => prev === 'amount' ? 'range' : 'amount');
        updateFin('monthly_income_type', incomeInputMode === 'amount' ? 'range' : 'amount');
    };

    const toggleOtherSource = (source: string) => {
        const current = data.financial?.other_income_sources || [];
        const updated = current.includes(source)
            ? current.filter((s: string) => s !== source)
            : [...current, source];
        updateFin('other_income_sources', updated);
    };

    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>
                    {!showIncomeInput && !uploadComplete
                        ? "Help us create a 360 view on your financial health."
                        : "Let's start with what comes in."}
                </h1>
                <p className={styles.subtitle}>
                    We'll build your financial picture from the ground up.
                </p>
            </div>


            {!showIncomeInput && !uploadComplete ? (
                <>
                    <FileUploadProgress
                        onComplete={handleUploadComplete}
                        onError={handleUploadError}
                        files={files}
                        onFilesChange={setFiles}
                        onRemove={handleRemoveFile}
                    />

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '1rem' }}>
                        {isUploadFinished ? (
                            <div style={{ display: 'flex', gap: '1rem' }}>
                                {onBack && (
                                    <button
                                        className={styles.buttonSecondary}
                                        onClick={onBack}
                                        style={{ flex: 1 }}
                                    >
                                        ← Back
                                    </button>
                                )}
                                <button
                                    className={styles.button}
                                    onClick={handleContinue}
                                    style={{ flex: 1, marginTop: 0 }}
                                >
                                    Next →
                                </button>
                            </div>
                        ) : (
                            <>
                                <button
                                    className={styles.buttonSecondary}
                                    onClick={() => {
                                        setShowIncomeInput(true);
                                        updateFin('is_manual_mode', true);
                                    }}
                                >
                                    I don't have statements handy
                                </button>
                                {onBack && (
                                    <button
                                        className={styles.buttonSecondary}
                                        onClick={onBack}
                                    >
                                        ← Back
                                    </button>
                                )}
                            </>
                        )}
                    </div>
                </>
            ) : (
                <>
                    {uploadComplete && (
                        <div style={{ color: 'var(--color-accent-blue)', textAlign: 'center', marginBottom: '1rem', fontSize: '0.9rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                            <FileCheck size={16} /> {sessionIds.length} file{sessionIds.length > 1 ? 's' : ''} uploaded successfully
                        </div>
                    )}

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                        {/* Main Income Section */}
                        <SectionCard title="Regular Income">
                            <div className={styles.formGroup}>
                                <label className={styles.label}>Monthly Income (After Tax)</label>
                                <CurrencyInput
                                    className={styles.input}
                                    placeholder="Amount"
                                    value={data.financial?.monthly_income || 0}
                                    onChange={(val) => updateFin('monthly_income', val)}
                                />
                            </div>

                            <div className={styles.formGroup}>
                                <label className={styles.label}>Frequency</label>
                                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                    {['Weekly', 'Bi-Weekly', 'Monthly', 'Irregular'].map(freq => (
                                        <Pill
                                            key={freq}
                                            label={freq}
                                            selected={data.financial?.income_frequency === freq}
                                            onClick={() => updateFin('income_frequency', freq)}
                                        />
                                    ))}
                                </div>
                            </div>
                        </SectionCard>

                        {/* Employment Section */}
                        <SectionCard title="Employment">
                            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                {['Full-time', 'Part-time', 'Freelance', 'Business Owner', 'Student', 'Retired', 'Not Working'].map(type => (
                                    <Pill
                                        key={type}
                                        label={type}
                                        selected={data.financial?.employment_type === type}
                                        onClick={() => updateFin('employment_type', type)}
                                    />
                                ))}
                            </div>
                        </SectionCard>

                        {/* Other Sources Section */}
                        <SectionCard title="Other Sources (Optional)">
                            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                {['Bonus', 'Commission', 'Freelance', 'Rental', 'Family Support', 'Pension', 'Dividends'].map(source => (
                                    <Pill
                                        key={source}
                                        label={source}
                                        selected={(data.financial?.other_income_sources || []).includes(source)}
                                        onClick={() => toggleOtherSource(source)}
                                    />
                                ))}
                            </div>
                        </SectionCard>
                    </div>

                    <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                        <button
                            className={styles.buttonSecondary}
                            onClick={() => {
                                if (showIncomeInput) {
                                    // Just go back to the "upload summary" view
                                    setShowIncomeInput(false);
                                } else if (onBack) {
                                    onBack();
                                }
                            }}
                            style={{ flex: 1 }}
                        >
                            {showIncomeInput ? "← Back" : (backLabel || "← Back")}
                        </button>                    <button className={styles.button} onClick={onNext} style={{ flex: 1, marginTop: 0 }}>
                            Next →
                        </button>
                    </div>
                </>
            )}
        </div>
    );
};

export const FinancialStep2: React.FC<StepProps> = ({ onNext, onBack, data, updateData }) => {
    const updateFin = (key: string, val: any) => {
        updateData('financial', { ...data.financial, [key]: val });
    };

    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Your monthly commitments</h1>
            </div>

            {/* Expenses */}
            <div className={styles.formGroup}>
                <label className={styles.label}>Your usual monthly expenses</label>
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <button
                        className={data.financial?.monthly_expenses_type === 'amount' ? styles.button : styles.buttonSecondary}
                        style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', marginTop: 0 }}
                        onClick={() => updateFin('monthly_expenses_type', 'amount')}
                    >
                        Amount
                    </button>
                    <button
                        className={data.financial?.monthly_expenses_type === 'skip' ? styles.button : styles.buttonSecondary}
                        style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', marginTop: 0 }}
                        onClick={() => updateFin('monthly_expenses_type', 'skip')}
                    >
                        Skip
                    </button>
                </div>
                {data.financial?.monthly_expenses_type === 'amount' && (
                    <CurrencyInput className={styles.input} placeholder="Amount" value={data.financial?.monthly_expenses || 0} onChange={(val) => updateFin('monthly_expenses', val)} />
                )}
            </div>

            {/* Debt */}
            <div className={styles.formGroup}>
                <label className={styles.label}>Any monthly loan or instalment payments?</label>
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <button className={data.financial?.has_debt === 'yes' ? styles.button : styles.buttonSecondary} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', marginTop: 0 }} onClick={() => updateFin('has_debt', 'yes')}>Yes</button>
                    <button className={data.financial?.has_debt === 'no' ? styles.button : styles.buttonSecondary} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', marginTop: 0 }} onClick={() => updateFin('has_debt', 'no')}>No</button>
                    <button className={data.financial?.has_debt === 'skip' ? styles.button : styles.buttonSecondary} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', marginTop: 0 }} onClick={() => updateFin('has_debt', 'skip')}>Skip</button>
                </div>
                {data.financial?.has_debt === 'yes' && (
                    <>
                        <CurrencyInput className={styles.input} placeholder="Monthly Payment Amount" value={data.financial?.monthly_debt_payments || 0} onChange={(val) => updateFin('monthly_debt_payments', val)} style={{ marginBottom: '0.5rem' }} />
                        <CurrencyInput className={styles.input} placeholder="Approx total outstanding? (Optional)" value={data.financial?.total_debt || 0} onChange={(val) => updateFin('total_debt', val)} />
                    </>
                )}
            </div>

            {/* Housing */}
            <div className={styles.formGroup}>
                <label className={styles.label}>Your living situation</label>
                <select className={styles.input} value={data.financial?.housing_status || 'rent'} onChange={(e) => updateFin('housing_status', e.target.value)}>
                    <option value="rent">I rent</option>
                    <option value="own">I own my home</option>
                    <option value="family">I live with family</option>
                    <option value="other">Other</option>
                    <option value="skip">Skip</option>
                </select>
                {data.financial?.housing_status === 'own' && (
                    <CurrencyInput className={styles.input} placeholder="Approx home value? (Optional)" value={data.financial?.housing_value || 0} onChange={(val) => updateFin('housing_value', val)} style={{ marginTop: '0.5rem' }} />
                )}
                {data.financial?.housing_status === 'rent' && (
                    <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        <CurrencyInput
                            className={styles.input}
                            placeholder="Rent Amount"
                            value={data.financial?.rent_amount || 0}
                            onChange={(val) => updateFin('rent_amount', val)}
                        />
                        <select
                            className={styles.input}
                            value={data.financial?.rent_frequency || 'Monthly'}
                            onChange={(e) => updateFin('rent_frequency', e.target.value)}
                        >
                            <option value="Weekly">Weekly</option>
                            <option value="Bi-Weekly">Bi-Weekly</option>
                            <option value="Monthly">Monthly</option>
                        </select>
                    </div>
                )}
            </div>

            {/* Car */}
            <div className={styles.formGroup}>
                <label className={styles.label}>Do you own or lease a car?</label>
                <select className={styles.input} value={data.financial?.car_status || 'no_car'} onChange={(e) => updateFin('car_status', e.target.value)}>
                    <option value="own">Own</option>
                    <option value="lease">Lease/rent</option>
                    <option value="no_car">No car</option>
                    <option value="skip">Skip</option>
                </select>
                {data.financial?.car_status === 'own' && (
                    <CurrencyInput className={styles.input} placeholder="Approx car value? (Optional)" value={data.financial?.car_value || 0} onChange={(val) => updateFin('car_value', val)} style={{ marginTop: '0.5rem' }} />
                )}
                {data.financial?.car_status === 'lease' && (
                    <div style={{ marginTop: '0.5rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                        <CurrencyInput
                            className={styles.input}
                            placeholder="Lease Amount"
                            value={data.financial?.car_lease_amount || 0}
                            onChange={(val) => updateFin('car_lease_amount', val)}
                        />
                        <select
                            className={styles.input}
                            value={data.financial?.car_lease_frequency || 'Monthly'}
                            onChange={(e) => updateFin('car_lease_frequency', e.target.value)}
                        >
                            <option value="Weekly">Weekly</option>
                            <option value="Bi-Weekly">Bi-Weekly</option>
                            <option value="Monthly">Monthly</option>
                        </select>
                    </div>
                )}
            </div>

            {/* Other Assets */}
            <div className={styles.formGroup}>
                <label className={styles.label}>Do you own any other major assets?</label>
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <button className={data.financial?.other_assets_status === 'yes' ? styles.button : styles.buttonSecondary} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', marginTop: 0 }} onClick={() => updateFin('other_assets_status', 'yes')}>Yes</button>
                    <button className={data.financial?.other_assets_status === 'no' ? styles.button : styles.buttonSecondary} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', marginTop: 0 }} onClick={() => updateFin('other_assets_status', 'no')}>No</button>
                    <button className={data.financial?.other_assets_status === 'skip' ? styles.button : styles.buttonSecondary} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', marginTop: 0 }} onClick={() => updateFin('other_assets_status', 'skip')}>Skip</button>
                </div>
                {data.financial?.other_assets_status === 'yes' && (
                    <input type="text" className={styles.input} placeholder="Short description (e.g. Boat, Art)" value={data.financial?.other_assets_description || ''} onChange={(e) => updateFin('other_assets_description', e.target.value)} />
                )}
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                {onBack && (
                    <button
                        className={styles.buttonSecondary}
                        onClick={() => {
                            // When going back to Step 1, ensure we show the input view if we have data
                            // OR if we were in manual mode before
                            if (
                                !!data.financial?.is_manual_mode ||
                                (data.financial?.monthly_income || 0) > 0 ||
                                data.financial?.monthly_income_type === 'range' ||
                                !!data.financial?.onboarding_session_id
                            ) {
                                updateFin('is_manual_mode', true);
                            }
                            onBack();
                        }}
                        style={{ flex: 1 }}
                    >
                        ← Back
                    </button>
                )}
                <button className={styles.button} onClick={onNext} style={{ flex: 1, marginTop: 0 }}>
                    Next →
                </button>
            </div>
        </div>
    );
};

export const FinancialStep3: React.FC<StepProps> = ({ onNext, onBack, data, updateData }) => {
    const updateFin = (key: string, val: any) => {
        updateData('financial', { ...data.financial, [key]: val });
    };

    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Your financial habits</h1>
            </div>

            {/* Fixed Bills */}
            <div className={styles.formGroup}>
                <label className={styles.label}>What are your total monthly fixed bills (rent, utilities, subscriptions)?</label>
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <button className={data.financial?.monthly_bills_type === 'amount' ? styles.button : styles.buttonSecondary} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', marginTop: 0 }} onClick={() => updateFin('monthly_bills_type', 'amount')}>Amount</button>
                    <button className={data.financial?.monthly_bills_type === 'skip' ? styles.button : styles.buttonSecondary} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', marginTop: 0 }} onClick={() => updateFin('monthly_bills_type', 'skip')}>Skip</button>
                </div>
                {data.financial?.monthly_bills_type === 'amount' && (
                    <CurrencyInput className={styles.input} placeholder="Amount" value={data.financial?.monthly_bills || 0} onChange={(val) => updateFin('monthly_bills', val)} />
                )}
            </div>

            {/* Discretionary Spend */}
            <div className={styles.formGroup}>
                <label className={styles.label}>Roughly how much do you spend monthly OUTSIDE of those bills?</label>
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <button className={data.financial?.discretionary_spend_type === 'amount' ? styles.button : styles.buttonSecondary} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', marginTop: 0 }} onClick={() => updateFin('discretionary_spend_type', 'amount')}>Amount</button>
                    <button className={data.financial?.discretionary_spend_type === 'skip' ? styles.button : styles.buttonSecondary} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', marginTop: 0 }} onClick={() => updateFin('discretionary_spend_type', 'skip')}>Skip</button>
                </div>
                {data.financial?.discretionary_spend_type === 'amount' && (
                    <CurrencyInput className={styles.input} placeholder="Ex: Dining, Shopping, Travel" value={data.financial?.discretionary_spend || 0} onChange={(val) => updateFin('discretionary_spend', val)} />
                )}
            </div>

            {/* Savings */}
            <div className={styles.formGroup}>
                <label className={styles.label}>Do you save anything monthly?</label>
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <button className={data.financial?.monthly_savings_type === 'amount' ? styles.button : styles.buttonSecondary} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', marginTop: 0 }} onClick={() => updateFin('monthly_savings_type', 'amount')}>Amount</button>
                    <button className={data.financial?.monthly_savings_type === 'no' ? styles.button : styles.buttonSecondary} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', marginTop: 0 }} onClick={() => updateFin('monthly_savings_type', 'no')}>No</button>
                    <button className={data.financial?.monthly_savings_type === 'skip' ? styles.button : styles.buttonSecondary} style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', marginTop: 0 }} onClick={() => updateFin('monthly_savings_type', 'skip')}>Skip</button>
                </div>
                {data.financial?.monthly_savings_type === 'amount' && (
                    <CurrencyInput className={styles.input} placeholder="Amount" value={data.financial?.monthly_savings || 0} onChange={(val) => updateFin('monthly_savings', val)} />
                )}
            </div>

            {/* Investments */}
            <div className={styles.formGroup}>
                <label className={styles.label}>Do you currently invest?</label>
                <select className={styles.input} value={data.financial?.investments_status || 'no'} onChange={(e) => updateFin('investments_status', e.target.value)}>
                    <option value="yes">Yes</option>
                    <option value="no">No</option>
                    <option value="sometimes">Sometimes</option>
                    <option value="skip">Skip</option>
                </select>
                {(data.financial?.investments_status === 'yes' || data.financial?.investments_status === 'sometimes') && (
                    <>
                        <CurrencyInput className={styles.input} placeholder="Approx total value? (Optional)" value={data.financial?.investments_value || 0} onChange={(val) => updateFin('investments_value', val)} style={{ marginTop: '0.5rem' }} />
                        <input
                            type="text"
                            className={styles.input}
                            placeholder="Where? (Stocks, crypto, etc)"
                            value={(data.financial?.investments_types || []).join(', ')}
                            onChange={(e) => updateFin('investments_types', e.target.value.split(',').map((s: string) => s.trim()))}
                            style={{ marginTop: '0.5rem' }}
                        />
                    </>
                )}
            </div>

            {/* Risk Appetite */}
            <div className={styles.formGroup}>
                <label className={styles.label}>What kind of investor feels most like you?</label>
                <select className={styles.input} value={data.financial?.risk_appetite || 'unsure'} onChange={(e) => updateFin('risk_appetite', e.target.value)}>
                    <option value="conservative">Conservative — prefer stability</option>
                    <option value="balanced">Balanced — some risk when needed</option>
                    <option value="growth">Growth — higher risk for higher return</option>
                    <option value="unsure">I’m not sure</option>
                </select>
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                {onBack && (
                    <button className={styles.buttonSecondary} onClick={onBack} style={{ flex: 1 }}>
                        ← Back
                    </button>
                )}
                <button className={styles.button} onClick={onNext} style={{ flex: 1, marginTop: 0 }}>
                    Build my financial snapshot →
                </button>
            </div>
        </div>
    );
};


export const HealthStep1: React.FC<StepProps> = ({ onNext, onBack, data, updateData }) => {
    const [whoopFiles, setWhoopFiles] = React.useState<FileUploadStatus[]>([]);
    const [connectedApps, setConnectedApps] = React.useState<{ apple: boolean; google: boolean }>({ apple: false, google: false });
    const [connecting, setConnecting] = React.useState<string | null>(null);

    const toggleConnect = async (app: 'apple' | 'google') => {
        if (connectedApps[app]) {
            // Disconnect logic (mock)
            setConnectedApps(prev => ({ ...prev, [app]: false }));
            return;
        }

        setConnecting(app);
        try {
            // 1. Get Auth URL
            const response = await fetch(`/api/health/${app}/auth-url`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) throw new Error('Failed to get auth URL');

            const { url } = await response.json();

            // 2. Open Popup
            const width = 600;
            const height = 700;
            const left = window.screen.width / 2 - width / 2;
            const top = window.screen.height / 2 - height / 2;

            const popup = window.open(
                url,
                `Connect ${app}`,
                `width=${width},height=${height},top=${top},left=${left}`
            );

            // 3. Listen for callback message (from popup)
            const handleMessage = async (event: MessageEvent) => {
                if (event.data?.type === 'HEALTH_AUTH_CODE' && event.data?.provider === app) {
                    const code = event.data.code;
                    console.log('Received auth code:', code);

                    try {
                        const cbResponse = await fetch(`/api/health/${app}/callback`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ code })
                        });

                        if (cbResponse.ok) {
                            setConnectedApps(prev => ({ ...prev, [app]: true }));
                        } else {
                            const errText = await cbResponse.text();
                            console.error('Callback failed:', errText);
                            alert(`Connection failed: ${errText}`);
                        }
                    } catch (e) {
                        console.error("Callback catch:", e);
                        alert("Connection failed");
                    }

                    setConnecting(null);
                    cleanup();
                }
            };

            window.addEventListener('message', handleMessage);

            // 4. Poll for closure (cancellation)
            const timer = setInterval(() => {
                if (popup?.closed) {
                    // If closed without message, it was likely cancelled
                    cleanup();
                    // Just revert loading state if we didn't get success
                    setConnecting(prev => prev === app ? null : prev);
                }
            }, 1000);

            const cleanup = () => {
                window.removeEventListener('message', handleMessage);
                clearInterval(timer);
            };

        } catch (error) {
            console.error('Connection failed:', error);
            alert('Failed to initiate connection.');
            setConnecting(null);
        }
    };

    const handleTrackInterest = async (feature: string) => {
        try {
            await fetch('/api/health/interest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ feature })
            });
            alert(`Thanks! We've noted your interest in ${feature} integration.`);
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Health & Lifestyle</h1>
                <p className={styles.subtitle}>
                    Your health is your greatest asset. Connect your data for personalized insights.
                </p>
            </div>

            {/* App Connections Section */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#334155', marginBottom: '1rem' }}>Connect Apps</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>

                    <div
                        onClick={() => handleTrackInterest('apple_health')}
                        style={{
                            padding: '1rem',
                            borderRadius: '12px',
                            border: '1px solid #e2e8f0',
                            background: '#f8fafc',
                            cursor: 'pointer', // Make clickable
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.75rem',
                            transition: 'all 0.2s',
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.borderColor = '#94a3b8'}
                        onMouseLeave={(e) => e.currentTarget.style.borderColor = '#e2e8f0'}
                    >
                        <div style={{ display: 'flex', color: 'var(--color-accent-red)' }}><Heart size={40} /></div>
                        <div>
                            <div style={{ fontWeight: 600, color: '#64748b' }}>Apple Health</div>
                            <div style={{ fontSize: '0.8rem', color: '#94a3b8', fontStyle: 'italic' }}>
                                Coming Soon
                            </div>
                        </div>
                    </div>

                    {/* Whoop - Interest Only */}
                    <div
                        onClick={() => handleTrackInterest('whoop_integration')}
                        style={{
                            padding: '1rem',
                            borderRadius: '12px',
                            border: '1px solid #e2e8f0',
                            background: '#f8fafc',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.75rem',
                            transition: 'all 0.2s'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.borderColor = '#94a3b8'}
                        onMouseLeave={(e) => e.currentTarget.style.borderColor = '#e2e8f0'}
                    >
                        <div style={{ display: 'flex', color: 'var(--color-accent-orange)' }}><Activity size={40} /></div>
                        <div>
                            <div style={{ fontWeight: 600, color: '#64748b' }}>Whoop</div>
                            <div style={{ fontSize: '0.8rem', color: '#94a3b8', fontStyle: 'italic' }}>
                                Coming Soon
                            </div>
                        </div>
                    </div>

                    {/* Google Fit - Active */}
                    <div
                        onClick={() => toggleConnect('google')}
                        style={{
                            padding: '1rem',
                            borderRadius: '12px',
                            border: `1px solid ${connectedApps.google ? '#60a5fa' : '#e2e8f0'}`,
                            background: connectedApps.google ? '#eff6ff' : '#fff',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.75rem',
                            transition: 'all 0.2s',
                            opacity: connecting && connecting !== 'google' ? 0.5 : 1,
                            pointerEvents: connecting ? 'none' : 'auto'
                        }}
                    >
                        <div style={{ display: 'flex', color: 'var(--color-accent-red)' }}>
                            {connecting === 'google' ? <Loader2 className={styles.spin} size={40} /> : <Heart size={40} />}
                        </div>
                        <div>
                            <div style={{ fontWeight: 600, color: '#1e293b' }}>Google Fit</div>
                            <div style={{ fontSize: '0.8rem', color: connectedApps.google ? '#3b82f6' : '#64748b' }}>
                                {connecting === 'google' ? 'Syncing...' : (connectedApps.google ? 'Connected' : 'Tap to connect')}
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Whoop Upload Section */}
            <div style={{ marginBottom: '2rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#334155', margin: 0 }}>Upload Whoop Report</h3>
                    <span style={{ fontSize: '0.75rem', background: '#e2e8f0', padding: '2px 8px', borderRadius: '12px', color: '#64748b' }}>Coming Soon</span>
                </div>
                <p style={{ fontSize: '0.85rem', color: '#64748b', marginBottom: '1rem' }}>
                    Upload your monthly performance PDF for deeper recovery analysis.
                </p>
                <FileUploadProgress
                    files={whoopFiles}
                    onFilesChange={setWhoopFiles}
                    onComplete={(ids) => console.log('Whoop upload complete', ids)}
                    uploadUrl="/api/onboarding/upload-whoop"
                    title="Upload Whoop Report"
                    description="Drag and drop your monthly PDF here"
                />
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                {onBack && (
                    <button className={styles.buttonSecondary} onClick={onBack} style={{ flex: 1 }}>
                        ← Back
                    </button>
                )}
                <button className={styles.button} onClick={onNext} style={{ flex: 1, marginTop: 0 }}>
                    Next →
                </button>
            </div>
        </div>
    );
}

export const HealthStep2: React.FC<StepProps> = ({ onNext, onBack, data, updateData }) => {

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        let val: any = e.target.value;
        if (e.target.type === 'number') {
            val = val === '' ? 0 : parseFloat(val);
        }
        updateData('health', {
            ...data.health,
            [e.target.name]: val
        });
    };

    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Health & Lifestyle</h1>
                <p className={styles.subtitle}>
                    A few quick questions to complete your profile.
                </p>
            </div>

            {/* A) Sleep Section */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 className={styles.sectionTitle} style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
                    😴 Sleep
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Avg Sleep Hours</label>
                        <select name="sleep_hours" className={styles.input} value={data.health?.sleep_hours || '7-8'} onChange={handleChange}>
                            <option value="<5">&lt; 5 hours</option>
                            <option value="5-6">5–6 hours</option>
                            <option value="6-7">6–7 hours</option>
                            <option value="7-8">7–8 hours</option>
                            <option value="8-9">8–9 hours</option>
                            <option value=">9">&gt; 9 hours</option>
                        </select>
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Sleep Consistency</label>
                        <select name="sleep_consistency" className={styles.input} value={data.health?.sleep_consistency || 'Mostly'} onChange={handleChange}>
                            <option value="Consistent">Consistent</option>
                            <option value="Mostly">Mostly</option>
                            <option value="Not really">Not really</option>
                        </select>
                    </div>
                    <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                        <label className={styles.label}>Do you wake up tired?</label>
                        <select name="wake_tired" className={styles.input} value={data.health?.wake_tired || 'Sometimes'} onChange={handleChange}>
                            <option value="Yes">Yes</option>
                            <option value="Sometimes">Sometimes</option>
                            <option value="No">No</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* B) Activity Section */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 className={styles.sectionTitle} style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
                    🏃 Movement & Activity
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Activity Level</label>
                        <select name="activity_level" className={styles.input} value={data.health?.activity_level || 'Moderate'} onChange={handleChange}>
                            <option value="Sedentary">Sedentary</option>
                            <option value="Lightly active">Lightly active</option>
                            <option value="Moderate">Moderate</option>
                            <option value="High">High</option>
                        </select>
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Primary Activity Type</label>
                        <select name="activity_type" className={styles.input} value={data.health?.activity_type || 'None'} onChange={handleChange}>
                            <option value="Walking">Walking</option>
                            <option value="Running">Running</option>
                            <option value="Gym">Gym</option>
                            <option value="Yoga">Yoga</option>
                            <option value="Sports">Sports</option>
                            <option value="None">None</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* C) Recovery & Stress Section */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 className={styles.sectionTitle} style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
                    🧘 Recovery & Stress
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Stress Level</label>
                        <select name="stress_level" className={styles.input} value={data.health?.stress_level || 'Sometimes'} onChange={handleChange}>
                            <option value="Rarely">Rarely</option>
                            <option value="Sometimes">Sometimes</option>
                            <option value="Often">Often</option>
                            <option value="Almost always">Almost always</option>
                        </select>
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Energy Pattern</label>
                        <select name="energy_pattern" className={styles.input} value={data.health?.energy_pattern || 'Stable'} onChange={handleChange}>
                            <option value="Stable">Stable</option>
                            <option value="Highs & lows">Highs & lows</option>
                            <option value="Afternoon crash">Afternoon crash</option>
                            <option value="Low most days">Low most days</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* D) Nutrition & Habits Section */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 className={styles.sectionTitle} style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
                    🥗 Nutrition & Habits
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                        <label className={styles.label}>Diet Style</label>
                        <select name="diet_style" className={styles.input} value={data.health?.diet_style || 'Balanced'} onChange={handleChange}>
                            <option value="Balanced">Balanced</option>
                            <option value="Mediterranean">Mediterranean</option>
                            <option value="High-carb">High-carb</option>
                            <option value="High-protein">High-protein</option>
                            <option value="Vegetarian">Vegetarian</option>
                            <option value="Vegan">Vegan</option>
                            <option value="Whatever’s available">Whatever’s available</option>
                        </select>
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Water Intake</label>
                        <select name="water_intake" className={styles.input} value={data.health?.water_intake || '1-2L'} onChange={handleChange}>
                            <option value="<1L">&lt; 1L</option>
                            <option value="1-2L">1–2L</option>
                            <option value="2-3L">2–3L</option>
                            <option value="3L+">3L+</option>
                        </select>
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Smoking Pattern</label>
                        <select name="smoking_pattern" className={styles.input} value={data.health?.smoking_pattern || 'Never'} onChange={handleChange}>
                            <option value="Never">Never</option>
                            <option value="Occasionally">Occasionally</option>
                            <option value="Regularly">Regularly</option>
                        </select>
                    </div>
                    <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                        <label className={styles.label}>Alcohol Pattern</label>
                        <select name="alcohol_pattern" className={styles.input} value={data.health?.alcohol_pattern || 'Occasionally'} onChange={handleChange}>
                            <option value="Never">Never</option>
                            <option value="Occasionally">Occasionally</option>
                            <option value="Regularly">Regularly</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* E) Lifestyle Load Section */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 className={styles.sectionTitle} style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
                    ⚖️ Lifestyle Load
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Eating Out</label>
                        <select name="eating_out_frequency" className={styles.input} value={data.health?.eating_out_frequency || 'Rarely'} onChange={handleChange}>
                            <option value="Rarely">Rarely</option>
                            <option value="1-2x week">1–2x week</option>
                            <option value="3-5x week">3–5x week</option>
                            <option value="Daily">Daily</option>
                        </select>
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Takeaway</label>
                        <select name="takeaway_frequency" className={styles.input} value={data.health?.takeaway_frequency || 'Rarely'} onChange={handleChange}>
                            <option value="Rarely">Rarely</option>
                            <option value="1-2x week">1–2x week</option>
                            <option value="3-5x week">3–5x week</option>
                            <option value="Daily">Daily</option>
                        </select>
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Home Cooking</label>
                        <select name="cooking_frequency" className={styles.input} value={data.health?.cooking_frequency || 'Rarely'} onChange={handleChange}>
                            <option value="Rarely">Rarely</option>
                            <option value="1-2x week">1–2x week</option>
                            <option value="3-5x week">3–5x week</option>
                            <option value="Daily">Daily</option>
                        </select>
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Nightlife</label>
                        <select name="nightlife_frequency" className={styles.input} value={data.health?.nightlife_frequency || 'Rarely'} onChange={handleChange}>
                            <option value="Rarely">Rarely</option>
                            <option value="1-2x week">1–2x week</option>
                            <option value="3-5x week">3–5x week</option>
                            <option value="Daily">Daily</option>
                        </select>
                    </div>
                </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                {onBack && (
                    <button className={styles.buttonSecondary} onClick={onBack} style={{ flex: 1 }}>
                        ← Back
                    </button>
                )}
                <button className={styles.button} onClick={onNext} style={{ flex: 1, marginTop: 0 }}>
                    Build my health snapshot →
                </button>
            </div>
        </div>
    );
};


export const ProductivityStep1: React.FC<StepProps> = ({ onNext, onBack, data, updateData }) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        updateData('productivity', { ...data.productivity, [name]: value });
    };

    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Time & Structure</h1>
                <p className={styles.subtitle}>
                    How do you currently manage your days?
                </p>
            </div>

            {/* A) Work & Structure */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 className={styles.sectionTitle} style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
                    📅 Basic Structure
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Work Status</label>
                        <select name="work_status" className={styles.input} value={data.productivity?.work_status || 'Full-time'} onChange={handleChange}>
                            <option value="Full-time">Full-time</option>
                            <option value="Part-time">Part-time</option>
                            <option value="Freelancer">Freelancer</option>
                            <option value="Business owner">Business owner</option>
                            <option value="Student">Student</option>
                            <option value="Not working">Not working</option>
                        </select>
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Weekly Work Hours</label>
                        <select name="work_hours_per_week" className={styles.input} value={data.productivity?.work_hours_per_week || '40'} onChange={handleChange}>
                            <option value="<20">&lt; 20 hours</option>
                            <option value="20-35">20–35 hours</option>
                            <option value="35-45">35–45 hours</option>
                            <option value="45-55">45–55 hours</option>
                            <option value="55+">55+ hours</option>
                        </select>
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Digital Calendar?</label>
                        <select name="uses_digital_calendar" className={styles.input} value={data.productivity?.uses_digital_calendar || 'No'} onChange={handleChange}>
                            <option value="Yes - Google">Yes - Google</option>
                            <option value="Yes - Outlook">Yes - Outlook</option>
                            <option value="Yes - Apple">Yes - Apple</option>
                            <option value="Yes - Other">Yes - Other</option>
                            <option value="No">No</option>
                        </select>
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Daily Commute</label>
                        <select name="commute_duration" className={styles.input} value={data.productivity?.commute_duration || '<15 min'} onChange={handleChange}>
                            <option value="No commute">No commute</option>
                            <option value="<15 min">&lt; 15 min</option>
                            <option value="15-30 min">15–30 min</option>
                            <option value="30-60 min">30–60 min</option>
                            <option value="60+">60+ min</option>
                        </select>
                    </div>
                </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                {onBack && (
                    <button className={styles.buttonSecondary} onClick={onBack} style={{ flex: 1 }}>
                        ← Back
                    </button>
                )}
                <button className={styles.button} onClick={onNext} style={{ flex: 1, marginTop: 0 }}>
                    Next →
                </button>
            </div>
        </div>
    );
}

export const ProductivityStep2: React.FC<StepProps> = ({ onNext, onBack, data, updateData }) => {
    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        updateData('productivity', { ...data.productivity, [name]: value });
    };

    const handleDrainChange = (drain: string) => {
        const currentDrains = data.productivity?.main_time_drains || [];
        let newDrains;
        if (currentDrains.includes(drain)) {
            newDrains = currentDrains.filter((d: string) => d !== drain);
        } else {
            newDrains = [...currentDrains, drain];
        }
        updateData('productivity', { ...data.productivity, main_time_drains: newDrains });
    };

    const drainOptions = [
        "Commuting", "Emails", "Meetings", "Kids schedules", "Errands",
        "Bills & admin", "Last-minute tasks", "Finding services", "Not sure"
    ];

    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Time & Structure</h1>
                <p className={styles.subtitle}>
                    Let's dig a little deeper into your time habits.
                </p>
            </div>

            {/* B) Daily Time Use */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 className={styles.sectionTitle} style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
                    ⏳ Time Use
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Meals & House (Daily)</label>
                        <select name="time_meals_house_daily" className={styles.input} value={data.productivity?.time_meals_house_daily || '1-2 hours'} onChange={handleChange}>
                            <option value="<30 min">&lt; 30 min</option>
                            <option value="30-60 min">30–60 min</option>
                            <option value="1-2 hours">1–2 hours</option>
                            <option value="2+ hours">2+ hours</option>
                        </select>
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Admin & Errands (Weekly)</label>
                        <select name="time_admin_weekly" className={styles.input} value={data.productivity?.time_admin_weekly || '1-3 hours'} onChange={handleChange}>
                            <option value="<1 hour">&lt; 1 hour</option>
                            <option value="1-3 hours">1–3 hours</option>
                            <option value="3-5 hours">3–5 hours</option>
                            <option value="5+ hours">5+ hours</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* C) Time Drains */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 className={styles.sectionTitle} style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
                    ⚠️ Top Time Drains
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {drainOptions.map(option => (
                        <div
                            key={option}
                            onClick={() => handleDrainChange(option)}
                            style={{
                                padding: '0.5rem 1rem',
                                borderRadius: '20px',
                                fontSize: '0.85rem',
                                cursor: 'pointer',
                                background: (data.productivity?.main_time_drains || []).includes(option) ? '#a78bfa' : '#f1f5f9',
                                color: (data.productivity?.main_time_drains || []).includes(option) ? '#fff' : '#475569',
                                border: '1px solid transparent',
                                transition: 'all 0.2s'
                            }}
                        >
                            {option}
                        </div>
                    ))}
                </div>
            </div>

            {/* D) Style & Pressure */}
            <div style={{ marginBottom: '2rem' }}>
                <h3 className={styles.sectionTitle} style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '0.5rem', marginBottom: '1rem' }}>
                    🧠 Style & Pressure
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Routine Style</label>
                        <select name="routine_style" className={styles.input} value={data.productivity?.routine_style || 'I try'} onChange={handleChange}>
                            <option value="I follow a routine">I follow a routine</option>
                            <option value="I try">I try</option>
                            <option value="Not really">Not really</option>
                            <option value="I’m spontaneous">I’m spontaneous</option>
                        </select>
                    </div>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>Task Planning</label>
                        <select name="task_style" className={styles.input} value={data.productivity?.task_style || 'I react to what\'s urgent'} onChange={handleChange}>
                            <option value="I plan ahead">I plan ahead</option>
                            <option value="I plan but things shift">I plan but things shift</option>
                            <option value="I react to what’s urgent">I react to what’s urgent</option>
                            <option value="I go with the flow">I go with the flow</option>
                        </select>
                    </div>
                    <div className={styles.formGroup} style={{ gridColumn: 'span 2' }}>
                        <label className={styles.label}>Do you feel overwhelmed by time?</label>
                        <select name="time_overwhelm_level" className={styles.input} value={data.productivity?.time_overwhelm_level || 'Sometimes'} onChange={handleChange}>
                            <option value="Rarely">Rarely</option>
                            <option value="Sometimes">Sometimes</option>
                            <option value="Often">Often</option>
                            <option value="Almost always">Almost always</option>
                        </select>
                    </div>
                </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                {onBack && (
                    <button className={styles.buttonSecondary} onClick={onBack} style={{ flex: 1 }}>
                        ← Back
                    </button>
                )}
                <button className={styles.button} onClick={onNext} style={{ flex: 1, marginTop: 0 }}>
                    Next Step
                </button>
            </div>
        </div>
    );
};


export const CalendarStep: React.FC<StepProps> = ({ onNext, onBack }) => {
    const [connecting, setConnecting] = React.useState<string | null>(null);
    const [connected, setConnected] = React.useState(false);

    const handleConnect = async () => {
        setConnecting('google');
        try {
            // 1. Get Auth URL
            const response = await fetch('/api/calendar/google/auth-url');
            if (!response.ok) throw new Error('Failed to get auth URL');
            const data = await response.json();
            const url = data.url;

            // 2. Open Popup
            const width = 600;
            const height = 700;
            const left = window.screen.width / 2 - width / 2;
            const top = window.screen.height / 2 - height / 2;

            const popup = window.open(
                url,
                'Connect Google Calendar',
                `width=${width},height=${height},top=${top},left=${left}`
            );

            // 3. Listen for callback
            const handleMessage = async (event: MessageEvent) => {
                if (event.data?.type === 'CALENDAR_AUTH_CODE') {
                    const code = event.data.code;
                    console.log('Received calendar auth code');

                    try {
                        const cbResponse = await fetch('/api/calendar/google/callback', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ code })
                        });

                        if (cbResponse.ok) {
                            setConnected(true);
                        } else {
                            alert('Calendar connection failed.');
                        }
                    } catch (e) {
                        console.error(e);
                        alert('Calendar connection error.');
                    }

                    setConnecting(null);
                    cleanup();
                }
            };

            window.addEventListener('message', handleMessage);

            const timer = setInterval(() => {
                if (popup?.closed) {
                    cleanup();
                    setConnecting(null);
                }
            }, 1000);

            const cleanup = () => {
                window.removeEventListener('message', handleMessage);
                clearInterval(timer);
            };

        } catch (error) {
            console.error(error);
            alert('Failed to start calendar connection');
            setConnecting(null);
        }
    };

    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Connect Calendar</h1>
                <p className={styles.subtitle}>
                    Sync your schedule for automatic load balancing.
                </p>
            </div>

            <div style={{ margin: '2rem 0' }}>
                <div
                    onClick={handleConnect}
                    style={{
                        padding: '1.5rem',
                        border: `2px solid ${connected ? '#a78bfa' : '#e2e8f0'}`,
                        borderRadius: '12px',
                        background: connected ? '#f5f3ff' : 'white',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        transition: 'all 0.2s'
                    }}
                >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <div style={{ display: 'flex', color: 'var(--color-accent-blue)' }}><Calendar size={40} /></div>
                        <div>
                            <div style={{ fontWeight: 600, color: '#1e293b' }}>Google Calendar</div>
                            <div style={{ fontSize: '0.8rem', color: connected ? '#7c3aed' : '#64748b' }}>
                                {connecting === 'google' ? 'Connecting...' : (connected ? 'Connected' : 'Tap to connect')}
                            </div>
                        </div>
                    </div>
                    {connected && <div style={{ fontSize: '1.2rem', display: 'flex' }}><Check size={24} /></div>}
                </div>

                <div style={{ marginTop: '2rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                        <h3 style={{ fontSize: '1rem', fontWeight: 600, color: '#334155', margin: 0 }}>Upload Work Calendar</h3>
                        <span style={{ fontSize: '0.75rem', background: '#e2e8f0', padding: '2px 8px', borderRadius: '12px', color: '#64748b' }}>Beta</span>
                    </div>

                    <FileUploadProgress
                        files={[]}
                        onFilesChange={() => { }}
                        onComplete={() => { }}
                        uploadUrl="/api/time/calendar/upload"
                        title="Upload Weekly View"
                        description="Upload a screenshot/PDF of your busy week"
                    />

                    <div style={{ marginTop: '1rem', textAlign: 'center' }}>
                        <button
                            className={styles.buttonSecondary}
                            onClick={() => console.log("Skipped upload")} // Logic handled by not uploading
                            style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}
                        >
                            I don't have a snapshot handy
                        </button>
                    </div>
                </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                {onBack && (
                    <button className={styles.buttonSecondary} onClick={onBack} style={{ flex: 1 }}>
                        ← Back
                    </button>
                )}
                <button className={styles.button} onClick={onNext} style={{ flex: 1, marginTop: 0 }}>
                    Start Chatting →
                </button>
            </div>
        </div>
    );
};

export const SignupStep: React.FC<StepProps> = ({ onNext, onSocialSuccess, onBack, data, updateData }) => {
    const [confirmPassword, setConfirmPassword] = React.useState('');
    const [passwordError, setPasswordError] = React.useState<string>('');

    const calculateStrength = (pwd: string) => {
        if (!pwd) return 0;
        let score = 0;
        if (pwd.length > 7) score++; // Length > 7
        if (/[A-Z]/.test(pwd)) score++; // Has Uppercase
        if (/[0-9]/.test(pwd)) score++; // Has Number
        if (/[^A-Za-z0-9]/.test(pwd)) score++; // Has Special Char
        return score;
    };

    const strength = calculateStrength(data.password || '');
    const strengthLabels = ['Weak', 'Fair', 'Good', 'Strong'];
    const strengthColors = ['#e2e8f0', '#ef4444', '#f59e0b', '#10b981'];

    const handleSignup = () => {
        if (!data.email || !data.email.includes('@')) {
            setPasswordError("Please enter a valid email.");
            return;
        }
        if (!data.password || data.password.length < 6) {
            setPasswordError("Password must be at least 6 characters.");
            return;
        }
        if (data.password !== confirmPassword) {
            setPasswordError("Passwords do not match.");
            return;
        }
        setPasswordError("");
        onNext(); // This triggers handleSignup in parent
    };

    const handleSocialLogin = async (provider: string) => {
        if (provider === 'facebook') {
            alert("Facebook login coming soon.");
            return;
        }

        try {
            // 1. Get Auth URL
            const response = await fetch('/api/auth/google/url');
            if (!response.ok) throw new Error('Failed to get auth URL');
            const data = await response.json();

            // 2. Popup
            const width = 500;
            const height = 600;
            const left = window.screen.width / 2 - width / 2;
            const top = window.screen.height / 2 - height / 2;

            const popup = window.open(
                data.url,
                'Google Login',
                `width=${width},height=${height},top=${top},left=${left}`
            );

            // 3. Listener
            const handleMessage = async (event: MessageEvent) => {
                if (event.data?.type === 'SOCIAL_AUTH_CODE' && event.data?.provider === 'google') {
                    const code = event.data.code;

                    try {
                        const cbResponse = await fetch('/api/auth/google/callback', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ code })
                        });

                        if (cbResponse.ok) {
                            const userData = await cbResponse.json();
                            // Pre-fill data or move next
                            updateData('email', userData.email);
                            updateData('name', userData.name || '');
                            if (onSocialSuccess && userData.user_id) {
                                onSocialSuccess(userData.user_id);
                            } else {
                                onNext();
                            }
                        } else {
                            alert("Login failed");
                        }
                    } catch (e) {
                        console.error(e);
                        alert("Login error");
                    }
                    cleanup();
                }
            };

            window.addEventListener('message', handleMessage);
            const timer = setInterval(() => {
                if (popup?.closed) { cleanup(); }
            }, 1000);

            const cleanup = () => {
                window.removeEventListener('message', handleMessage);
                clearInterval(timer);
            };

        } catch (e: any) {
            console.error(e);
            alert("Could not start login: " + (e.message || "Unknown error"));
        }
    }

    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Create your HELM Profile</h1>
                <p className={styles.subtitle}>
                    Save your data and get your personalized scores.
                </p>
            </div>

            <div className={styles.formGroup} style={{ marginBottom: '2rem' }}>
                <label className={styles.label}>Email Address</label>
                <input
                    type="email"
                    className={styles.input}
                    placeholder="you@example.com"
                    value={data.email || ''}
                    onChange={(e) => updateData('email', e.target.value)}
                />
            </div>

            <div className={styles.formGroup} style={{ marginBottom: '1rem' }}>
                <label className={styles.label}>Password</label>
                <input
                    type="password"
                    className={styles.input}
                    placeholder="Create a password"
                    value={data.password || ''}
                    onChange={(e) => updateData('password', e.target.value)}
                />
                {data.password && (
                    <div style={{ marginTop: '0.5rem', display: 'flex', gap: '4px', height: '4px' }}>
                        {[0, 1, 2, 3].map(i => (
                            <div key={i} style={{ flex: 1, background: i < strength ? strengthColors[Math.min(Math.max(0, strength - 1), 3)] : '#e2e8f0', borderRadius: '2px', transition: 'background 0.3s' }} />
                        ))}
                    </div>
                )}
            </div>

            <div className={styles.formGroup} style={{ marginBottom: '1rem' }}>
                <label className={styles.label}>Confirm Password</label>
                <input
                    type="password"
                    className={styles.input}
                    placeholder="Confirm password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                />
            </div>

            {passwordError && <div style={{ color: '#ef4444', fontSize: '0.9rem', marginBottom: '1rem' }}>{passwordError}</div>}

            <div style={{ textAlign: 'right', marginBottom: '2rem' }}>
                <a href="#" style={{ fontSize: '0.9rem', color: '#6366f1', textDecoration: 'none' }} onClick={(e) => { e.preventDefault(); alert("Forgot Password not implemented yet."); }}>Forgot Password?</a>
            </div>

            <div style={{ display: 'flex', gap: '1rem' }}>
                {onBack && (
                    <button
                        className={styles.buttonSecondary}
                        onClick={onBack}
                        style={{ flex: 1 }}
                    >
                        ← Back
                    </button>
                )}
                <button
                    className={styles.button}
                    onClick={handleSignup}
                    style={{ flex: 1, marginTop: 0 }}
                >
                    Create Account
                </button>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', margin: '2rem 0', color: '#94a3b8' }}>
                <div style={{ flex: 1, height: '1px', background: '#e2e8f0' }}></div>
                <span style={{ padding: '0 1rem', fontSize: '0.9rem' }}>or continue with</span>
                <div style={{ flex: 1, height: '1px', background: '#e2e8f0' }}></div>
            </div>

            <div style={{ display: 'flex', gap: '1rem' }}>
                <button
                    onClick={() => handleSocialLogin('google')}
                    style={{
                        flex: 1,
                        padding: '0.75rem',
                        borderRadius: '12px',
                        border: '1px solid #e2e8f0',
                        background: 'white',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.5rem',
                        fontWeight: 500,
                        color: '#334155'
                    }}
                >
                    <span style={{ fontSize: '1.2rem' }}>G</span> Google
                </button>
                <button
                    disabled
                    style={{
                        flex: 1,
                        padding: '0.75rem',
                        borderRadius: '12px',
                        border: '1px solid #e2e8f0',
                        background: '#f8fafc',
                        cursor: 'not-allowed',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '0.5rem',
                        fontWeight: 500,
                        color: '#94a3b8',
                        opacity: 0.7
                    }}
                >
                    <span style={{ fontSize: '1.2rem' }}>f</span> Facebook <span style={{ color: '#cbd5e1', fontSize: '0.9em', fontWeight: 400 }}>(Coming Soon)</span>
                </button>
            </div>
            <p style={{ textAlign: 'center', fontSize: '0.8rem', color: '#94a3b8', marginTop: '2rem' }}>
                By creating an account, you agree to our Terms of Service and Privacy Policy.
            </p>
        </div >
    );
};

export const ProcessingStep: React.FC = () => {
    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Analyzing Data...</h1>
                <p className={styles.subtitle}>
                    Constructing your HELM Pulse Profile.
                </p>
            </div>
            <div style={{ display: 'flex', justifyContent: 'center', margin: '2rem 0' }}>
                <div style={{
                    width: '40px',
                    height: '40px',
                    border: '3px solid rgba(255,255,255,0.1)',
                    borderTopColor: '#60a5fa',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                }} />
                <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
            </div>
        </div>
    );
};

interface ResultsProps {
    indices: {
        financial: number;
        health: number;
        productivity: number;
    };
    onComplete: () => void;
    onBack: () => void;
}

export const ResultsStep: React.FC<ResultsProps> = ({ indices, onComplete, onBack }) => {
    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Your HELM Profile</h1>
                <p className={styles.subtitle}>
                    Here is your starting baseline. We'll help you optimize these scores.
                </p>
            </div>

            <div className={styles.grid}>
                <div className={styles.metricCard}>
                    <div className={styles.metricLabel}>Financial Score</div>
                    <div className={styles.metricValue} style={{ color: 'var(--color-accent-blue)' }}>
                        {indices.financial}
                    </div>
                </div>
                <div className={styles.metricCard}>
                    <div className={styles.metricLabel}>Health Score</div>
                    <div className={styles.metricValue} style={{ color: 'var(--color-accent-blue)' }}>
                        {indices.health}
                    </div>
                </div>
                <div className={styles.metricCard}>
                    <div className={styles.metricLabel}>Productivity Score</div>
                    <div className={styles.metricValue} style={{ color: 'var(--text-primary)' }}>
                        {indices.productivity}
                    </div>
                </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button className={styles.buttonSecondary} onClick={onBack} style={{ flex: 1 }}>
                    ← Back
                </button>
                <button className={styles.button} onClick={onComplete} style={{ flex: 1, marginTop: 0 }}>
                    Go to Dashboard
                </button>
            </div>
        </div>
    );
};

export const FinancialScoreStep: React.FC<{ score: number; subscores?: any; onNext: () => void; onBack: () => void; loading: boolean; error?: string }> = ({ score, subscores, onNext, onBack, loading, error }) => {
    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Your Financial Pulse</h1>
                <p className={styles.subtitle}>
                    Based on what you've shared, here is your preliminary Financial Wellbeing Score.
                </p>
            </div>

            {loading ? (
                <div style={{ display: 'flex', justifyContent: 'center', margin: '3rem 0' }}>
                    <div style={{
                        width: '40px',
                        height: '40px',
                        border: '3px solid rgba(255,255,255,0.1)',
                        borderTopColor: '#60a5fa',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                    }} />
                    <style>{`
              @keyframes spin {
                to { transform: rotate(360deg); }
              }
            `}</style>
                </div>
            ) : error ? (
                <div style={{ color: 'red', textAlign: 'center', margin: '2rem 0' }}>
                    <p>Error calculating score:</p>
                    <p>{error}</p>
                </div>
            ) : (
                <>
                    <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        margin: '2rem 0'
                    }}>
                        <div style={{
                            width: '120px',
                            height: '120px',
                            borderRadius: '50%',
                            background: 'conic-gradient(#60a5fa 0% 0%, #e2e8f0 0% 100%)', // Placeholder for actual progress
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            position: 'relative'
                        }}>
                            <div style={{
                                width: '100px',
                                height: '100px',
                                borderRadius: '50%',
                                background: '#fff',
                                display: 'flex',
                                flexDirection: 'column',
                                justifyContent: 'center',
                                alignItems: 'center'
                            }}>
                                <span style={{ fontSize: '2rem', fontWeight: 700, color: '#1e293b' }}>{score}</span>
                                <span style={{ fontSize: '0.8rem', color: '#64748b' }}>/ 100</span>
                            </div>
                        </div>
                    </div>

                    {subscores && (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
                            {Object.entries(subscores).map(([key, value]: [string, any]) => {
                                const maxScores: Record<string, number> = {
                                    income_stability: 15,
                                    burn_rate: 15,
                                    savings_momentum: 15,
                                    debt_stress: 15,
                                    recurring_commitments: 10,
                                    spending_stability: 10,
                                    liquidity_cushion: 10,
                                    risk_indicators: 10
                                };
                                const maxVal = maxScores[key] || 10;

                                return (
                                    <div key={key} style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                                        <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'capitalize', marginBottom: '0.25rem' }}>
                                            {key.replace(/_/g, ' ')}
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
                                            <span style={{ fontSize: '1rem', fontWeight: 600, color: '#334155' }}>
                                                {value}
                                            </span>
                                            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                                                / {maxVal}
                                            </span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    <div style={{ textAlign: 'center', color: '#64748b', fontSize: '0.9rem', marginBottom: '2rem' }}>
                        This is just the start. Connect your accounts to get a real-time, 360° view.
                    </div>
                </>
            )}

            <div style={{ display: 'flex', gap: '1rem' }}>
                <button className={styles.buttonSecondary} onClick={onBack} style={{ flex: 1 }}>
                    ← Back
                </button>
                <button className={styles.button} onClick={onNext} style={{ flex: 1, marginTop: 0 }} disabled={loading || !!error}>
                    Next: Health →
                </button>
            </div>
        </div>
    );
};

export const HealthScoreStep: React.FC<{ score: number; subscores?: any; onNext: () => void; onBack: () => void; loading: boolean; error?: string }> = ({ score, subscores, onNext, onBack, loading, error }) => {
    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Your Health Snapshot</h1>
                <p className={styles.subtitle}>
                    Based on your inputs and connected data, here is your preliminary Health Score.
                </p>
            </div>

            {loading ? (
                <div style={{ display: 'flex', justifyContent: 'center', margin: '3rem 0' }}>
                    <div style={{
                        width: '40px',
                        height: '40px',
                        border: '3px solid rgba(255,255,255,0.1)',
                        borderTopColor: '#34d399',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                    }} />
                    <style>{`
              @keyframes spin {
                to { transform: rotate(360deg); }
              }
            `}</style>
                </div>
            ) : error ? (
                <div style={{ color: 'red', textAlign: 'center', margin: '2rem 0' }}>
                    <p>Error calculating score:</p>
                    <p>{error}</p>
                </div>
            ) : (
                <>
                    <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        margin: '2rem 0'
                    }}>
                        <div style={{
                            width: '120px',
                            height: '120px',
                            borderRadius: '50%',
                            background: 'conic-gradient(#34d399 0% 0%, #e2e8f0 0% 100%)',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            position: 'relative'
                        }}>
                            <div style={{
                                width: '100px',
                                height: '100px',
                                borderRadius: '50%',
                                background: '#fff',
                                display: 'flex',
                                flexDirection: 'column',
                                justifyContent: 'center',
                                alignItems: 'center'
                            }}>
                                <span style={{ fontSize: '2rem', fontWeight: 700, color: '#1e293b' }}>{score}</span>
                                <span style={{ fontSize: '0.8rem', color: '#64748b' }}>/ 100</span>
                            </div>
                        </div>
                    </div>

                    {subscores && (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
                            {Object.entries(subscores).map(([key, value]: [string, any]) => {
                                const maxVal = value?.max || (key === 'lifestyle' ? 10 : (key === 'recovery' || key === 'nutrition' ? 20 : 25));
                                const scoreVal = (value && typeof value === 'object') ? value.score : value;

                                return (
                                    <div key={key} style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                                        <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'capitalize', marginBottom: '0.25rem' }}>
                                            {key}
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
                                            <span style={{ fontSize: '1rem', fontWeight: 600, color: '#334155' }}>
                                                {scoreVal}
                                            </span>
                                            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                                                / {maxVal}
                                            </span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    <div style={{ textAlign: 'center', color: '#64748b', fontSize: '0.9rem', marginBottom: '2rem' }}>
                        Connect more devices (like Whoop or Apple Health) to improve the accuracy of this score.
                    </div>
                </>
            )}

            <div style={{ display: 'flex', gap: '1rem' }}>
                <button className={styles.buttonSecondary} onClick={onBack} style={{ flex: 1 }}>
                    ← Back
                </button>
                <button className={styles.button} onClick={onNext} style={{ flex: 1, marginTop: 0 }} disabled={loading || !!error}>
                    Next: Productivity →
                </button>
            </div>
        </div>
    );
};

export const TimeScoreStep: React.FC<{ score: number; subscores?: any; onNext: () => void; onBack: () => void; loading: boolean; error?: string }> = ({ score, subscores, onNext, onBack, loading, error }) => {
    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Productivity Pulse</h1>
                <p className={styles.subtitle}>
                    A check-up on your time structure and load.
                </p>
            </div>

            {loading ? (
                <div style={{ display: 'flex', justifyContent: 'center', margin: '3rem 0' }}>
                    <div style={{
                        width: '40px',
                        height: '40px',
                        border: '3px solid rgba(255,255,255,0.1)',
                        borderTopColor: '#a78bfa',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                    }} />
                    <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
                </div>
            ) : error ? (
                <div style={{ color: 'red', textAlign: 'center', margin: '2rem 0' }}>
                    <p>Error: {error}</p>
                </div>
            ) : (
                <>
                    <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        margin: '2rem 0'
                    }}>
                        <div style={{
                            width: '120px',
                            height: '120px',
                            borderRadius: '50%',
                            background: 'conic-gradient(#a78bfa 0% 0%, #e2e8f0 0% 100%)',
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            position: 'relative'
                        }}>
                            <div style={{
                                width: '100px',
                                height: '100px',
                                borderRadius: '50%',
                                background: '#fff',
                                display: 'flex',
                                flexDirection: 'column',
                                justifyContent: 'center',
                                alignItems: 'center'
                            }}>
                                <span style={{ fontSize: '2rem', fontWeight: 700, color: '#1e293b' }}>{score}</span>
                                <span style={{ fontSize: '0.8rem', color: '#64748b' }}>/ 100</span>
                            </div>
                        </div>
                    </div>

                    {subscores && (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
                            {Object.entries(subscores).map(([key, value]: [string, any]) => {
                                const maxVal = value.max || 10;
                                const val = value.score || value; // handle object or primitive

                                return (
                                    <div key={key} style={{ background: '#f8fafc', padding: '0.75rem', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                                        <div style={{ fontSize: '0.75rem', color: '#64748b', textTransform: 'capitalize', marginBottom: '0.25rem' }}>
                                            {key.replace(/_/g, ' ')}
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.25rem' }}>
                                            <span style={{ fontSize: '1rem', fontWeight: 600, color: '#334155' }}>
                                                {val}
                                            </span>
                                            <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                                                / {maxVal}
                                            </span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </>
            )}

            <div style={{ display: 'flex', gap: '1rem' }}>
                <button className={styles.buttonSecondary} onClick={onBack} style={{ flex: 1 }}>
                    ← Back
                </button>
                <button className={styles.button} onClick={onNext} style={{ flex: 1, marginTop: 0 }} disabled={loading || !!error}>
                    Finish Setup →
                </button>
            </div>
        </div>
    );
};

export interface FocusSelectionStepProps extends StepProps {
    onSelectFocus: (focus: 'financial' | 'health' | 'productivity') => void;
}

export const FocusSelectionStep: React.FC<FocusSelectionStepProps> = ({ onBack, onSelectFocus }) => {
    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>What matters most right now?</h1>
                <p className={styles.subtitle}>
                    We'll adapt the experience to your priority.
                    <br />
                    <span style={{ fontWeight: 500, color: 'var(--color-accent-blue)', display: 'block', marginTop: '0.5rem' }}>
                        We’ll start here. You can fill in the rest later.
                    </span>
                </p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div
                    onClick={() => onSelectFocus('financial')}
                    style={{
                        padding: '1.5rem',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--border-color)',
                        background: 'var(--bg-surface)',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '1rem',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--color-accent-blue)'}
                    onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border-color)'}
                >
                    <div style={{ fontSize: '2rem' }}>💰</div>
                    <div>
                        <div style={{ fontWeight: 600, fontSize: '1.1rem', color: 'var(--text-primary)' }}>Stabilize Finances</div>
                        <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>I want to see my runway and stop stressing about money.</div>
                    </div>
                </div>

                <div
                    onClick={() => onSelectFocus('health')}
                    style={{
                        padding: '1.5rem',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--border-color)',
                        background: 'var(--bg-surface)',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '1rem',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--color-accent-red)'}
                    onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border-color)'}
                >
                    <div style={{ fontSize: '2rem' }}>🔋</div>
                    <div>
                        <div style={{ fontWeight: 600, fontSize: '1.1rem', color: 'var(--text-primary)' }}>Recover Energy</div>
                        <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>I'm running on empty and need to get back on track.</div>
                    </div>
                </div>

                <div
                    onClick={() => onSelectFocus('productivity')}
                    style={{
                        padding: '1.5rem',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--border-color)',
                        background: 'var(--bg-surface)',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '1rem',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--color-accent-blue)'}
                    onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border-color)'}
                >
                    <div style={{ fontSize: '2rem' }}>⚡</div>
                    <div>
                        <div style={{ fontWeight: 600, fontSize: '1.1rem', color: 'var(--text-primary)' }}>Execute & Focus</div>
                        <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>I need to organize my time and get things done.</div>
                    </div>
                </div>
            </div>

            <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'center' }}>
                {onBack && (
                    <button
                        className={styles.buttonSecondary}
                        onClick={onBack}
                        style={{ border: 'none', background: 'transparent' }}
                    >
                        Log Out
                    </button>
                )}
            </div>
        </div>
    );
};

export const QuickFinancialStep: React.FC<StepProps> = ({ onNext, data, updateData }) => {
    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Quick Financial Check</h1>
                <p className={styles.subtitle}>
                    Just a couple of quick questions so we don’t give bad advice.
                </p>
            </div>
            <div className={styles.formGroup}>
                <label className={styles.label}>Monthly Income</label>
                <select
                    className={styles.input}
                    value={data.financial?.monthly_income_type === 'range' ? data.financial?.monthly_income : ''}
                    onChange={(e) => {
                        updateData('financial', { ...data.financial, monthly_income_type: 'range', monthly_income: e.target.value });
                    }}
                >
                    <option value="">Select range...</option>
                    <option value="0-3000">$0 - $3,000</option>
                    <option value="3000-7000">$3,000 - $7,000</option>
                    <option value="7000-12000">$7,000 - $12,000</option>
                    <option value="12000+">$12,000+</option>
                </select>
            </div>
            <div className={styles.formGroup}>
                <label className={styles.label}>Do you have debt?</label>
                <select
                    className={styles.input}
                    value={data.financial?.has_debt || 'no'}
                    onChange={(e) => updateData('financial', { ...data.financial, has_debt: e.target.value })}
                >
                    <option value="no">No</option>
                    <option value="yes">Yes</option>
                </select>
            </div>
            <div className={styles.formGroup}>
                <label className={styles.label}>Spending Comfort</label>
                <select
                    className={styles.input}
                    value={data.financial?.risk_appetite || 'unsure'} // Reusing risk_appetite for now
                    onChange={(e) => updateData('financial', { ...data.financial, risk_appetite: e.target.value })}
                >
                    <option value="unsure">I'm just getting by</option>
                    <option value="conservative">I'm comfortable</option>
                    <option value="aggressive">I have plenty of room</option>
                </select>
            </div>
            <button className={styles.button} onClick={onNext}>Next →</button>
        </div>
    );
};

export const QuickHealthStep: React.FC<StepProps> = ({ onNext, data, updateData }) => {
    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Quick Health Check</h1>
                <p className={styles.subtitle}>
                    Just a couple of quick questions so we don’t give bad advice.
                </p>
            </div>
            <div className={styles.formGroup}>
                <label className={styles.label}>Average Sleep</label>
                <select
                    className={styles.input}
                    value={data.health?.sleep_hours || '7-8'}
                    onChange={(e) => updateData('health', { ...data.health, sleep_hours: e.target.value })}
                >
                    <option value="<5">Less than 5h</option>
                    <option value="5-6">5-6h</option>
                    <option value="6-7">6-7h</option>
                    <option value="7-8">7-8h</option>
                    <option value="8+">8h+</option>
                </select>
            </div>
            <div className={styles.formGroup}>
                <label className={styles.label}>Energy Levels</label>
                <select
                    className={styles.input}
                    value={data.health?.energy_pattern || 'Stable'}
                    onChange={(e) => updateData('health', { ...data.health, energy_pattern: e.target.value })}
                >
                    <option value="Stable">Consistent</option>
                    <option value="Afternoon Slump">Afternoon Slump</option>
                    <option value="Low all day">Low all day</option>
                    <option value="Hyperactive">Hyperactive</option>
                </select>
            </div>
            <button className={styles.button} onClick={onNext}>Next →</button>
        </div>
    );
};

export const QuickProductivityStep: React.FC<StepProps> = ({ onNext, data, updateData }) => {
    return (
        <div className={styles.stepContainer}>
            <div className={styles.header}>
                <h1 className={styles.title}>Quick Productivity Check</h1>
                <p className={styles.subtitle}>
                    Just a couple of quick questions so we don’t give bad advice.
                </p>
            </div>
            <div className={styles.formGroup}>
                <label className={styles.label}>Work Type</label>
                <select
                    className={styles.input}
                    value={data.productivity?.work_status || 'Full-time'}
                    onChange={(e) => updateData('productivity', { ...data.productivity, work_status: e.target.value })}
                >
                    <option value="Full-time">Full-time</option>
                    <option value="Part-time">Part-time</option>
                    <option value="Freelance">Freelance</option>
                    <option value="Student">Student</option>
                    <option value="Other">Other</option>
                </select>
            </div>
            <div className={styles.formGroup}>
                <label className={styles.label}>Calendar Usage</label>
                <select
                    className={styles.input}
                    value={data.productivity?.uses_digital_calendar || 'No'}
                    onChange={(e) => updateData('productivity', { ...data.productivity, uses_digital_calendar: e.target.value })}
                >
                    <option value="Yes">Yes, heavily</option>
                    <option value="Sometimes">Sometimes</option>
                    <option value="No">No</option>
                </select>
            </div>
            <div className={styles.formGroup}>
                <label className={styles.label}>Overwhelm Level</label>
                <select
                    className={styles.input}
                    value={data.productivity?.time_overwhelm_level || 'Sometimes'}
                    onChange={(e) => updateData('productivity', { ...data.productivity, time_overwhelm_level: e.target.value })}
                >
                    <option value="Rarely">Rarely</option>
                    <option value="Sometimes">Sometimes</option>
                    <option value="Often">Often</option>
                    <option value="Always">Constant</option>
                </select>
            </div>
            <button className={styles.button} onClick={onNext}>Next →</button>
        </div>
    );
};
