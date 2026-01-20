import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import Sidebar from '../../components/layout/Sidebar';
import SettingsModal from '../../components/modals/SettingsModal';
import styles from './Layout.module.css';

const Layout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(() => window.innerWidth > 768);
  const [isCollapsed, setIsCollapsed] = useState(() => window.innerWidth > 768); // Collapsed by default on desktop, Expanded by default on mobile (when open)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const location = useLocation();

  const toggleSidebar = () => {
    if (window.innerWidth <= 1024) {
      setIsCollapsed(false);
    }
    setIsSidebarOpen(!isSidebarOpen);
  };

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const navigate = useNavigate();

  const handleNewChat = () => {
    console.log("New chat clicked");
    navigate('/chat');
  };

  return (
    <div className={styles.layout}>
      {/* Mobile Backdrop */}
      {isSidebarOpen && (
        <div
          className={`${styles.backdrop} ${isSidebarOpen ? styles.backdropVisible : ''}`}
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      <Sidebar
        isOpen={isSidebarOpen}
        isCollapsed={isCollapsed}
        onToggle={toggleSidebar}
        onToggleCollapse={toggleCollapse}
        onNewChat={handleNewChat}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      <main className={`${styles.main} ${isSidebarOpen ? (isCollapsed ? styles.sidebarCollapsed : styles.sidebarOpen) : ''}`}>
        {/* Mobile Header */}
        <div className={styles.mobileHeader}>
          <button className={styles.mobileToggle} onClick={() => setIsSidebarOpen(true)}>
            <span style={{ fontSize: '24px' }}>☰</span>
          </button>
          {/* Optional: Add Logo or Title here for mobile context if needed */}
        </div>

        {location.pathname !== '/' && (
          <div className={styles.backNav}>
            <a href="#" onClick={(e) => { e.preventDefault(); navigate(-1); }} className={styles.backLink}>← Back</a>
          </div>
        )}

        <Outlet />
      </main>

      <SettingsModal
        isOpen={isSettingsOpen}
        onDismiss={() => setIsSettingsOpen(false)}
      />
    </div>
  );
};

export default Layout;
