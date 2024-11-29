import React, { useState, useEffect } from 'react';

import styles from './UserProfile.module.css';

const UserProfile = () => {
    const [userData, setUserData] = useState({
        name: '',
        address: '',
        savingsGoals: [],
        recurringExpenses: [],
        debts: [],
    });

    useEffect(() => {
        // Fetch user data from the backend
        fetch('/api/user/profile')
            .then(response => response.json())
            .then(data => setUserData(data));
    }, []);

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setUserData({ ...userData, [name]: value });
    };

    const handleFormSubmit = (e) => {
        e.preventDefault();
        // Submit updated data to the backend
        fetch('/api/user/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData),
        });
    };

    return (
        <form className={styles.form} onSubmit={handleFormSubmit}>
            <label>
                Name:
                <input type="text" name="name" value={userData.name} onChange={handleInputChange} />
            </label>
            <label>
                Address:
                <input type="text" name="address" value={userData.address} onChange={handleInputChange} />
            </label>
            <div>
                <h3>Savings Goals</h3>
                {userData.savingsGoals.map((goal, index) => (
                    <p key={index}>{goal}</p>
                ))}
            </div>
            <div>
                <h3>Recurring Expenses</h3>
                {userData.recurringExpenses.map((expense, index) => (
                    <p key={index}>{expense}</p>
                ))}
            </div>
            <div>
                <h3>Debts</h3>
                {userData.debts.map((debt, index) => (
                    <p key={index}>{debt}</p>
                ))}
            </div>
            <button type="submit">Save Changes</button>
        </form>
    );
};

export default UserProfile;
