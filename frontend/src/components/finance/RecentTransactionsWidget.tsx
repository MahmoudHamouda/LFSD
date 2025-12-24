import React, { useEffect, useState } from 'react';
import { getTransactions } from '../../api/financialApi';
import { Transaction } from '../../types/finance';
import { ArrowUpRight, ArrowDownLeft, Receipt } from 'lucide-react';

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

    if (loading) return <div style={{ padding: '20px', textAlign: 'center', color: '#888' }}>Loading transactions...</div>;

    return (
        <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            border: '1px solid var(--border-color)',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            height: 'fit-content'
        }}>
            <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Recent Transactions</h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {transactions.length > 0 ? (
                    transactions.map((tx, idx) => (
                        <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                <div style={{
                                    width: '32px', height: '32px',
                                    borderRadius: '50%',
                                    backgroundColor: tx.amount < 0 ? '#FEF2F2' : '#EFF6FF',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    color: tx.amount < 0 ? '#EF4444' : '#3B82F6'
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
                                color: tx.amount < 0 ? 'var(--text-primary)' : '#10B981'
                            }}>
                                {tx.amount < 0 ? '-' : '+'}${Math.abs(tx.amount).toFixed(2)}
                            </span>
                        </div>
                    ))
                ) : (
                    <div style={{ textAlign: 'center', padding: '20px 0', color: 'var(--text-tertiary)' }}>
                        <Receipt size={24} style={{ marginBottom: '8px', opacity: 0.5 }} />
                        <div style={{ fontSize: '13px' }}>No recent transactions</div>
                    </div>
                )}
            </div>

            <button style={{
                width: '100%',
                padding: '8px',
                background: 'transparent',
                border: '1px solid var(--border-color)',
                borderRadius: '6px',
                color: 'var(--text-secondary)',
                fontSize: '13px',
                cursor: 'pointer'
            }}>
                View All
            </button>
        </div>
    );
};

export default RecentTransactionsWidget;
