import React, { useEffect, useState } from 'react';
import {
    getBillingSummary,
    getCustomerReconciliation,
    getAPICostBreakdown,
    BillingSummary,
    CustomerReconciliation,
    APICostBreakdown
} from '../../api/adminApi';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend
} from 'recharts';
import {
    DollarSign, TrendingDown, TrendingUp, Users, Activity,
    ExternalLink, RefreshCw, AlertCircle
} from 'lucide-react';

const COLORS = ['#4ade80', '#f87171', '#fbbf24', '#60a5fa'];

const BillingReconciliation: React.FC = () => {
    const [summary, setSummary] = useState<BillingSummary | null>(null);
    const [customers, setCustomers] = useState<CustomerReconciliation[]>([]);
    const [apis, setApis] = useState<APICostBreakdown[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [s, c, a] = await Promise.all([
                getBillingSummary(),
                getCustomerReconciliation(),
                getAPICostBreakdown()
            ]);
            setSummary(s);
            setCustomers(c);
            setApis(a);
            setError(null);
        } catch (err: any) {
            setError(err.message || 'Failed to load billing data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    if (loading) return <div style={{ color: '#888', padding: '20px' }}>Loading financial data...</div>;
    if (error) return (
        <div style={{ color: '#ef4444', padding: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={20} />
            {error}
        </div>
    );

    const pieData = summary ? [
        { name: 'Revenue', value: summary.total_revenue },
        { name: 'Cost', value: summary.total_cost },
    ] : [];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ margin: 0, color: '#fff' }}>Billing & Reconciliation</h3>
                <button
                    onClick={fetchData}
                    style={{
                        background: '#333',
                        color: '#fff',
                        border: 'none',
                        padding: '8px 16px',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                    }}
                >
                    <RefreshCw size={14} /> Refresh
                </button>
            </div>

            {/* Summary Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
                <div style={{ backgroundColor: '#1a1a1a', padding: '20px', borderRadius: '12px', border: '1px solid #333' }}>
                    <div style={{ color: '#888', fontSize: '13px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <DollarSign size={14} color="#4ade80" /> Total Revenue
                    </div>
                    <div style={{ fontSize: '24px', fontWeight: 600, color: '#fff' }}>${summary?.total_revenue.toFixed(2)}</div>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>From {summary?.metrics.active_subscribers} active subscriptions</div>
                </div>
                <div style={{ backgroundColor: '#1a1a1a', padding: '20px', borderRadius: '12px', border: '1px solid #333' }}>
                    <div style={{ color: '#888', fontSize: '13px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <TrendingDown size={14} color="#f87171" /> Total Cost
                    </div>
                    <div style={{ fontSize: '24px', fontWeight: 600, color: '#fff' }}>${summary?.total_cost.toFixed(2)}</div>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>AI and API provider fees</div>
                </div>
                <div style={{ backgroundColor: '#1a1a1a', padding: '20px', borderRadius: '12px', border: '1px solid #333' }}>
                    <div style={{ color: '#888', fontSize: '13px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <TrendingUp size={14} color={summary && summary.profit >= 0 ? '#4ade80' : '#f87171'} /> Net Profit
                    </div>
                    <div style={{ fontSize: '24px', fontWeight: 600, color: summary && summary.profit >= 0 ? '#4ade80' : '#f87171' }}>
                        ${summary?.profit.toFixed(2)}
                    </div>
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>Margin: {summary && summary.total_revenue > 0 ? ((summary.profit / summary.total_revenue) * 100).toFixed(1) : 0}%</div>
                </div>
            </div>

            {/* Charts Row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>
                <div style={{ backgroundColor: '#1a1a1a', padding: '24px', borderRadius: '12px', border: '1px solid #333', height: '350px' }}>
                    <h4 style={{ margin: '0 0 20px 0', fontSize: '16px', color: '#fff' }}>Revenue vs Cost</h4>
                    <ResponsiveContainer width="100%" height="80%">
                        <PieChart>
                            <Pie
                                data={pieData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {pieData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{ backgroundColor: '#222', border: '1px solid #444', color: '#fff' }}
                                itemStyle={{ color: '#fff' }}
                            />
                            <Legend verticalAlign="bottom" height={36} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                <div style={{ backgroundColor: '#1a1a1a', padding: '24px', borderRadius: '12px', border: '1px solid #333', height: '350px' }}>
                    <h4 style={{ margin: '0 0 20px 0', fontSize: '16px', color: '#fff' }}>Customer Margin Breakdown (Sample)</h4>
                    <ResponsiveContainer width="100%" height="80%">
                        <BarChart data={customers.slice(0, 10)}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                            <XAxis dataKey="email" hide />
                            <YAxis stroke="#666" fontSize={12} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#222', border: '1px solid #444', color: '#fff' }}
                                labelStyle={{ color: '#888' }}
                            />
                            <Bar dataKey="margin" fill="#4ade80" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* API Integration Costs Table */}
            <div style={{ backgroundColor: '#1a1a1a', borderRadius: '12px', border: '1px solid #333', overflow: 'hidden' }}>
                <div style={{ padding: '16px 20px', borderBottom: '1px solid #333', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Activity size={16} color="#4ade80" />
                    <h4 style={{ margin: 0, fontSize: '15px', color: '#fff' }}>API Integration Costs</h4>
                </div>
                <table style={{ width: '100%', borderCollapse: 'collapse', color: '#ccc', fontSize: '14px' }}>
                    <thead>
                        <tr style={{ textAlign: 'left', backgroundColor: '#222' }}>
                            <th style={{ padding: '12px 20px', color: '#888' }}>Integration Provider</th>
                            <th style={{ padding: '12px 20px', color: '#888' }}>Usage Unit</th>
                            <th style={{ padding: '12px 20px', color: '#888' }}>Total Usage</th>
                            <th style={{ padding: '12px 20px', color: '#888' }}>Accrued Cost</th>
                        </tr>
                    </thead>
                    <tbody>
                        {apis.map((api, idx) => (
                            <tr key={idx} style={{ borderBottom: '1px solid #222' }}>
                                <td style={{ padding: '16px 20px', color: '#fff', fontWeight: 500 }}>{api.integration}</td>
                                <td style={{ padding: '16px 20px' }}>{api.unit}</td>
                                <td style={{ padding: '16px 20px' }}>{api.usage.toLocaleString()}</td>
                                <td style={{ padding: '16px 20px', color: '#f87171' }}>${api.total_cost.toFixed(4)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Customer Reconciliation Table */}
            <div style={{ backgroundColor: '#1a1a1a', borderRadius: '12px', border: '1px solid #333', overflow: 'hidden' }}>
                <div style={{ padding: '16px 20px', borderBottom: '1px solid #333', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Users size={16} color="#4ade80" />
                    <h4 style={{ margin: 0, fontSize: '15px', color: '#fff' }}>Per-Customer Reconciliation</h4>
                </div>
                <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', color: '#ccc', fontSize: '14px' }}>
                        <thead style={{ position: 'sticky', top: 0, backgroundColor: '#222', zIndex: 1 }}>
                            <tr style={{ textAlign: 'left' }}>
                                <th style={{ padding: '12px 20px', color: '#888' }}>Customer</th>
                                <th style={{ padding: '12px 20px', color: '#888' }}>Plan</th>
                                <th style={{ padding: '12px 20px', color: '#888' }}>Revenue</th>
                                <th style={{ padding: '12px 20px', color: '#888' }}>Cost</th>
                                <th style={{ padding: '12px 20px', color: '#888' }}>Margin</th>
                            </tr>
                        </thead>
                        <tbody>
                            {customers.map((cust) => (
                                <tr key={cust.user_id} style={{ borderBottom: '1px solid #222' }}>
                                    <td style={{ padding: '16px 20px' }}>
                                        <div style={{ color: '#fff', fontWeight: 500 }}>{cust.email}</div>
                                        <div style={{ fontSize: '11px', color: '#666' }}>{cust.user_id}</div>
                                    </td>
                                    <td style={{ padding: '16px 20px' }}>
                                        <span style={{
                                            textTransform: 'capitalize',
                                            fontSize: '11px',
                                            padding: '2px 8px',
                                            borderRadius: '10px',
                                            backgroundColor: cust.plan === 'tier_pro' ? '#fbbf2420' : '#333',
                                            color: cust.plan === 'tier_pro' ? '#fbbf24' : '#888',
                                            border: `1px solid ${cust.plan === 'tier_pro' ? '#fbbf2440' : '#444'}`
                                        }}>
                                            {cust.plan.replace('tier_', '')}
                                        </span>
                                    </td>
                                    <td style={{ padding: '16px 20px', color: '#4ade80' }}>+${cust.revenue.toFixed(2)}</td>
                                    <td style={{ padding: '16px 20px', color: '#f87171' }}>-${cust.cost.toFixed(2)}</td>
                                    <td style={{
                                        padding: '16px 20px',
                                        fontWeight: 600,
                                        color: cust.margin >= 0 ? '#4ade80' : '#f87171'
                                    }}>
                                        {cust.margin >= 0 ? '+' : ''}${cust.margin.toFixed(2)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default BillingReconciliation;
