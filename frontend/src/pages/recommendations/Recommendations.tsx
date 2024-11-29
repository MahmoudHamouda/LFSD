import React, { useState, useEffect } from 'react';

import styles from './Recommendations.module.css';

const Recommendations = () => {
    const [recommendations, setRecommendations] = useState([]);

    useEffect(() => {
        // Fetch recommendations from the backend
        fetch('/api/recommendations')
            .then(response => response.json())
            .then(data => setRecommendations(data));
    }, []);

    return (
        <div className={styles.container}>
            <h1>Personalized Recommendations</h1>
            <ul className={styles.list}>
                {recommendations.map((rec, index) => (
                    <li key={index} className={styles.item}>
                        {rec}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default Recommendations;
