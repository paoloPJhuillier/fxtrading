import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { lazy, Suspense, useEffect } from 'react';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from '@/lib/auth';
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
  useEffect(() => {
    const hide = () => {
      const el = document.getElementById('emergent-badge');
      if (el) { el.remove(); return true; }
      return false;
    };
    if (hide()) return;
    const t1 = setTimeout(hide, 500);
    const t2 = setTimeout(hide, 2000);
    const obs = new MutationObserver(() => {
      if (hide()) obs.disconnect();
    });
    obs.observe(document.body, { childList: true });
    return () => { clearTimeout(t1); clearTimeout(t2); obs.disconnect(); };
  }, []);

  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster position="top-right" theme="light" richColors />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
