/**
 * Home Page Component
 * 
 * Main landing page displaying user indexes, highlights, quick actions,
 * and smart recommendations.
 */

import React from 'react';
import { SummaryIndexBar } from '../../components/indexes';
import { useUserEngagement } from '../../hooks/useUser';
import styles from './Home.module.css';
import { Wallet, Clock, Heart, Car, CreditCard, Activity } from 'lucide-react';

import { useNavigate } from 'react-router-dom';
import { LifestyleWidget } from '../../components/lifestyle/LifestyleWidget';
import { GoalSetter } from '../../components/lifestyle/GoalSetter';

const Home: React.FC = () => {
    const navigate = useNavigate();
    const [scores, setScores] = React.useState<any>(null);
    const [isLoadingScores, setIsLoadingScores] = React.useState(true);
    const [timeHorizon, setTimeHorizon] = React.useState<'week' | 'month'>('week');
    const { streaks } = useUserEngagement();

    React.useEffect(() => {
        const fetchScores = async () => {
            setIsLoadingScores(true);
            try {
                const token = localStorage.getItem('token');
                // Pass the selected timeHorizon as 'period' query param
                const response = await fetch(`/api/scores/current?period=${timeHorizon}`, {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                if (response.ok) {
                    const data = await response.json();
                    setScores(data);
                }
            } catch (error) {
                console.error("Failed to fetch scores", error);
            } finally {
                setIsLoadingScores(false);
            }
        };
        fetchScores();
    }, [timeHorizon]); // Re-fetch when timeHorizon changes

    const handleChatSubmit = (message: string) => {
        if (message.trim()) {
            // Navigate to chat with the message
            navigate('/chat', { state: { initialMessage: message } });
        }
    };

    // Helper to format trend display
    const renderTrend = (value: number | null | undefined, contextLabel?: string) => {
        if (value === null || value === undefined) {
            return <span className={styles.trendAction}>Connect to unlock trends</span>;
        }

        if (value === 0) return <span className={styles.trendNeutral}> (stable)</span>;

        const sign = value > 0 ? '+' : '';
        const arrow = value > 0 ? '↑' : '↓';
        const colorClass = value > 0 ? styles.trendPositive : styles.trendNegative;

        // e.g. "+4.5 (Trending Up)"
        return (
            <span className={colorClass}>
                {sign}{value} {arrow} {contextLabel && `(${contextLabel})`}
            </span>
        );
    };

    if (isLoadingScores) {
        return (
            <div className={styles.container}>
                <div className={styles.loading}>Loading...</div>
            </div>
        );
    }

    // Prepare index data for SummaryIndexBar
    const indexData = [
        {
            id: 'financial',
            label: 'Stabilize Finances',
            value: scores?.has_data ? (scores?.financial_score || 0) : 0,
            trend: scores?.has_data ? (scores?.financial_trend || 0) : 0,
            variant: 'primary' as const,
            icon: (
                <div className={`${styles.iconContainer} ${styles.iconFinancial}`} style={{ margin: 0, padding: '8px', borderRadius: '8px' }}>
                    <Wallet size={20} />
                </div>
            ),
            onClick: () => navigate('/finance'),
        },
        {
            id: 'time',
            label: 'Execute & Focus',
            value: scores?.has_data ? (scores?.productivity_score || 0) : 0,
            trend: scores?.has_data ? (scores?.productivity_trend || 0) : 0,
            variant: 'secondary' as const,
            icon: (
                <div className={`${styles.iconContainer} ${styles.iconTime}`} style={{ margin: 0, padding: '8px', borderRadius: '8px' }}>
                    <Clock size={20} />
                </div>
            ),
            onClick: () => navigate('/time'),
        },
        {
            id: 'health',
            label: 'Recover Energy',
            value: scores?.has_data ? (scores?.health_score || 0) : 0,
            trend: scores?.has_data ? (scores?.health_trend || 0) : 0,
            variant: 'primary' as const,
            icon: (
                <div className={`${styles.iconContainer} ${styles.iconHealth}`} style={{ margin: 0, padding: '8px', borderRadius: '8px' }}>
                    <Heart size={20} />
                </div>
            ),
            onClick: () => navigate('/health'),
        }
    ];

    return (
        <div className={styles.container}>
            {/* Hero Indexes Section */}
            <section className={styles.heroSection}>
                <h1 className={styles.welcomeTitle}>Welcome back!</h1>
                <p className={styles.welcomeSubtitle}>Here's your wellbeing overview</p>

                <div style={{ marginBottom: '40px' }}></div>

                <SummaryIndexBar indexes={indexData} />
            </section>

            {/* Dashboard Grid Layout */}
            <div className={styles.dashboardGrid}>
                {/* Main Content Column */}
                <div className={styles.dashboardMain}>
                    {/* This Week / Month at a Glance */}
                    <section className={styles.highlightsSection}>
                        <div className={styles.sectionHeader}>
                            <h2 className={styles.sectionTitle} style={{ margin: 0 }}>
                                {timeHorizon === 'week' ? 'This Week at a Glance' : 'This Month in Review'}
                            </h2>
                            <div className={styles.toggleContainer}>
                                <span
                                    className={`${styles.toggleOption} ${timeHorizon === 'week' ? styles.active : ''}`}
                                    onClick={() => setTimeHorizon('week')}
                                >
                                    This Week
                                </span>
                                <span
                                    className={`${styles.toggleOption} ${timeHorizon === 'month' ? styles.active : ''}`}
                                    onClick={() => setTimeHorizon('month')}
                                >
                                    This Month
                                </span>
                            </div>
                        </div>

                        <div className={styles.highlightGrid}>
                            {/* Financial Card */}
                            <div
                                className={`${styles.highlightCard} ${styles.clickable}`}
                                onClick={() => navigate('/finance')}
                            >
                                <div className={`${styles.iconContainer} ${styles.iconFinancial}`}>
                                    <Wallet size={32} />
                                </div>
                                <h3 className={styles.highlightTitle}>
                                    {timeHorizon === 'week' ? 'Financial (WTD)' : 'Financial (MTD)'}
                                </h3>
                                {scores?.has_data ? (
                                    <p className={styles.highlightText}>
                                        Savings: {scores?.breakdown?.financial?.sr ? Math.round(scores.breakdown.financial.sr * 100) : 0}%
                                        {' '}{renderTrend(scores?.financial_trend, timeHorizon === 'week' ? 'vs last week' : 'vs last month')}
                                    </p>
                                ) : (
                                    <p className={styles.highlightText} style={{ color: 'var(--color-accent-blue)', fontWeight: 600 }}>
                                        Complete onboarding to see your insights
                                    </p>
                                )}
                            </div>

                            {/* Focus Card */}
                            <div
                                className={`${styles.highlightCard} ${styles.clickable}`}
                                onClick={() => navigate('/time')}
                            >
                                <div className={`${styles.iconContainer} ${styles.iconTime}`}>
                                    <Clock size={32} />
                                </div>
                                <h3 className={styles.highlightTitle}>
                                    {timeHorizon === 'week' ? 'Focus (WTD)' : 'Focus (MTD)'}
                                </h3>
                                {scores?.has_data ? (
                                    <p className={styles.highlightText}>
                                        Productivity: {Math.round(scores?.productivity_score || 0)}
                                        {' '}{renderTrend(scores?.productivity_trend, timeHorizon === 'week' ? 'vs last week' : 'vs last month')}
                                    </p>
                                ) : (
                                    <p className={styles.highlightText} style={{ color: 'var(--color-accent-blue)', fontWeight: 600 }}>
                                        Complete onboarding to see your insights
                                    </p>
                                )}
                            </div>

                            {/* Energy Card */}
                            <div
                                className={`${styles.highlightCard} ${styles.clickable}`}
                                onClick={() => navigate('/health')}
                            >
                                <div className={`${styles.iconContainer} ${styles.iconHealth}`}>
                                    <Heart size={32} />
                                </div>
                                <h3 className={styles.highlightTitle}>
                                    {timeHorizon === 'week' ? 'Energy (WTD)' : 'Energy (MTD)'}
                                </h3>
                                {scores?.has_data ? (
                                    <p className={styles.highlightText}>
                                        Health Score: {scores?.health_score || 0}
                                        {' '}{renderTrend(scores?.health_trend, timeHorizon === 'week' ? 'vs last week' : 'vs last month')}
                                    </p>
                                ) : (
                                    <p className={styles.highlightText} style={{ color: 'var(--color-accent-blue)', fontWeight: 600 }}>
                                        Complete onboarding to see your insights
                                    </p>
                                )}
                            </div>
                        </div>
                    </section>

                    {/* Streaks */}
                    {streaks && (
                        <section className={styles.streaksSection}>
                            <h2 className={styles.sectionTitle}>Your Streaks</h2>

                            <div className={styles.streaksGrid}>
                                <div className={styles.streakCard}>
                                    <div className={styles.streakNumber}>{streaks.dailyCheckIn}</div>
                                    <div className={styles.streakLabel}>Day Check-in Streak</div>
                                </div>

                                <div className={styles.streakCard}>
                                    <div className={styles.streakNumber}>{streaks.financialReview}</div>
                                    <div className={styles.streakLabel}>Week Financial Review Streak</div>
                                </div>
                            </div>
                        </section>
                    )}

                    {/* Lifestyle Section */}
                    {/* Moved inside main content to keep it linear */}
                    <section className={styles.recommendationsSection} style={{ marginTop: '0' }}>
                        <h2 className={styles.sectionTitle}>Lifestyle & Goals</h2>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
                            <LifestyleWidget />
                            <GoalSetter />
                        </div>
                    </section>
                </div>

                {/* Sidebar Column */}
                <div className={styles.dashboardSidebar}>
                    {/* Quick Actions */}
                    <section className={styles.quickActionsSection}>
                        <h2 className={styles.sectionTitle}>Quick Actions</h2>

                        <div className={styles.quickActionsGrid}>
                            <button
                                className={styles.quickActionButton}
                                onClick={() => handleChatSubmit("I want to book a car. Please ask me for the origin, destination, and time to make a mobility decision.")}
                            >
                                <span className={styles.quickActionIcon}><Car size={24} /></span>
                                <span className={styles.quickActionLabel}>Book a Car</span>
                            </button>

                            <button
                                className={styles.quickActionButton}
                                onClick={() => handleChatSubmit("Please analyze my current financial status. Show me how much I owe, how much I'm making, my potential savings by month-end, and if I'm on track for my goals.")}
                            >
                                <span className={styles.quickActionIcon}><CreditCard size={24} /></span>
                                <span className={styles.quickActionLabel}>Financial Health</span>
                            </button>

                            <button
                                className={styles.quickActionButton}
                                onClick={() => handleChatSubmit("Show me my health overview.")}
                            >
                                <span className={styles.quickActionIcon}><Activity size={24} /></span>
                                <span className={styles.quickActionLabel}>View Health</span>
                            </button>
                        </div>
                    </section>

                    {/* Smart Recommendations */}
                    <section className={styles.recommendationsSection}>
                        <h2 className={styles.sectionTitle}>Smart Recommendations</h2>

                        <div className={styles.recommendationsList}>
                            <div className={styles.recommendationCard}>
                                <div className={styles.recommendationHeader}>
                                    <span className={styles.recommendationBadge}>Financial</span>
                                    <span className={styles.recommendationTime}>2 hours ago</span>
                                </div>
                                <h3 className={styles.recommendationTitle}>
                                    Optimize your monthly subscriptions
                                </h3>
                                <p className={styles.recommendationDescription}>
                                    We found 3 subscriptions you rarely use. Cancel them to save $45/month.
                                </p>
                                <button className={styles.recommendationAction}>Review Now</button>
                            </div>

                            <div className={styles.recommendationCard}>
                                <div className={styles.recommendationHeader}>
                                    <span className={styles.recommendationBadge}>Time</span>
                                    <span className={styles.recommendationTime}>5 hours ago</span>
                                </div>
                                <h3 className={styles.recommendationTitle}>
                                    Automate your morning commute
                                </h3>
                                <p className={styles.recommendationDescription}>
                                    Set up automatic ride booking for your 8 AM commute every weekday.
                                </p>
                                <button className={styles.recommendationAction}>Set Up</button>
                            </div>

                            <div className={styles.recommendationCard}>
                                <div className={styles.recommendationHeader}>
                                    <span className={styles.recommendationBadge}>Health</span>
                                    <span className={styles.recommendationTime}>1 day ago</span>
                                </div>
                                <h3 className={styles.recommendationTitle}>
                                    Schedule recovery time
                                </h3>
                                <p className={styles.recommendationDescription}>
                                    Your activity load is high. Consider lighter tasks tomorrow afternoon.
                                </p>
                                <button className={styles.recommendationAction}>View Schedule</button>
                            </div>
                        </div>
                    </section>
                </div>
            </div>
        </div>
    );
};

export default Home;
