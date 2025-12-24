import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './Dashboard.module.css';
import { getUserProfile } from '../../api/userApi';
import { getUnifiedHistory } from '../../api/historyApi';
import { User } from '../../types/user';
import { HistoryItem } from '../../types/history';

const Dashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [recentActivity, setRecentActivity] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [userData, historyData] = await Promise.all([
          getUserProfile(),
          getUnifiedHistory({ types: ['viv_log', 'transaction', 'health'] }, 5)
        ]);

        if (userData) setUser(userData);
        if (historyData) {
          // Flatten groups to get items
          const items = historyData.groups.flatMap(g => g.items).slice(0, 5);
          setRecentActivity(items);
        }
      } catch (error) {
        console.error("Failed to load dashboard data", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  if (loading) return <div className={styles.container}>Loading HELM...</div>;
  if (!user) return <div className={styles.container}>Failed to load user profile.</div>;

  const { vivIndex } = user;
  const isCrisis = vivIndex.financialScore < 30 || vivIndex.healthScore < 30 || vivIndex.timeScore < 30;

  // STRICT BRAND RULES: No hex codes allowed other than defined in tokens.
  // Good = Blue (#3793D1), Warning/Bad = Red (#E23835), Neutral = Grayscale.
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'var(--color-accent-blue)';
    if (score >= 50) return 'var(--text-secondary)'; // Neutral for mid-range (no orange allowed)
    return 'var(--color-accent-red)';
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>Welcome back, {user.identity.username}</h1>
          <p className={styles.subtitle}>Here is your HELM Pulse for today.</p>
        </div>
      </div>

      {isCrisis && (
        <div className={styles.crisisAlert}>
          <span>⚠️ Crisis Mode Active: One or more of your vitals are critically low. Focus on recovery.</span>
        </div>
      )}

      <div className={styles.indexesGrid}>
        {/* Financial Score */}
        <div
          className={`${styles.indexCard} ${styles.clickableCard}`}
          onClick={() => navigate('/finance')}
        >
          <span className={styles.scoreLabel}>Financial Wealth</span>
          <div className={styles.scoreCircle} style={{ border: `8px solid ${getScoreColor(vivIndex.financialScore)}`, color: getScoreColor(vivIndex.financialScore) }}>
            {vivIndex.financialScore}
          </div>
          <span className={styles.scoreTrend}>Target: 80+</span>
        </div>

        {/* Health Score */}
        <div
          className={`${styles.indexCard} ${styles.clickableCard}`}
          onClick={() => navigate('/health')}
        >
          <span className={styles.scoreLabel}>Physical Wellbeing</span>
          <div className={styles.scoreCircle} style={{ border: `8px solid ${getScoreColor(vivIndex.healthScore)}`, color: getScoreColor(vivIndex.healthScore) }}>
            {vivIndex.healthScore}
          </div>
          <span className={styles.scoreTrend}>Target: 80+</span>
        </div>

        {/* Time Score */}
        <div
          className={`${styles.indexCard} ${styles.clickableCard}`}
          onClick={() => navigate('/time')}
        >
          <span className={styles.scoreLabel}>Execution Intelligence</span>
          <div className={styles.scoreCircle} style={{ border: `8px solid ${getScoreColor(vivIndex.timeScore)}`, color: getScoreColor(vivIndex.timeScore) }}>
            {vivIndex.timeScore}
          </div>
          <span className={styles.scoreTrend}>Target: 80+</span>
        </div>
      </div>

      <div>
        <h2 className={styles.sectionTitle}>Recent Activity</h2>
        <div className={styles.activityFeed}>
          {recentActivity.map(item => (
            <div key={item.id} className={styles.activityCard} style={{ borderLeftColor: item.type === 'transaction' ? 'var(--color-accent-blue)' : item.type === 'health' ? 'var(--text-secondary)' : 'var(--text-primary)' }}>
              <div className={styles.activityContent}>
                <span className={styles.activityTitle}>{item.title}</span>
                <span className={styles.activitySubtitle}>{item.subtitle}</span>
              </div>
              <span className={styles.activityTime}>{new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            </div>
          ))}
          {recentActivity.length === 0 && <p>No recent activity recorded.</p>}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
