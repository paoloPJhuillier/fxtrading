import { useState, memo, useCallback } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import {
  LayoutDashboard, FileText, PlusCircle, ClipboardCheck,
  Database, Users, History, LogOut, Menu, TrendingUp, Activity, KeyRound, BarChart3, Settings
} from 'lucide-react';
import { toast } from 'sonner';

function userDisplayName(u) {
  if (u?.first_name || u?.last_name) return `${u.first_name || ''} ${u.last_name || ''}`.trim();
  return u?.name || '';
}
function userInitials(u) {
  const fn = u?.first_name || u?.name || '';
  const ln = u?.last_name || '';
  if (fn && ln) return `${fn.charAt(0)}${ln.charAt(0)}`.toUpperCase();
  return fn.charAt(0).toUpperCase() || '?';
}

const navConfig = {
  trader: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/deals', icon: FileText, label: 'My Deals' },
    { to: '/deals/new', icon: PlusCircle, label: 'New Deal' },
    { to: '/reports', icon: BarChart3, label: 'Reports' },
  ],
  treasury: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/treasury', icon: ClipboardCheck, label: 'Deal Queue' },
    { to: '/reports', icon: BarChart3, label: 'Reports' },
  ],
  admin: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/reference-data', icon: Database, label: 'Reference Data' },
    { to: '/users', icon: Users, label: 'Users' },
    { to: '/transactions', icon: History, label: 'Transactions' },
    { to: '/audit-log', icon: Activity, label: 'Audit Trail' },
    { to: '/reports', icon: BarChart3, label: 'Reports' },
  ],
  sysadmin: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/reference-data', icon: Database, label: 'Reference Data' },
    { to: '/users', icon: Users, label: 'Users' },
    { to: '/transactions', icon: History, label: 'Transactions' },
    { to: '/audit-log', icon: Activity, label: 'Audit Trail' },
    { to: '/reports', icon: BarChart3, label: 'Reports' },
    { to: '/system', icon: Settings, label: 'System' },
  ],
};

