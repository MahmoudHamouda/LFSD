import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import Sidebar from '../../components/layout/Sidebar';
import SettingsModal from '../../components/modals/SettingsModal';
import styles from './Layout.module.css';

const Layout = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const location = useLocation();

  const toggleSidebar = () => {
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
      <Sidebar
        isOpen={isSidebarOpen}
        isCollapsed={isCollapsed}
        onToggle={toggleSidebar}
        onToggleCollapse={toggleCollapse}
        onNewChat={handleNewChat}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      <main className={`${styles.main} ${isSidebarOpen ? (isCollapsed ? styles.sidebarCollapsed : styles.sidebarOpen) : ''}`}>
        {/* Mobile Sidebar Toggle */}
        <button className={styles.mobileToggle} onClick={toggleSidebar}>
          ☰
        </button>

        {location.pathname !== '/' && (
          <div className={styles.backNav}>
            <a href="/" onClick={(e) => { e.preventDefault(); navigate('/'); }} className={styles.backLink}>← Back to Home</a>
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
