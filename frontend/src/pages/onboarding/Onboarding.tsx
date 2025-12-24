
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthProvider';
import styles from './Onboarding.module.css';
import {
    WelcomeStep,
    FocusSelectionStep,
    FinancialStep1,
    FinancialStep2,
    FinancialStep3,
    FinancialScoreStep,
    HealthStep1,
    HealthStep2,
    HealthScoreStep,
    ProductivityStep1,
    ProductivityStep2,
    CalendarStep,
    TimeScoreStep,
    ProcessingStep,
    ResultsStep,
    SignupStep,
    QuickFinancialStep,
    QuickHealthStep,
    QuickProductivityStep
} from './OnboardingSteps';

export default function Onboarding() {
    const navigate = useNavigate();
    const { user, logout } = useAuth();
    const [step, setStep] = useState(0);
    const [focusArea, setFocusArea] = useState<'financial' | 'health' | 'productivity' | null>(null);
    const [loadingScore, setLoadingScore] = useState(false);
    const [scoreError, setScoreError] = useState<string | undefined>(undefined);

    // Form Data
    const [formData, setFormData] = useState({
        name: user?.name || '',
        email: user?.email || '',
        password: '',
        financial: {
            currency: 'USD',
            onboarding_session_id: '',
            session_ids: [] as string[],
            is_manual_mode: false,
            monthly_income: 0,
            monthly_income_type: 'amount',
            income_frequency: 'Monthly',
            employment_type: 'Full-time',
            other_income_sources: [] as string[],
            monthly_expenses: 0,
            monthly_expenses_type: 'amount',
            has_debt: 'no',
            total_debt: 0,
            monthly_debt_payments: 0,
            housing_status: 'rent',
            housing_value: 0,
            rent_amount: 0,
            rent_frequency: 'Monthly',
            car_status: 'no_car',
            car_value: 0,
            car_lease_amount: 0,
            car_lease_frequency: 'Monthly',
            other_assets_status: 'no',
            other_assets_description: '',
            discretionary_spend: 0,
            discretionary_spend_type: 'amount',
            monthly_savings: 0,
            monthly_savings_type: 'amount',
            investments_status: 'no',
            investments_value: 0,
            investments_types: [] as string[],
            risk_appetite: 'unsure'
        },
        health: {
            sleep_hours: '7-8',
            sleep_consistency: 'Mostly',
            wake_tired: 'Sometimes',
            activity_level: 'Moderate',
            activity_type: 'None',
            stress_level: 'Sometimes',
            energy_pattern: 'Stable',
            diet_style: 'Balanced',
            water_intake: '1-2L',
            smoking_pattern: 'Never',
            alcohol_pattern: 'Occasionally',
            eating_out_frequency: 'Rarely',
            takeaway_frequency: 'Rarely',
            cooking_frequency: 'Rarely',
            nightlife_frequency: 'Rarely'
        },
        productivity: {
            work_status: 'Full-time',
            work_hours_per_week: '40',
            uses_digital_calendar: 'No',
            commute_duration: '<15 min',
            time_meals_house_daily: '1-2 hours',
            time_admin_weekly: '1-3 hours',
            main_time_drains: [] as string[],
            routine_style: 'I try',
            task_style: 'I react to what\'s urgent',
            time_overwhelm_level: 'Sometimes'
        }
    });

    const [calculatedIndices, setCalculatedIndices] = useState({
        financial: 0,
        health: 0,
        productivity: 0
    });

    const [financialBreakdown, setFinancialBreakdown] = useState<any>(null);
    const [healthBreakdown, setHealthBreakdown] = useState<any>(null);
    const [timeBreakdown, setTimeBreakdown] = useState<any>(null);

    const updateData = React.useCallback((section: string, data: any) => {
        setFormData(prev => ({ ...prev, [section]: data }));
    }, []);

    // Define Flows
    const getFlow = (focus: string | null) => {
        if (focus === 'financial') {
            return [
                { id: 'financial-1', component: FinancialStep1 },
                { id: 'financial-2', component: FinancialStep2 },
                { id: 'financial-3', component: FinancialStep3 },
                { id: 'financial-score', component: FinancialScoreStep },
                { id: 'quick-health', component: QuickHealthStep },
                { id: 'quick-productivity', component: QuickProductivityStep }
            ];
        }
        if (focus === 'health') {
            return [
                { id: 'health-1', component: HealthStep1 },
                { id: 'health-2', component: HealthStep2 },
                { id: 'health-score', component: HealthScoreStep },
                { id: 'quick-financial', component: QuickFinancialStep },
                { id: 'quick-productivity', component: QuickProductivityStep }
            ];
        }
        if (focus === 'productivity') {
            return [
                { id: 'productivity-1', component: ProductivityStep1 },
                { id: 'productivity-2', component: ProductivityStep2 },
                { id: 'calendar', component: CalendarStep },
                { id: 'time-score', component: TimeScoreStep },
                { id: 'quick-financial', component: QuickFinancialStep },
                { id: 'quick-health', component: QuickHealthStep }
            ];
        }
        return [];
    };

    const handleFocusSelect = (focus: 'financial' | 'health' | 'productivity') => {
        setFocusArea(focus);
        setStep(1);
    };

    const handleBack = () => {
        setStep(prev => Math.max(0, prev - 1));
    };

    const handleNext = () => {
        setStep(prev => prev + 1);
    };

    const calculateScore = async (type: 'financial' | 'health' | 'productivity') => {
        setLoadingScore(true);
        setScoreError(undefined);

        try {
            const payload = {
                user_id: user?.id,
                ...formData.financial,
                ...formData.health,
                ...formData.productivity
            };
            const token = localStorage.getItem('token');
            const response = await fetch('/api/scores/onboarding', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) throw new Error('Failed to calculate scores');
            const result = await response.json();

            if (type === 'financial') {
                setCalculatedIndices(prev => ({ ...prev, financial: result.financial_score }));
                setFinancialBreakdown(result.breakdown?.financial?.subscores);
            } else if (type === 'health') {
                setCalculatedIndices(prev => ({ ...prev, health: result.health_score }));
                setHealthBreakdown(result.breakdown?.health?.subscores);
            } else if (type === 'productivity') {
                setCalculatedIndices(prev => ({ ...prev, productivity: result.productivity_score }));
                setTimeBreakdown(result.breakdown?.productivity?.subscores || result.breakdown?.time?.subscores);
            }
        } catch (error: any) {
            console.error(error);
            setScoreError(error.message);
        } finally {
            setLoadingScore(false);
        }
    };

    const handleFinish = async () => {
        setLoadingScore(true);
        try {
            // Persist one last time with all data
            const payload = {
                user_id: user?.id,
                ...formData.financial,
                ...formData.health,
                ...formData.productivity
            };

            const token = localStorage.getItem('token');
            await fetch('/api/scores/onboarding', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify(payload),
            });

            // Mark Complete
            await fetch(`/api/users/${user?.id}/onboarding/complete`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });

            window.location.href = '/';
        } catch (e) {
            console.error(e);
            alert("Error finishing setup");
        } finally {
            setLoadingScore(false);
        }
    };

    // Render Component based on Step
    if (step === 0) {
        return (
            <div className={styles.container}>
                <div className={styles.content}>
                    <FocusSelectionStep onNext={() => { }} onBack={logout} data={formData} updateData={updateData} onSelectFocus={handleFocusSelect} />
                </div>
            </div>
        );
    }

    const flow = getFlow(focusArea);
    const flowIndex = step - 1; // step 1 -> index 0

    if (flowIndex >= flow.length) {
        return <div className={styles.container}><div className={styles.content}>Configuring your dashboard...</div></div>;
    }

    const currentStep = flow[flowIndex];
    if (!currentStep) return <div className={styles.container}>Error: Unknown step</div>;

    const Component = currentStep.component;
    const isLastStep = flowIndex === flow.length - 1;

    // Special props injection
    let extraProps: any = {};
    if (currentStep.id === 'financial-3') {
        extraProps = { onNext: () => { calculateScore('financial'); handleNext(); } };
    }
    if (currentStep.id === 'financial-score') {
        extraProps = { score: calculatedIndices.financial, subscores: financialBreakdown, loading: loadingScore, error: scoreError };
    }
    if (currentStep.id === 'health-2') {
        extraProps = { onNext: () => { calculateScore('health'); handleNext(); } };
    }
    if (currentStep.id === 'health-score') {
        extraProps = { score: calculatedIndices.health, subscores: healthBreakdown, loading: loadingScore, error: scoreError };
    }
    if (currentStep.id === 'calendar') {
        extraProps = { onNext: () => { calculateScore('productivity'); handleNext(); } };
    }
    if (currentStep.id === 'time-score') {
        extraProps = { score: calculatedIndices.productivity, subscores: timeBreakdown, loading: loadingScore, error: scoreError };
    }

    // Wire completion to the last step's Next action
    if (isLastStep) {
        // If it's a Quick step, they usually just call onNext. We override it.
        // If it's TimeScoreStep (in productivity flow), it also has a button.
        // We accumulate props, so existing onNext logic might conflict if we don't be careful.
        // But Quick steps just take `onNext`. Score steps take `onNext`.
        // So this override is safe.
        extraProps = { ...extraProps, onNext: handleFinish };
    }

    return (
        <div className={styles.container}>
            <div className={styles.progress} style={{ width: `${((step) / (flow.length + 1)) * 100}%` }} />
            <div className={styles.content}>
                <Component
                    onNext={handleNext}
                    onBack={handleBack}
                    data={formData}
                    updateData={updateData}
                    {...extraProps}
                />
            </div>
        </div>
    );
}
