import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { initializeIcons } from '@fluentui/react';

import Chat from './pages/chat';
import Dashboard from './pages/dashboard';
import Recommendations from './pages/recommendations';
import UserProfile from './pages/userProfile';
import Layout from './pages/layout';
import NoPage from './pages/noPage';

import { AppStateProvider } from './state/AppProvider';
import './index.css';

// Initialize Fluent UI icons
initializeIcons();

export default function App() {
  return (
    <AppStateProvider>
      <BrowserRouter>
        <Routes>
          {/* Main Layout */}
          <Route path="/" element={<Layout />}>
            {/* Default Route */}
            <Route index element={<Dashboard />} />

            {/* Chat Assistant Page */}
            <Route path="chat" element={<Chat />} />

            {/* Recommendations Page */}
            <Route path="recommendations" element={<Recommendations />} />

            {/* User Profile Page */}
            <Route path="profile" element={<UserProfile />} />

            {/* Catch-All Route for 404s */}
            <Route path="*" element={<NoPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AppStateProvider>
  );
}

// Mount React application to the DOM
ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
