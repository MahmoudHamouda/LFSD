import React, { useState, useEffect } from 'react';
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

interface Location {
    lat: number;
    lng: number;
    address?: string;
}

interface RideOptionsProps {
    destination: string;
    options: RideOption[];
    cheapest?: RideOption;
    onBook: (option: RideOption, location: Location | string) => void;
}

const RideOptions: React.FC<RideOptionsProps> = ({ destination, options, cheapest, onBook }) => {
    const [location, setLocation] = useState<Location | null>(null);
    const [manualAddress, setManualAddress] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [useManual, setUseManual] = useState(false);

    useEffect(() => {
        if (!navigator.geolocation) {
            setError('Geolocation is not supported by your browser');
            setLoading(false);
            setUseManual(true);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                setLocation({
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                });
                setLoading(false);
            },
            (err) => {
                console.warn("Geolocation error:", err);
                setError('Location access denied. Please enter pickup location.');
                setLoading(false);
                setUseManual(true);
            }
        );
    }, []);

    const handleBook = (option: RideOption) => {
        if (location) {
            onBook(option, location);
        } else if (manualAddress.trim()) {
            onBook(option, manualAddress);
        }
    };

    const isReady = !!location || (useManual && manualAddress.trim().length > 0);

    const getStatusMessage = () => {
        if (loading) return "Locating you for accurate pickup...";
        if (error) return error;
        if (location) return "Pickup location set via GPS";
        return "Please provide a pickup location";
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <span>Ride options to <strong>{destination}</strong></span>
            </div>

            <div className={styles.locationStatus}>
                <div className={`${styles.statusBadge} ${loading ? styles.loading : error ? styles.error : styles.success}`}>
                    <div className={styles.statusDot} />
                    <span>{getStatusMessage()}</span>
                </div>

                {(error || useManual) && (
                    <div className={styles.manualInputGroup}>
                        <input
                            type="text"
                            placeholder="Type pickup address (e.g. Burj Khalifa)"
                            value={manualAddress}
                            onChange={(e) => setManualAddress(e.target.value)}
                            className={styles.addressInput}
                        />
                    </div>
                )}
            </div>

            <div className={styles.optionsList}>
                {options.map((option) => (
                    <button
                        key={option.id}
                        className={`${styles.optionCard} ${option.recommended ? styles.recommended : ''} ${!isReady ? styles.disabled : ''}`}
                        onClick={() => isReady && handleBook(option)}
                        disabled={!isReady}
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
                    </button>
                ))}
            </div>
        </div>
    );
};

export default RideOptions;
