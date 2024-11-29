import React, { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from 'recharts';

import styles from './Dashboard.module.css';

const Dashboard = () => {
  const [financialData, setFinancialData] = useState({
    savings: 0,
    debts: 0,
    expenses: 0,
    income: 0,
    affordabilityAnalysis: [],
  });

  useEffect(() => {
    // Fetch data from the backend (API integration)
    fetch('/api/financial/overview')
      .then(response => response.json())
      .then(data => setFinancialData(data));
  }, []);

  const COLORS = ['#FF6A00', '#005BFF', '#CCCCCC', '#333333'];

  const pieData = [
    { name: 'Savings', value: financialData.savings },
    { name: 'Income', value: financialData.income },
    { name: 'Debts', value: financialData.debts },
    { name: 'Expenses', value: financialData.expenses },
  ];

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Financial Health Overview</h1>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={pieData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={100}
            fill="#8884d8"
            label
          >
            {pieData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default Dashboard;
