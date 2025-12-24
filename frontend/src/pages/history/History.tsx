/**
 * History Page Component
 * 
 * Unified history timeline displaying all user activities with filters.
 */

import React, { useEffect, useState } from 'react';
import { SummaryIndexBar } from '../../components/indexes';
import { useUserIndexes } from '../../hooks/useUser';
import styles from './History.module.css';
import { getUnifiedHistory } from '../../api/historyApi';
import { HistoryDayGroup, HistoryItemType } from '../../types/history';

const History: React.FC = () => {
    const { indexes, hasHealthIndex } = useUserIndexes();
    const [selectedTypes, setSelectedTypes] = useState<HistoryItemType[]>([]);
    const [historyGroups, setHistoryGroups] = useState<HistoryDayGroup[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadHistory = async () => {
            setLoading(true);
            try {
                const response = await getUnifiedHistory({
                    types: selectedTypes.length > 0 ? selectedTypes : []
                });
                if (response) {
                    setHistoryGroups(response.groups);
                }
            } catch (error) {
                console.error("Failed to load history", error);
            } finally {
                setLoading(false);
            }
        };

        loadHistory();
    }, [selectedTypes]);

    // Prepare index data
    const indexData = [
        {
            id: 'financial',
            label: 'Financial Wellbeing',
            value: indexes?.financialScore || 0,
            variant: 'primary' as const,
            icon: 'Money',
        },
        {
            id: 'time',
            label: 'Time Saved',
            value: indexes?.timeScore || 0,
            variant: 'secondary' as const,
            icon: 'Clock',
        },
    ];

    if (indexes) {
        indexData.push({
            id: 'balance',
            label: 'Physical Wellbeing',
            value: indexes.healthScore,
            variant: 'primary' as const,
            icon: 'Health',
        });
    }

    const toggleType = (type: HistoryItemType) => {
        setSelectedTypes(prev =>
            prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]
        );
    };

    const getIcon = (type: string) => {
        switch (type) {
            case 'transaction': return '💳';
            case 'health': return '❤️';
            case 'viv_log': return '🧠';
            default: return '📝';
        }
    };

    return (
        <div className={styles.container}>
            {/* Indexes Bar */}
            <SummaryIndexBar indexes={indexData} variant="compact" />

            {/* Filter Bar */}
            <div className={styles.filterBar}>
                <div className={styles.typeFilters}>
                    <button
                        className={`${styles.filterChip} ${selectedTypes.includes('transaction') ? styles.active : ''}`}
                        onClick={() => toggleType('transaction')}
                    >
                        💰 Money
                    </button>
                    <button
                        className={`${styles.filterChip} ${selectedTypes.includes('health') ? styles.active : ''}`}
                        onClick={() => toggleType('health')}
                    >
                        ❤️ Health
                    </button>
                    <button
                        className={`${styles.filterChip} ${selectedTypes.includes('viv_log') ? styles.active : ''}`}
                        onClick={() => toggleType('viv_log')}
                    >
                        🧠 HELM Logic
                    </button>
                </div>
            </div>

            {/* Execution Intelligence Score */}
            <div className={styles.timeline}>
                {loading ? (
                    <div style={{ textAlign: 'center', padding: '40px' }}>Loading timeline...</div>
                ) : (
                    historyGroups.map((group) => (
                        <div key={group.date} className={styles.dayGroup}>
                            <div className={styles.dayLabel}>{group.date}</div>

                            <div className={styles.itemsList}>
                                {group.items.map((item) => (
                                    <div key={item.id} className={styles.historyItem} style={{ borderLeft: `4px solid ${item.type === 'transaction' ? 'var(--color-accent-blue)' : item.type === 'health' ? 'var(--text-secondary)' : 'var(--text-primary)'}` }}>
                                        <div className={styles.itemIcon}>
                                            {getIcon(item.type)}
                                        </div>

                                        <div className={styles.itemContent}>
                                            <div className={styles.itemTitle}>{item.title}</div>
                                            <div className={styles.itemSubtitle}>{item.subtitle}</div>
                                        </div>

                                        <div className={styles.itemMeta}>
                                            {item.amount !== undefined && (
                                                <div className={`${styles.itemAmount} ${item.amount < 0 ? styles.negative : styles.positive}`}>
                                                    {item.amount < 0 ? '-' : '+'}${Math.abs(item.amount).toFixed(2)}
                                                </div>
                                            )}
                                            {item.metadata?.score !== undefined && (
                                                <div className={styles.itemMetric}>{item.metadata.score}</div>
                                            )}
                                            <div className={styles.itemTime}>{new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))
                )}
                {!loading && historyGroups.length === 0 && (
                    <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>No history found.</div>
                )}
            </div>
        </div>
    );
};

export default History;
