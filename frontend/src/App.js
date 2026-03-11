import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from '@/lib/auth';
import Layout from '@/components/Layout';
import LoginPage from '@/pages/LoginPage';
import DashboardPage from '@/pages/DashboardPage';
import DealsPage from '@/pages/DealsPage';
import NewDealPage from '@/pages/NewDealPage';
import TreasuryPage from '@/pages/TreasuryPage';
import ReferenceDataPage from '@/pages/ReferenceDataPage';
import UsersPage from '@/pages/UsersPage';
import TransactionHistoryPage from '@/pages/TransactionHistoryPage';

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
      </Route>
    </Routes>
  );
}

function App() {
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
