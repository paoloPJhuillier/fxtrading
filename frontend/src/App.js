import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { lazy, Suspense, useEffect } from 'react';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from '@/lib/auth';
import { RefDataProvider } from '@/lib/refdata';
import Layout from '@/components/Layout';
import LoginPage from '@/pages/LoginPage';

const pageImports = {
  Dashboard: () => import('@/pages/DashboardPage'),
  Deals: () => import('@/pages/DealsPage'),
  NewDeal: () => import('@/pages/NewDealPage'),
  EditDeal: () => import('@/pages/EditDealPage'),
  Treasury: () => import('@/pages/TreasuryPage'),
  ReferenceData: () => import('@/pages/ReferenceDataPage'),
  Users: () => import('@/pages/UsersPage'),
  TransactionHistory: () => import('@/pages/TransactionHistoryPage'),
  AuditLog: () => import('@/pages/AuditLogPage'),
};

const DashboardPage = lazy(pageImports.Dashboard);
const DealsPage = lazy(pageImports.Deals);
const NewDealPage = lazy(pageImports.NewDeal);
const EditDealPage = lazy(pageImports.EditDeal);
const TreasuryPage = lazy(pageImports.Treasury);
const ReferenceDataPage = lazy(pageImports.ReferenceData);
const UsersPage = lazy(pageImports.Users);
const TransactionHistoryPage = lazy(pageImports.TransactionHistory);
const AuditLogPage = lazy(pageImports.AuditLog);

// Prefetch page chunks one at a time with delay to avoid network contention
let prefetchTimer = null;
function prefetchAllPages() {
  const keys = Object.keys(pageImports);
  let i = 0;
  function next() {
    if (i < keys.length) {
      pageImports[keys[i]]();
      i++;
      prefetchTimer = setTimeout(next, 150);
    }
  }
  next();
}
function cancelPrefetch() {
  if (prefetchTimer) { clearTimeout(prefetchTimer); prefetchTimer = null; }
}

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

  // After login, prefetch all page chunks on idle
  useEffect(() => {
    if (!user) return;
    if ('requestIdleCallback' in window) {
      const id = requestIdleCallback(prefetchAllPages);
      return () => { cancelIdleCallback(id); cancelPrefetch(); };
    } else {
      const id = setTimeout(prefetchAllPages, 1000);
      return () => { clearTimeout(id); cancelPrefetch(); };
    }
  }, [user]);

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
          <Route path="/deals/:id/edit" element={<EditDealPage />} />
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
