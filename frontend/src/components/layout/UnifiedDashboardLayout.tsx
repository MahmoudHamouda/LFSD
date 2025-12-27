import React from 'react';
import styles from './UnifiedDashboardLayout.module.css';

interface UnifiedDashboardLayoutProps {
    hero: React.ReactNode;
    indicators: React.ReactNode;
    pillars: React.ReactNode;
}

export const UnifiedDashboardLayout: React.FC<UnifiedDashboardLayoutProps> = ({
    hero,
    indicators,
    pillars
}) => {
    return (
        <div className={styles.container}>
            {/* Top Row: Hero (Score + Goal) */}
            <div className={styles.heroRow}>
                {hero}
            </div>

            {/* Bottom Row: Content Grid */}
            <div className={styles.contentGrid}>
                {/* Left Column (1/3): Operational/Indicators */}
                <div className={styles.leftColumn}>
                    {indicators}
                </div>

                {/* Right Column (2/3): Analytical/Pillars */}
                <div className={styles.rightColumn}>
                    {pillars}
                </div>
            </div>
        </div>
    );
};
