import React from 'react';
import styles from './FinancialSummary.module.css';

interface BreakdownItem {
    category: string;
    amount: number;
    percentage: number;
}

interface FinancialSummaryProps {
    total: number;
    period: string;
    breakdown: BreakdownItem[];
    category?: string;
}

const FinancialSummary: React.FC<FinancialSummaryProps> = ({ total, period, breakdown, category }) => {
    const isCategoryView = category && category !== 'all';

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <div className={styles.title}>Spending Summary</div>
                <div className={styles.period}>{period}</div>
            </div>

            <div className={styles.totalSection}>
                <div className={styles.currency}>AED</div>
                <div className={styles.amount}>{total.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                {isCategoryView && <div className={styles.categoryLabel}>on {category}</div>}
            </div>

            {!isCategoryView && (
                <div className={styles.breakdownList}>
                    {breakdown.map((item, index) => (
                        <div key={index} className={styles.breakdownItem}>
                            <div className={styles.itemHeader}>
                                <span className={styles.itemCategory}>{item.category}</span>
                                <span className={styles.itemAmount}>AED {item.amount.toLocaleString()}</span>
                            </div>
                            <div className={styles.progressBarBg}>
                                <div
                                    className={styles.progressBarFill}
                                    style={{ width: `${item.percentage}%`, backgroundColor: getCategoryColor(index) }}
                                ></div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

const getCategoryColor = (index: number) => {
    const colors = ['#4dabf7', '#51cf66', '#fcc419', '#ff6b6b', '#845ef7'];
    return colors[index % colors.length];
};

export default FinancialSummary;
