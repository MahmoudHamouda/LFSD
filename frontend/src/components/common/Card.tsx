import React, { ReactNode } from 'react';
import styles from './Card.module.css';

interface CardProps {
    children: ReactNode;
    title?: string;
    className?: string;
    actionLabel?: string;
    onAction?: () => void;
    style?: React.CSSProperties;
}

export const Card: React.FC<CardProps> = ({
    children,
    title,
    className = '',
    actionLabel,
    onAction,
    style
}) => {
    return (
        <div className={`${styles.card} ${className}`} style={style}>
            {title && <h3 className={styles.cardTitle}>{title}</h3>}
            <div className={styles.cardContent}>
                {children}
            </div>
            {actionLabel && (
                <button className={styles.cardAction} onClick={onAction}>
                    {actionLabel}
                </button>
            )}
        </div>
    );
};

export default Card;
