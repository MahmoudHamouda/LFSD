import React from 'react';
import { Link, Outlet, useLocation } from 'react-router-dom';
import Sidebar from '../../components/layout/Sidebar';
import { Users, FileText, Shield, ArrowLeft, BarChart3, CreditCard } from 'lucide-react';

const AdminLayout: React.FC = () => {
    const location = useLocation();
    const [isSidebarOpen, setIsSidebarOpen] = React.useState(true);
    const [isSidebarCollapsed, setIsSidebarCollapsed] = React.useState(false);

    const isActive = (path: string) => location.pathname.includes(path);

    const navItems = [
        { path: '/admin/users', label: 'User Management', icon: Users },
        { path: '/admin/subscriptions', label: 'Subscriptions', icon: CreditCard },
        { path: '/admin/billing', label: 'Billing & Reconciliation', icon: BarChart3 },
        { path: '/admin/audit', label: 'Audit Logs', icon: FileText },
    ];

    return (
        <div style={{ display: 'flex', height: '100vh', backgroundColor: '#111' }}>
            {/* Reuse main Sidebar for consistency, or we could make a custom one */}
            <Sidebar
                isOpen={isSidebarOpen}
                isCollapsed={isSidebarCollapsed}
                onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
                onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                onNewChat={() => { }} // No-op for admin
                onOpenSettings={() => { }}
            />

            <main style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                <header style={{
                    padding: '16px 24px',
                    borderBottom: '1px solid #333',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '16px',
                    backgroundColor: '#1a1a1a'
                }}>
                    <Link to="/" style={{ color: '#888', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <ArrowLeft size={16} /> Back to App
                    </Link>
                    <div style={{ width: '1px', height: '20px', backgroundColor: '#333' }}></div>
                    <h2 style={{ margin: 0, fontSize: '18px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Shield size={18} color="#4ade80" />
                        Admin Console
                    </h2>

                    <nav style={{ marginLeft: '40px', display: 'flex', gap: '20px' }}>
                        {navItems.map(item => (
                            <Link
                                key={item.path}
                                to={item.path}
                                style={{
                                    textDecoration: 'none',
                                    color: isActive(item.path) ? '#4ade80' : '#888',
                                    fontWeight: isActive(item.path) ? 600 : 400,
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '6px',
                                    fontSize: '14px'
                                }}
                            >
                                <item.icon size={14} />
                                {item.label}
                            </Link>
                        ))}
                    </nav>
                </header>

                <div style={{ flex: 1, overflow: 'auto', padding: '24px' }}>
                    <Outlet />
                </div>
            </main>
        </div>
    );
};

export default AdminLayout;
