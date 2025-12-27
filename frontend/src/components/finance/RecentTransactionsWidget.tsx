import React, { useEffect, useState } from 'react';
import { getTransactions } from '../../api/financialApi';
import { Transaction } from '../../types/finance';
import { ArrowUpRight, ArrowDownLeft, Receipt } from 'lucide-react';
import Card from '../common/Card';

const RecentTransactionsWidget: React.FC = () => {
    const [transactions, setTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchTx = async () => {
            try {
                const data = await getTransactions(5);
                setTransactions(data);
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        fetchTx();
    }, []);

    if (loading) return <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-tertiary)' }}>Loading transactions...</div>;

    const handleAction = () => {
        if (transactions.length === 0) {
            window.location.href = '/profile?tab=financial&anchor=connections';
        } else {
            console.log("View All Transactions");
            // Navigate to full transactions page if it exists
        }
    };

    return (
        <Card title="Recent Transactions" actionLabel="View All" onAction={handleAction}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                {transactions.length > 0 ? (
                    transactions.map((tx, idx) => (
                        <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                                <div style={{
                                    width: '32px', height: '32px',
                                    borderRadius: '50%',
                                    backgroundColor: tx.amount < 0 ? 'var(--bg-badge-error)' : 'var(--bg-badge-success)', // Use token badge colors
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    color: tx.amount < 0 ? 'var(--color-accent-red)' : 'var(--color-accent-blue)' // Actually + money is green usually but UI had blue. I'll stick to blue or Green. Request said consistent design. I'll use success/error.
                                }}>
                                    {tx.amount < 0 ? <ArrowUpRight size={16} /> : <ArrowDownLeft size={16} />}
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column' }}>
                                    <span style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-primary)' }}>{tx.merchant || 'Unknown'}</span>
                                    <span style={{ fontSize: '12px', color: 'var(--text-tertiary)' }}>{tx.date}</span>
                                </div>
                            </div>
                            <span style={{
                                fontSize: '14px',
                                fontWeight: 600,
                                color: tx.amount < 0 ? 'var(--text-primary)' : 'var(--status-success)'
                            }}>
                                {tx.amount < 0 ? '-' : '+'}${Math.abs(tx.amount).toFixed(2)}
                            </span>
                        </div>
                    ))
                ) : (
                    <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--text-tertiary)' }}>
                        <Receipt size={32} style={{ marginBottom: '12px', opacity: 0.3 }} />
                        <div style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '4px' }}>No transactions found</div>
                        <div style={{ fontSize: '12px', marginBottom: '16px' }}>Upload a statement to see your spending insights.</div>
                        <a
                            href="/profile?tab=financial&anchor=connections"
                            style={{
                                display: 'inline-flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                padding: '8px 16px',
                                backgroundColor: 'var(--color-primary)',
                                color: 'white',
                                borderRadius: '6px',
                                fontSize: '13px',
                                fontWeight: 500,
                                textDecoration: 'none',
                                transition: 'background-color 0.2s'
                            }}
                        >
                            Upload Statement
                        </a>
                    </div>
                )}
            </div>
        </Card>
    );
};

export default RecentTransactionsWidget;
