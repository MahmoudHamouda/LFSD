import React, { useEffect, useState } from 'react';
import { getAdminUsers, unlockUser, AdminUser } from '../../api/adminApi';
import { Lock, Unlock, Search, AlertCircle, CheckCircle } from 'lucide-react';

const UserManagement: React.FC = () => {
    const [users, setUsers] = useState<AdminUser[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [actionLoading, setActionLoading] = useState<string | null>(null);

    const fetchUsers = async () => {
        try {
            setLoading(true);
            const data = await getAdminUsers();
            setUsers(data);
            setError(null);
        } catch (err) {
            setError('Failed to load users');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleUnlock = async (userId: string) => {
        try {
            setActionLoading(userId);
            await unlockUser(userId, "Manual unlock via Admin Console");
            // Optimistic update
            setUsers(users.map(u => u.id === userId ? { ...u, account_status: 'ACTIVE' } : u));
        } catch (err: any) {
            alert(`Failed to unlock: ${err.message}`);
        } finally {
            setActionLoading(null);
        }
    };

    if (loading) return <div style={{ color: '#888' }}>Loading users...</div>;
    if (error) return <div style={{ color: '#ef4444' }}>{error}</div>;

    return (
        <div>
            <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ margin: 0, color: '#fff' }}>Users</h3>
                <button
                    onClick={fetchUsers}
                    style={{
                        background: '#333',
                        color: '#fff',
                        border: 'none',
                        padding: '8px 16px',
                        borderRadius: '6px',
                        cursor: 'pointer'
                    }}
                >
                    Refresh
                </button>
            </div>

            <div style={{ backgroundColor: '#1a1a1a', borderRadius: '8px', overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', color: '#ccc', fontSize: '14px' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid #333', textAlign: 'left' }}>
                            <th style={{ padding: '12px 16px', color: '#888' }}>ID / Email</th>
                            <th style={{ padding: '12px 16px', color: '#888' }}>Joined</th>
                            <th style={{ padding: '12px 16px', color: '#888' }}>Status</th>
                            <th style={{ padding: '12px 16px', color: '#888' }}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {users.map(user => (
                            <tr key={user.id} style={{ borderBottom: '1px solid #222' }}>
                                <td style={{ padding: '12px 16px' }}>
                                    <div style={{ color: '#fff', fontWeight: 500 }}>{user.email}</div>
                                    <div style={{ fontSize: '11px', color: '#666' }}>{user.id}</div>
                                </td>
                                <td style={{ padding: '12px 16px' }}>
                                    {new Date(user.created_at).toLocaleDateString()}
                                </td>
                                <td style={{ padding: '12px 16px' }}>
                                    {user.account_status === 'ACTIVE' ? (
                                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#4ade80', backgroundColor: '#4ade8020', padding: '4px 8px', borderRadius: '12px', fontSize: '12px' }}>
                                            <CheckCircle size={12} /> Active
                                        </span>
                                    ) : (
                                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: '#ef4444', backgroundColor: '#ef444420', padding: '4px 8px', borderRadius: '12px', fontSize: '12px' }}>
                                            <Lock size={12} /> {user.account_status}
                                        </span>
                                    )}
                                </td>
                                <td style={{ padding: '12px 16px' }}>
                                    {user.account_status !== 'ACTIVE' && (
                                        <button
                                            onClick={() => handleUnlock(user.id)}
                                            disabled={actionLoading === user.id}
                                            style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '6px',
                                                backgroundColor: '#3b82f6',
                                                color: '#fff',
                                                border: 'none',
                                                padding: '6px 12px',
                                                borderRadius: '4px',
                                                cursor: actionLoading === user.id ? 'not-allowed' : 'pointer',
                                                fontSize: '12px'
                                            }}
                                        >
                                            <Unlock size={12} />
                                            {actionLoading === user.id ? 'Unlocking...' : 'Unlock'}
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {users.length === 0 && (
                    <div style={{ padding: '32px', textAlign: 'center', color: '#666' }}>
                        No users found.
                    </div>
                )}
            </div>
        </div>
    );
};

export default UserManagement;
