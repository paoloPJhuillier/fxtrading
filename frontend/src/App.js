import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { lazy, Suspense } from 'react';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from '@/lib/auth';
import { RefDataProvider } from '@/lib/refdata';
import Layout from '@/components/Layout';
import LoginPage from '@/pages/LoginPage';

const DashboardPage = lazy(() => import('@/pages/DashboardPage'));
const DealsPage = lazy(() => import('@/pages/DealsPage'));
const NewDealPage = lazy(() => import('@/pages/NewDealPage'));
const TreasuryPage = lazy(() => import('@/pages/TreasuryPage'));
const ReferenceDataPage = lazy(() => import('@/pages/ReferenceDataPage'));
const UsersPage = lazy(() => import('@/pages/UsersPage'));
const TransactionHistoryPage = lazy(() => import('@/pages/TransactionHistoryPage'));
const AuditLogPage = lazy(() => import('@/pages/AuditLogPage'));

const PageLoader = () => (
  <div className="flex items-center justify-center h-32">
    <div className="animate-spin h-6 w-6 border-3 border-[#518dca] border-t-transparent rounded-full" />
  </div>
);

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return (
    <div className="flex items-center justify-center h-screen bg-[#f8fafc]">
      <div className="animate-spin h-8 w-8 border-4 border-[#518dca] border-t-transparent rounded-full" />
    </div>
  );
  if (!user) return <Navigate to="/login" />;
  return children;
}

function AppRoutes() {
  const { user, loading } = useAuth();
  if (loading) return null;
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/dashboard" /> : <LoginPage />} />
        <Route path="/" element={<Navigate to={user ? "/dashboard" : "/login"} />} />
        <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/deals" element={<DealsPage />} />
          <Route path="/deals/new" element={<NewDealPage />} />
          <Route path="/treasury" element={<TreasuryPage />} />
          <Route path="/reference-data" element={<ReferenceDataPage />} />
          <Route path="/users" element={<UsersPage />} />
          <Route path="/transactions" element={<TransactionHistoryPage />} />
          <Route path="/audit-log" element={<AuditLogPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <RefDataProvider>
          <AppRoutes />
          <Toaster position="top-right" theme="light" richColors />
        </RefDataProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
