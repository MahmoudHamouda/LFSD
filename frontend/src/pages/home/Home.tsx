/**
 * Home Page Component
 * 
 * Main landing page displaying user indexes, highlights, quick actions,
 * and smart recommendations.
 */

import React, { useState, useEffect } from 'react';
import { SummaryIndexBar } from '../../components/indexes';
import { useUserEngagement } from '../../hooks/useUser';
import styles from './Home.module.css';
import { Wallet, Clock, Heart, Car, CreditCard, Activity } from 'lucide-react';

import { useNavigate } from 'react-router-dom';
import GoalsSection from '../../components/dashboard/GoalsSection';
import PillarSummaryCard, { PillarData } from '../../components/dashboard/PillarSummaryCard';
import ChatInput from '../../components/chat/ChatInput';

const Home: React.FC = () => {
    const navigate = useNavigate();
    const [overallScores, setOverallScores] = useState<any>(null);
    const [weekScores, setWeekScores] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);
    const { streaks } = useUserEngagement();
    const [recommendations, setRecommendations] = useState<any[]>([]);
    const [treats, setTreats] = useState<any[]>([]);

    useEffect(() => {
        const fetchScores = async () => {
            setIsLoading(true);
            try {
                const token = localStorage.getItem('token');

                // Fetch Overall, Weekly scores, Recommendations, AND Treats
                const [resOverall, resWeek, resRecs, resTreats] = await Promise.all([
                    fetch('/api/scores/current?period=month', { headers: { 'Authorization': `Bearer ${token}` } }),
                    fetch('/api/scores/current?period=week', { headers: { 'Authorization': `Bearer ${token}` } }),
                    fetch('/api/home/recommendations', { headers: { 'Authorization': `Bearer ${token}` } }),
                    fetch('/api/home/treats', { headers: { 'Authorization': `Bearer ${token}` } })
                ]);

                if (resOverall.ok) {
                    setOverallScores(await resOverall.json());
                }
                if (resWeek.ok) {
                    setWeekScores(await resWeek.json());
                }
                if (resRecs.ok) {
                    const data = await resRecs.json();
                    if (data.items) {
                        setRecommendations(data.items);
                    }
                }
                if (resTreats.ok) {
                    const data = await resTreats.json();
                    if (data.items) {
                        setTreats(data.items);
                    }
                }
            } catch (error) {
                console.error("Failed to fetch data", error);
            } finally {
                setIsLoading(false);
            }
        };
        fetchScores();
    }, []);

    const calculateTimeAgo = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

        if (diffInSeconds < 60) return 'Just now';
        const diffInMinutes = Math.floor(diffInSeconds / 60);
        if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
        const diffInHours = Math.floor(diffInMinutes / 60);
        if (diffInHours < 24) return `${diffInHours}h ago`;
        const diffInDays = Math.floor(diffInHours / 24);
        return `${diffInDays}d ago`;
    };

    const handleChatSubmit = (message: string) => {
        if (message.trim()) {
            navigate('/chat', { state: { initialMessage: message } });
        }
    };

    if (isLoading) {
        return (
            <div className={styles.container}>
                <div className={styles.loading}>Loading...</div>
            </div>
        );
    }

    // --- Data Preparation for Pillars ---

    // Finance
    const financeOverall: PillarData = {
        value: overallScores?.financial_score || 0,
        trend: overallScores?.financial_trend ?? null,
        metricLabel: 'Overall Financial Score',
        subtext: 'Monthly View'
    };

    const financeWeek: PillarData = {
        value: weekScores?.breakdown?.financial?.sr !== undefined ? `${Math.round(weekScores.breakdown.financial.sr * 100)}%` : '0%',
        trend: weekScores?.financial_trend ?? null,
        metricLabel: 'Savings Rate (WTD)',
        subtext: 'vs last week'
    };
    // Update financeWeek value to use weekScores
    if (weekScores?.breakdown?.financial?.sr !== undefined) {
        financeWeek.value = `${Math.round(weekScores.breakdown.financial.sr * 100)}%`;
    }

    // Time
    const timeOverall: PillarData = {
        value: overallScores?.productivity_score || 0,
        trend: overallScores?.productivity_trend ?? null,
        metricLabel: 'Productivity Score',
        subtext: 'Monthly Average'
    };

    const timeWeek: PillarData = {
        value: weekScores?.productivity_score || 0,
        trend: weekScores?.productivity_trend ?? null,
        metricLabel: 'Productivity (WTD)',
        subtext: 'vs last week'
    };

    // Health
    const healthOverall: PillarData = {
        value: overallScores?.health_score || 0,
        trend: null, // explicit null for verification
        metricLabel: 'Health & Recovery',
        subtext: 'Monthly Average'
    };

    const healthWeek: PillarData = {
        value: weekScores?.health_score || 0,
        trend: weekScores?.health_trend,
        metricLabel: 'Health Score (WTD)',
        subtext: 'vs last week'
    };

    const getRecommendationIcon = (type: string) => {
        switch (type) {
            case 'finance': return <Wallet className="w-5 h-5 text-green-500" />;
            case 'time': return <Clock className="w-5 h-5 text-blue-500" />;
            case 'health': return <Heart className="w-5 h-5 text-red-500" />;
            case 'mobility': return <Car className="w-5 h-5 text-purple-500" />;
            default: return <Activity className="w-5 h-5 text-gray-500" />;
        }
    };

    return (
        <div className={styles.container}>
            {/* Hero Indexes Section */}
            <section className={styles.heroSection}>
                <h1 className={styles.welcomeTitle}>Welcome back</h1>
                <p className={styles.welcomeSubtitle}>Here’s how things are looking today.</p>

                <div className={styles.chatPromptContainer}>
                    <ChatInput onSend={handleChatSubmit} isLoading={false} />
                </div>

                <div className={styles.pillarGrid}>
                    <PillarSummaryCard
                        title="Stabilize Finances"
                        icon={<Wallet size={24} />}
                        color="var(--color-accent-green)"
                        overallData={financeOverall}
                        weekData={financeWeek}
                        onNavigate={() => navigate('/finance')}
                    />
                    <PillarSummaryCard
                        title="Execute & Focus"
                        icon={<Clock size={24} />}
                        color="var(--color-accent-blue)"
                        overallData={timeOverall}
                        weekData={timeWeek}
                        onNavigate={() => navigate('/time')}
                    />
                    <PillarSummaryCard
                        title="Recover Energy"
                        icon={<Heart size={24} />}
                        color="var(--color-accent-red)"
                        overallData={healthOverall}
                        weekData={healthWeek}
                        onNavigate={() => navigate('/health')}
                    />
                </div>
            </section>


            {/* Main Sections Row: 2 Columns */}
            <div className={styles.sectionsRow}>
                {/* Left Column: Streaks + Smart Recommendations */}
                <div className={styles.columnLeft}>
                    {/* Streaks */}
                    {streaks && (
                        <section className={styles.streaksColumn}>
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

                    {/* Goals Section (Restored & Standardized) */}
                    <GoalsSection variant="all" />
                </div>

                {/* Right Column: Quick Actions + Treat Yourself */}
                <div className={styles.columnRight}>
                    {/* Quick Actions */}
                    <section className={styles.quickActionsColumn}>
                        <h2 className={styles.sectionTitle}>Quick Actions</h2>

                        <div className={styles.quickActionsGrid}>
                            <button
                                className={styles.quickActionButton}
                                onClick={() => handleChatSubmit("I want to book a car. Please ask me for the origin, destination, and time to make a mobility decision.")}
                            >
                                <span className={styles.quickActionIcon}><Car size={40} /></span>
                                <span className={styles.quickActionLabel}>Book a Car</span>
                            </button>

                            <button
                                className={styles.quickActionButton}
                                onClick={() => handleChatSubmit("Please analyze my current financial status. Show me how much I owe, how much I'm making, my potential savings by month-end, and if I'm on track for my goals.")}
                            >
                                <span className={styles.quickActionIcon}><CreditCard size={40} /></span>
                                <span className={styles.quickActionLabel}>Financial Health</span>
                            </button>

                            <button
                                className={styles.quickActionButton}
                                onClick={() => handleChatSubmit("Show me my health overview.")}
                            >
                                <span className={styles.quickActionIcon}><Activity size={40} /></span>
                                <span className={styles.quickActionLabel}>View Health</span>
                            </button>
                        </div>
                    </section>

                    {/* Treat Yourself */}
                    <section className={styles.recommendationsSection}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                            <h2 className={styles.sectionTitle} style={{ margin: 0 }}>Treat Yourself</h2>
                        </div>

                        <p style={{ color: 'var(--color-text-secondary)', marginBottom: '20px', fontSize: '14px' }}>
                            Rewards based on your recent achievements.
                        </p>

                        {treats.length > 0 ? (
                            <div className={styles.recommendationsList}>
                                {treats.map((treat) => (
                                    <div key={treat.id} className={styles.recommendationCard}>
                                        <div className={styles.recommendationHeader}>
                                            <span className={styles.recommendationBadge} style={{ backgroundColor: 'RGBA(255, 140, 0, 0.1)', color: 'darkorange' }}>
                                                {treat.category.charAt(0) + treat.category.slice(1).toLowerCase()}
                                            </span>
                                        </div>
                                        <h3 className={styles.recommendationTitle}>
                                            {treat.title}
                                        </h3>
                                        <p className={styles.recommendationDescription}>
                                            {treat.body}
                                        </p>
                                        <button
                                            className={styles.recommendationAction}
                                            style={{ backgroundColor: 'var(--color-accent-orange)', border: 'none' }}
                                            onClick={() => navigate(treat.cta.href)}
                                        >
                                            {treat.cta.label}
                                        </button>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className={styles.emptyState}>
                                <p className={styles.emptyStateText}>No recommendations yet. Keep up the good work!</p>
                            </div>
                        )}
                    </section>

                    {/* Smart Recommendations */}
                    <section className={styles.recommendationsSection}>
                        <h2 className={styles.sectionTitle}>Smart Recommendations</h2>

                        <div className={styles.recommendationsList}>
                            {recommendations.length > 0 ? (
                                recommendations.map((rec) => (
                                    <div key={rec.id} className={styles.recommendationCard}>
                                        <div className={styles.recommendationIconWrapper}>
                                            <div className={styles.recommendationIcon}>
                                                {getRecommendationIcon(rec.type)}
                                            </div>
                                        </div>
                                        <div className={styles.recommendationContent}>
                                            <h4 className={styles.recommendationTitle}>{rec.title}</h4>
                                            <p className={styles.recommendationDescription}>{rec.body}</p> {/* Changed from rec.description to rec.body to match original data structure */}
                                            <div className={styles.recommendationMeta}>
                                                {/* Assuming rec.impact is available */}
                                                {/* <span className={styles.recommendationImpact}>{rec.impact}</span> */}
                                                <button className={styles.recommendationAction} onClick={() => navigate(rec.cta.href)}> {/* Added onClick to match original functionality */}
                                                    {rec.cta.label} {/* Changed from "Review" to rec.cta.label */}
                                                    {/* <ArrowRight className="w-4 h-4" /> */}
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div className={styles.emptyState}>
                                    <div className={styles.emptyStateIcon}>🎉</div> {/* Added back empty state icon */}
                                    <p className={styles.emptyStateText}>All caught up! No new recommendations at this time.</p> {/* Changed text to match original */}
                                </div>
                            )}
                        </div>
                    </section>
                </div>
            </div>
        </div>
    );
};

export default Home;
