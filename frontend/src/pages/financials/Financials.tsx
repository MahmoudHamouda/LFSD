import React, { useEffect, useState } from 'react';
import styles from './Financials.module.css';
import { getFinancialAccounts, getTransactions } from '../../api/financialApi';
import { FinancialAccount, Transaction } from '../../types/finance';

const Financials = () => {
    const [accounts, setAccounts] = useState<FinancialAccount[]>([]);
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadData = async () => {
            try {
                const [accountsData, transactionsData] = await Promise.all([
                    getFinancialAccounts(),
                    getTransactions(20)
                ]);
                setAccounts(accountsData);
                setTransactions(transactionsData);
            } catch (error) {
                console.error("Failed to load financial data", error);
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    if (loading) return <div className={styles.container}>Loading Financials...</div>;

    const formatCurrency = (amount: number, currency: string = 'USD') => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: currency,
        }).format(amount);
    };

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h1 className={styles.title}>Deep Finance</h1>
            </div>

            <div className={styles.accountsGrid}>
                {accounts.map(account => (
                    <div key={account.id} className={styles.accountCard}>
                        <span className={styles.accountType}>{account.accountType}</span>
                        <span className={styles.accountName}>{account.institutionName}</span>
                        <span className={styles.accountBalance}>{formatCurrency(account.currentBalance)}</span>
                    </div>
                ))}
                {accounts.length === 0 && <p>No accounts connected.</p>}
            </div>

            <h2 className={styles.sectionTitle}>Recent Transactions</h2>
            <div className={styles.transactionsList}>
                {transactions.map(txn => (
                    <div key={txn.id} className={styles.transactionItem}>
                        <div className={styles.transactionInfo}>
                            <span className={styles.merchantName}>{txn.merchantName}</span>
                            <span className={styles.transactionCategory}>{txn.categoryPrimary} • {new Date(txn.transactionDate).toLocaleDateString()}</span>
                        </div>
                        <span className={`${styles.transactionAmount} ${txn.amount > 0 ? styles.amountPositive : styles.amountNegative}`}>
                            {txn.amount > 0 ? '+' : ''}{formatCurrency(txn.amount, txn.currencyCode)}
                        </span>
                    </div>
                ))}
                {transactions.length === 0 && <div className={styles.transactionItem}>No transactions found.</div>}
            </div>
        </div>
    );
};

export default Financials;
