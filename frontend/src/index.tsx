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
import Login from './pages/login/LoginNative';
// import Login from './pages/login/LoginAuth0';
import { CallbackPage } from './pages/CallbackPage';
import ForgotPassword from './pages/login/ForgotPassword';
import ResetPassword from './pages/login/ResetPassword';
import AdminLayout from './pages/admin/AdminLayout';
import UserManagement from './pages/admin/UserManagement';
import AuditViewer from './pages/admin/AuditViewer';
import SubscriptionManagement from './pages/admin/SubscriptionManagement';
import BillingReconciliation from './pages/admin/BillingReconciliation';

import { AppStateProvider } from './state/AppProvider';
import './index.css';
import { initTheme } from './utils/theme';

// Initialize Theme
initTheme();

// Initialize Fluent UI icons
initializeIcons();

// Auth & Guards
import { AuthProvider } from './context/AuthProvider';
import { ProtectedRoute, PublicOnlyRoute, OnboardingRoute, AdminRoute } from './components/auth/RouteGuards';
import { Auth0Wrapper } from './components/Auth0Wrapper';


export default function App() {
  return (
    <Auth0Wrapper>
      <AuthProvider>
        <AppStateProvider>
          <BrowserRouter>
            <Routes>
              {/* Auth0 Callback Route */}
              <Route path="/callback" element={<CallbackPage />} />

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

              {/* Admin Routes - Protected by Admin Guard */}
              <Route path="/admin" element={
                <AdminRoute>
                  <AdminLayout />
                </AdminRoute>
              }>
                <Route path="users" element={<UserManagement />} />
                <Route path="audit" element={<AuditViewer />} />
                <Route path="subscriptions" element={<SubscriptionManagement />} />
                <Route path="billing" element={<BillingReconciliation />} />
              </Route>

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
    </Auth0Wrapper>
  );
}

// Mount React application to the DOM
ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