const SidebarContent = memo(function SidebarContent({ items, user, onLogout, onNavClick, onChangePassword }) {
  return (
    <div className="flex flex-col h-full">
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center gap-3">
          <TrendingUp className="h-7 w-7 text-[#518dca]" />
          <div>
            <h1 className="text-lg font-bold text-white" style={{ fontFamily: 'Chivo, sans-serif' }}>FX Tracker</h1>
            <p className="text-[10px] text-white/50 uppercase tracking-widest">Trading Platform</p>
          </div>
        </div>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {items.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/dashboard'}
            onClick={onNavClick}
            data-testid={`nav-${item.label.toLowerCase().replace(/\s/g, '-')}`}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 rounded-md text-sm transition-colors duration-150 ${
                isActive
                  ? 'bg-[#518dca] text-white font-medium shadow-sm'
                  : 'text-white/60 hover:bg-white/8 hover:text-white'
              }`
            }
          >
            <item.icon className="h-4 w-4 flex-shrink-0" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-white/10">
        <div className="px-3 py-2 mb-2">
          <p className="text-sm font-medium text-white truncate" data-testid="sidebar-user-name">{userDisplayName(user)}</p>
          <p className="text-xs text-white/50 capitalize">{user?.role === 'treasury' ? 'Treasury Ops' : user?.role}</p>
        </div>
        <Button
          variant="ghost"
          className="w-full justify-start text-white/60 hover:text-white hover:bg-white/10 mb-1"
          onClick={onChangePassword}
          data-testid="change-password-btn"
        >
          <KeyRound className="h-4 w-4 mr-3" />
          Change Password
        </Button>
        <Button
          variant="ghost"
          className="w-full justify-start text-white/60 hover:text-white hover:bg-white/10"
          onClick={onLogout}
          data-testid="logout-btn"
        >
          <LogOut className="h-4 w-4 mr-3" />
          Logout
        </Button>
      </div>
    </div>
  );
});

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [pwdOpen, setPwdOpen] = useState(false);
  const [pwdForm, setPwdForm] = useState({ current: '', new: '', confirm: '' });
  const [pwdLoading, setPwdLoading] = useState(false);
  const items = navConfig[user?.role] || [];

  const handleLogout = useCallback(() => { logout(); navigate('/login'); }, [logout, navigate]);
  const handleNavClick = useCallback(() => setOpen(false), []);
  const handleChangePassword = useCallback(() => {
    setPwdForm({ current: '', new: '', confirm: '' });
    setPwdOpen(true);
    setOpen(false);
  }, []);

  const submitPasswordChange = useCallback(async () => {
    if (!pwdForm.current) { toast.error('Current password is required'); return; }
    if (!pwdForm.new || pwdForm.new.length < 4) { toast.error('New password must be at least 4 characters'); return; }
    if (pwdForm.new !== pwdForm.confirm) { toast.error('Passwords do not match'); return; }
    setPwdLoading(true);
    try {
      await api.put('/auth/change-password', { current_password: pwdForm.current, new_password: pwdForm.new });
      toast.success('Password changed successfully');
      setPwdOpen(false);
    } catch (err) {
      toast.error(err?.response?.data?.detail || 'Failed to change password');
    } finally { setPwdLoading(false); }
  }, [pwdForm]);

  return (
    <div className="flex h-screen bg-[#f8fafc]">
      <aside className="hidden lg:flex w-64 bg-[#08263e] flex-col flex-shrink-0">
        <SidebarContent items={items} user={user} onLogout={handleLogout} onNavClick={handleNavClick} onChangePassword={handleChangePassword} />
      </aside>
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="h-14 bg-white border-b border-slate-200 flex items-center px-4 lg:px-8 flex-shrink-0">
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="lg:hidden mr-2" data-testid="mobile-menu-btn">
                <Menu className="h-5 w-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-64 p-0 bg-[#08263e] border-none">
              <SidebarContent items={items} user={user} onLogout={handleLogout} onNavClick={handleNavClick} onChangePassword={handleChangePassword} />
            </SheetContent>
          </Sheet>
          <div className="flex-1" />
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium text-[#08263e]" data-testid="header-user-name">{userDisplayName(user)}</p>
              <p className="text-[11px] text-slate-400 capitalize">{user?.role === 'treasury' ? 'Treasury Ops' : user?.role}</p>
            </div>
            <div className="h-8 w-8 rounded-full bg-[#08263e] flex items-center justify-center text-white text-xs font-semibold" data-testid="user-avatar">
              {userInitials(user)}
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-4 lg:p-8 pb-20">
          <Outlet />
        </main>
      </div>

      {pwdOpen && (
        <Dialog open={pwdOpen} onOpenChange={setPwdOpen}>
          <DialogContent data-testid="change-password-dialog">
            <DialogHeader>
              <DialogTitle style={{ fontFamily: 'Chivo' }}>Change Password</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label className="text-xs">Current Password</Label>
                <Input type="password" value={pwdForm.current} onChange={e => setPwdForm(p => ({ ...p, current: e.target.value }))} data-testid="current-password-input" placeholder="Enter current password" />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">New Password</Label>
                <Input type="password" value={pwdForm.new} onChange={e => setPwdForm(p => ({ ...p, new: e.target.value }))} data-testid="new-password-input" placeholder="Enter new password" />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Confirm New Password</Label>
                <Input type="password" value={pwdForm.confirm} onChange={e => setPwdForm(p => ({ ...p, confirm: e.target.value }))} data-testid="confirm-password-input" placeholder="Re-enter new password" />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setPwdOpen(false)} data-testid="pwd-cancel-btn">Cancel</Button>
              <Button className="bg-[#08263e] hover:bg-[#08263e]/90" onClick={submitPasswordChange} disabled={pwdLoading} data-testid="pwd-submit-btn">
                {pwdLoading ? 'Changing...' : 'Change Password'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
