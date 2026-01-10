import React, { useEffect, useState } from 'react';
import { getAuditLogs, AuditLogItem } from '../../api/adminApi';
import { FileJson, User, Monitor, Clock } from 'lucide-react';

const AuditViewer: React.FC = () => {
    const [logs, setLogs] = useState<AuditLogItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expandedId, setExpandedId] = useState<string | null>(null);

    const fetchLogs = async () => {
        try {
            setLoading(true);
            const data = await getAuditLogs(50);
            setLogs(data);
            setError(null);
        } catch (err) {
            setError('Failed to load audit logs');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchLogs();
    }, []);

    if (loading) return <div style={{ color: '#888' }}>Loading logs...</div>;
    if (error) return <div style={{ color: '#ef4444' }}>{error}</div>;

    return (
        <div>
            <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ margin: 0, color: '#fff' }}>Audit Trail (Last 50)</h3>
                <button
                    onClick={fetchLogs}
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

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {logs.map(log => (
                    <div
                        key={log.id}
                        style={{
                            backgroundColor: '#1a1a1a',
                            borderRadius: '8px',
                            padding: '16px',
                            border: '1px solid #333'
                        }}
                    >
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{
                                    backgroundColor: '#2563eb',
                                    color: '#fff',
                                    fontSize: '11px',
                                    padding: '2px 6px',
                                    borderRadius: '4px',
                                    fontWeight: 600
                                }}>
                                    {log.action}
                                </span>
                                <span style={{ color: '#ccc', fontWeight: 500 }}>
                                    {log.entity_type} <span style={{ color: '#666' }}>#{log.entity_id}</span>
                                </span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#666', fontSize: '12px' }}>
                                <Clock size={12} />
                                {new Date(log.timestamp).toLocaleString()}
                            </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: '#888', marginBottom: '12px' }}>
                            <User size={12} />
                            Actor: <span style={{ color: '#aaa' }}>{log.actor_id || 'System'}</span>
                        </div>

                        {log.changes_json && (
                            <div style={{ marginTop: '8px' }}>
                                <button
                                    onClick={() => setExpandedId(expandedId === log.id ? null : log.id)}
                                    style={{
                                        background: 'none',
                                        border: 'none',
                                        color: '#4ade80',
                                        fontSize: '12px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '4px',
                                        cursor: 'pointer',
                                        padding: 0
                                    }}
                                >
                                    <FileJson size={12} />
                                    {expandedId === log.id ? 'Hide Details' : 'Show Details'}
                                </button>

                                {expandedId === log.id && (
                                    <pre style={{
                                        marginTop: '8px',
                                        backgroundColor: '#111',
                                        padding: '12px',
                                        borderRadius: '6px',
                                        fontSize: '12px',
                                        color: '#ccc',
                                        overflow: 'auto'
                                    }}>
                                        {JSON.stringify(log.changes_json, null, 2)}
                                    </pre>
                                )}
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default AuditViewer;
