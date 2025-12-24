import React, { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Lock, AlertCircle, TrendingUp } from 'lucide-react';
import { getCategoryCoverage, getFinancialHistory } from '../../api/financialApi';
import styles from './Dashboard.module.css';

interface TrendCardProps {
    categoryId: string;
    title: string;
    description: string;
    isOpen: boolean;
    onClose: () => void;
}

const TrendCard: React.FC<TrendCardProps> = ({ categoryId, title, description, isOpen, onClose }) => {
    const [loading, setLoading] = useState(true);
    const [coverage, setCoverage] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);

    useEffect(() => {
        if (isOpen) {
            loadData();
        }
    }, [isOpen, categoryId]);

    const loadData = async () => {
        setLoading(true);
        try {
            const [covRes, histRes] = await Promise.all([
                getCategoryCoverage(categoryId),
                getFinancialHistory(categoryId, '30d')
            ]);
            setCoverage(covRes);
            if (histRes && histRes.points) {
                setHistory(histRes.points);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className={styles.modalOverlay} onClick={onClose}>
            <div className={styles.modalContent} onClick={e => e.stopPropagation()}>

                <div className={styles.modalHeader}>
                    <div>
                        <h2 className={styles.modalTitle}>{title}</h2>
                        <p className={styles.modalDesc}>{description}</p>
                    </div>
                    <button onClick={onClose} className={styles.closeButton}>
                        ✕
                    </button>
                </div>

                <div className={styles.chartContainer}>
                    {loading ? (
                        <div className={styles.loadingSpinner}></div>
                    ) : coverage?.chart_unlocked ? (
                        /* UNLOCKED STATE */
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={history}>
                                <defs>
                                    <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <XAxis dataKey="date" hide />
                                <YAxis hide domain={[0, 100]} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1f1f1f', border: '1px solid #333', borderRadius: '8px' }}
                                    itemStyle={{ color: '#fff' }}
                                />
                                <Area
                                    type="monotone"
                                    dataKey="value"
                                    stroke="#3B82F6"
                                    strokeWidth={3}
                                    fillOpacity={1}
                                    fill="url(#colorScore)"
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : coverage?.has_some_data ? (
                        /* LOCKED STATE (Partial Data) */
                        <div className={styles.stateContent}>
                            <div className={styles.iconCircle}>
                                <Lock className={styles.lockIcon} />
                            </div>
                            <h3 className={styles.stateTitle}>Unlock Trends</h3>
                            <p className={styles.stateDesc}>
                                Keep logging your data to unlock deep insights. You need {coverage.remaining_days} more days of data.
                            </p>

                            {/* Progress Bar */}
                            <div className={styles.progressContainer}>
                                <div
                                    className={styles.progressFill}
                                    style={{ width: `${(coverage.coverage_ratio || 0) * 100}%` }}
                                />
                            </div>
                            <p className={styles.progressText}>
                                {Math.round((coverage.coverage_ratio || 0) * 100)}% Complete
                            </p>
                        </div>
                    ) : (
                        /* EMPTY STATE (No Data) */
                        <div className={styles.stateContent}>
                            <div className={styles.iconCircle}>
                                <AlertCircle className={styles.alertIcon} />
                            </div>
                            <h3 className={styles.stateTitle}>No Data Available</h3>
                            <p className={styles.stateDesc}>
                                Connect your accounts or start logging transactions to see this metric.
                            </p>
                            <a
                                href="/account?tab=data"
                                className={styles.connectButton}
                            >
                                Connect Data Source
                            </a>
                        </div>
                    )}
                </div>

                <div className={styles.statsGrid}>
                    <div className={styles.statBox}>
                        <div className={styles.statLabel}>Current Score</div>
                        <div className={styles.statValue}>
                            {history.length > 0 ? history[history.length - 1].value.toFixed(1) : (coverage?.chart_unlocked ? 'N/A' : 'Locked')}
                        </div>
                    </div>
                    <div className={styles.statBox}>
                        <div className={styles.statLabel}>Data Quality</div>
                        <div className={styles.qualityValue}>
                            {coverage?.no_data ? (
                                <span className={styles.qualityNone}>No Data</span>
                            ) : coverage?.chart_unlocked ? (
                                <span className={styles.qualityExcellent}>
                                    <TrendingUp className="w-3 h-3" /> Excellent
                                </span>
                            ) : (
                                <span className={styles.qualityBuilding}>Building History</span>
                            )}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default TrendCard;
