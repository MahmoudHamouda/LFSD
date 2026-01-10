import React, { useState } from 'react';
import { X, Check, Star } from 'lucide-react';
import styles from './UpgradePrompt.module.css';
import { useAuth } from '../../context/AuthProvider';

interface UpgradePromptProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: () => void;
    currentPlan: string;
}

const PLANS = [
    {
        id: 'tier_free',
        name: 'Free',
        price: '$0',
        features: ['100 AI Chat Calls', '10 Smart Recos', '0 Executions', '5 Active Goals'],
        buttonText: 'Current Plan'
    },
    {
        id: 'tier_plus',
        name: 'Plus',
        price: '$4.99',
        features: ['500 AI Chat Calls', '100 Smart Recos', '20 Executions', 'Unlimited Goals'],
        buttonText: 'Upgrade'
    },
    {
        id: 'tier_pro',
        name: 'Pro',
        price: '$9.99',
        recommended: true,
        features: ['2,000 AI Chat Calls', '500 Smart Recos', '100 Executions', 'Unlimited Goals'],
        buttonText: 'Upgrade'
    },
    {
        id: 'tier_enterprise',
        name: 'Enterprise',
        price: 'Custom',
        features: ['SLA + Audit', 'Custom Integrations', 'Unlimited Everything'],
        buttonText: 'Contact Us'
    }
];

const UpgradePrompt: React.FC<UpgradePromptProps> = ({ isOpen, onClose, onSuccess, currentPlan }) => {
    const { getAccessToken } = useAuth();
    const [loading, setLoading] = useState<string | null>(null);

    if (!isOpen) return null;

    const handleSubscribe = async (planId: string) => {
        if (planId === 'tier_enterprise') {
            alert("Please contact enterprise@helm.com for custom setup.");
            return;
        }

        setLoading(planId);
        try {
            const token = await getAccessToken();
            const response = await fetch('/api/growth/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    plan_id: planId,
                    payment_method_id: 'pm_mock_card'
                })
            });

            if (!response.ok) {
                throw new Error('Subscription failed');
            }

            onSuccess();
            onClose();
        } catch (error) {
            console.error("Upgrade failed", error);
            alert("Failed to upgrade plan. Please try again.");
        } finally {
            setLoading(null);
        }
    };

    return (
        <div className={styles.overlay}>
            <div className={styles.modal} style={{ maxWidth: '1000px' }}>
                <button className={styles.closeButton} onClick={onClose} aria-label="Close">
                    <X size={24} />
                </button>

                <div className={styles.header}>
                    <div className={styles.iconWrapper}>
                        <Star size={32} className={styles.starIcon} />
                    </div>
                    <h2 className={styles.title}>Scale Your HELM Experience</h2>
                    <p className={styles.subtitle}>Choose the plan that fits your execution and intelligence needs.</p>
                </div>

                <div className={styles.plansContainer}>
                    {PLANS.map((plan) => (
                        <div
                            key={plan.id}
                            className={`${styles.planCard} ${plan.id === 'tier_free' ? styles.freePlan : plan.id === 'tier_pro' ? styles.proPlan : ''} ${currentPlan === plan.id ? styles.currentPlan : ''}`}
                        >
                            {plan.recommended && <div className={styles.popularBadge}>RECOMMENDED</div>}
                            <div className={styles.planHeader}>
                                <h3>{plan.name}</h3>
                                <span className={styles.price}>{plan.price}{plan.id !== 'tier_enterprise' && plan.id !== 'tier_free' && <span>/mo</span>}</span>
                            </div>
                            <ul className={styles.featuresList}>
                                {plan.features.map((feature, i) => (
                                    <li key={i}><Check size={14} /> {feature}</li>
                                ))}
                            </ul>
                            <button
                                className={styles.upgradeButton}
                                onClick={() => handleSubscribe(plan.id)}
                                disabled={!!loading || currentPlan === plan.id}
                                style={{
                                    opacity: currentPlan === plan.id ? 0.6 : 1,
                                    cursor: currentPlan === plan.id ? 'default' : 'pointer'
                                }}
                            >
                                {loading === plan.id ? 'Processing...' : currentPlan === plan.id ? 'Active' : plan.buttonText}
                            </button>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default UpgradePrompt;
