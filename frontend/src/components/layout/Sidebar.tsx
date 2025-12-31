import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
    MessageSquare,
    Plus,
    ChevronLeft,
    ChevronRight,
    ChevronDown,
    MessageCircle,
    Trash2,
    User,
    ExternalLink,
    LogOut
} from 'lucide-react';
import styles from './Sidebar.module.css';


interface SidebarProps {
    isOpen: boolean;
    isCollapsed: boolean;
    onToggle: () => void;
    onToggleCollapse: () => void;
    onNewChat: () => void;
    onOpenSettings: () => void;
}

// Real conversations state
interface Conversation {
    id: string;
    title: string;
    date: string;
    // messages?: any[];
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, isCollapsed, onToggle, onToggleCollapse, onNewChat, onOpenSettings }) => {
    const navigate = useNavigate();
    const [conversations, setConversations] = useState<Conversation[]>([]);
    const [isConversationsExpanded, setIsConversationsExpanded] = useState(true);

    const handleNavigation = (path: string) => {
        navigate(path);
        if (window.innerWidth <= 768) {
            onToggle();
        }
    };

    useEffect(() => {
        const loadHistory = async () => {
            // dynamic import to avoid circular dependencies if any, or just standard import
            try {
                // Ideally this should be a direct import if possible, but keeping existing pattern or fixing it.
                // Assuming historyList is exported from api/api
                const { historyList } = await import('../../api/api');
                const data = await historyList();
                if (data) {
                    const lastCleared = localStorage.getItem('lastClearedHistory');
                    const filteredData = lastCleared
                        ? data.filter((c: Conversation) => new Date(c.date) > new Date(lastCleared))
                        : data;
                    setConversations(filteredData);
                }
            } catch (e) {
                console.error("Failed to load history", e);
            }
        };
        loadHistory();
    }, []);

    return (
        <aside className={`${styles.sidebar} ${!isOpen ? styles.closed : ''} ${isCollapsed ? styles.collapsed : ''}`}>
            <div className={`${styles.header} ${isCollapsed ? styles.collapsed : ''}`}>
                {/* Brand Logo - H Mark only */}
                {!isCollapsed && (
                    <Link to="/" style={{ display: 'flex', alignItems: 'center', textDecoration: 'none', color: 'inherit' }}>
                        <h1 style={{ margin: 0, marginRight: '16px', fontSize: '24px', fontWeight: 'bold', fontFamily: 'var(--font-heading)' }}>H</h1>
                    </Link>
                )}

                <button className={styles.toggleButton} onClick={onToggleCollapse} title={isCollapsed ? "Expand Sidebar" : "Collapse Sidebar"}>
                    {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                </button>
                <button className={styles.newChatButton} onClick={onNewChat} title="New Chat">
                    <span className={styles.icon}><Plus size={18} /></span>
                    <span>New chat</span>
                </button>
            </div>

            <div className={styles.content}>
                {/* Conversations Section */}
                <div className={styles.topLevelItem}>
                    <button
                        className={`${styles.topLevelHeader} ${isConversationsExpanded ? styles.active : ''}`}
                        onClick={() => setIsConversationsExpanded(!isConversationsExpanded)}
                        title="Conversations"
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <span className={styles.icon}><MessageSquare size={18} /></span>
                            <span>Conversations</span>
                        </div>
                        <span className={`${styles.expandIcon} ${isConversationsExpanded ? styles.expanded : ''}`}>
                            <ChevronDown size={14} />
                        </span>
                    </button>

                    <div className={`${styles.topLevelContent} ${isConversationsExpanded ? styles.expanded : ''}`}>
                        {conversations.map(conv => (
                            <button
                                key={conv.id}
                                className={styles.connectorItem}
                                onClick={() => handleNavigation(`/chat?id=${conv.id}`)}
                                title={conv.title}
                            >
                                <span className={styles.icon} style={{ fontSize: '12px', display: 'flex', alignItems: 'center' }}>
                                    <MessageCircle size={14} />
                                </span>
                                <span>{conv.title || 'New Chat'}</span>
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            <div className={styles.footer}>
                <button className={styles.menuItem} onClick={() => handleNavigation('/profile')} title="My account">
                    <span className={styles.icon}><User size={18} /></span>
                    <span>My account</span>
                </button>
                <button className={styles.menuItem} onClick={() => {
                    // Simple logout: clear storage and redirect
                    localStorage.clear();
                    sessionStorage.clear();
                    window.location.href = '/onboarding';
                }} title="Log out">
                    <span className={styles.icon}><LogOut size={18} /></span>
                    <span>Log out</span>
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
