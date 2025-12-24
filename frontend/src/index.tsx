import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { initializeIcons } from '@fluentui/react';

import Chat from './pages/chat/Chat';
import Dashboard from './pages/dashboard/Dashboard';
import Recommendations from './pages/recommendations/Recommendations';
import UserProfile from './pages/userProfile/UserProfile';
import Layout from './pages/layout/Layout';
import NoPage from './pages/noPage/NoPage';
import Home from './pages/home/Home';
import History from './pages/history/History';
import HealthDashboard from './pages/health/HealthDashboard';
import HealthConnect from './pages/health/HealthConnect';
import AuthCallback from './pages/health/AuthCallback';
import TimeDashboard from './pages/time/TimeDashboard';
import FinanceDashboard from './pages/financials/FinanceDashboard';
import Onboarding from './pages/onboarding/Onboarding';
import Login from './pages/login/Login';
import ForgotPassword from './pages/login/ForgotPassword';
import ResetPassword from './pages/login/ResetPassword';

import { AppStateProvider } from './state/AppProvider';
import './index.css';

// Initialize Fluent UI icons
initializeIcons();

// Auth & Guards
import { AuthProvider } from './context/AuthProvider';
import { ProtectedRoute, PublicOnlyRoute, OnboardingRoute } from './components/auth/RouteGuards';


export default function App() {
  return (
    <AuthProvider>
      <AppStateProvider>
        <BrowserRouter>
          <Routes>
            {/* Login Page - Public Only */}
            <Route path="/login" element={
              <PublicOnlyRoute>
                <Login />
              </PublicOnlyRoute>
            } />
            <Route path="/forgot-password" element={
              <PublicOnlyRoute>
                <ForgotPassword />
              </PublicOnlyRoute>
            } />
            <Route path="/reset-password" element={
              <PublicOnlyRoute>
                <ResetPassword />
              </PublicOnlyRoute>
            } />

            {/* Onboarding - Protected but for incomplete users */}
            <Route path="/onboarding" element={
              <OnboardingRoute>
                <Onboarding />
              </OnboardingRoute>
            } />

            {/* Main Layout - Protected */}
            <Route path="/" element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }>
              {/* Default Route - Home page */}
              <Route index element={<Home />} />

              {/* History Page */}
              <Route path="history" element={<History />} />

              {/* Time Pages */}
              <Route path="time" element={<TimeDashboard />} />

              {/* Health Pages */}
              <Route path="health" element={<HealthDashboard />} />
              <Route path="health/connect" element={<HealthConnect />} />
              <Route path="health/google/callback" element={<AuthCallback />} />

              {/* Finance Pages */}
              <Route path="finance" element={<FinanceDashboard />} />

              {/* Chat Page */}
              <Route path="chat" element={<Chat />} />

              {/* Dashboard Page (Legacy) */}
              <Route path="dashboard" element={<Dashboard />} />

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
    </AuthProvider>
  );
}

// Mount React application to the DOM
ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
