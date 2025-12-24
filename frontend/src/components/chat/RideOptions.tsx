import React from 'react';
import styles from './RideOptions.module.css';

interface RideOption {
    id: string;
    provider: string;
    type: string;
    price: string;
    eta: string;
    recommended?: boolean;
    reasoning?: string;
}

interface RideOptionsProps {
    destination: string;
    options: RideOption[];
    cheapest?: RideOption;
    onBook: (option: RideOption) => void;
}

const RideOptions: React.FC<RideOptionsProps> = ({ destination, options, cheapest, onBook }) => {
    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span>Ride options to <strong>{destination}</strong></span>
            </div>

            <div className={styles.optionsList}>
                {options.map((option) => (
                    <div
                        key={option.id}
                        className={`${styles.optionCard} ${option.recommended ? styles.recommended : ''}`}
                        onClick={() => onBook(option)}
                    >
                        <div className={styles.providerInfo}>
                            <div className={styles.providerName}>{option.provider}</div>
                            <div className={styles.rideType}>{option.type}</div>
                        </div>

                        <div className={styles.rideDetails}>
                            <div className={styles.price}>{option.price}</div>
                            <div className={styles.eta}>{option.eta} mins</div>
                        </div>

                        {option.recommended && (
                            <div className={styles.badge}>Recommended</div>
                        )}

                        {option.recommended && option.reasoning && (
                            <div className={styles.reasoning}>{option.reasoning}</div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default RideOptions;
