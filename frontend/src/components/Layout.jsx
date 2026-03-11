import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import {
  LayoutDashboard, FileText, PlusCircle, ClipboardCheck,
  Database, Users, History, LogOut, Menu, TrendingUp
} from 'lucide-react';

const navConfig = {
  trader: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/deals', icon: FileText, label: 'My Deals' },
    { to: '/deals/new', icon: PlusCircle, label: 'New Deal' },
  ],
  treasury: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/treasury', icon: ClipboardCheck, label: 'Deal Queue' },
  ],
  admin: [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/reference-data', icon: Database, label: 'Reference Data' },
    { to: '/users', icon: Users, label: 'Users' },
    { to: '/transactions', icon: History, label: 'Transactions' },
  ],
};

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const items = navConfig[user?.role] || [];

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const SidebarContent = () => (
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
            onClick={() => setOpen(false)}
            data-testid={`nav-${item.label.toLowerCase().replace(/\s/g, '-')}`}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 rounded-md text-sm transition-all duration-150 ${
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
          <p className="text-sm font-medium text-white truncate">{user?.name}</p>
          <p className="text-xs text-white/50 capitalize">{user?.role === 'treasury' ? 'Treasury Ops' : user?.role}</p>
        </div>
        <Button
          variant="ghost"
          className="w-full justify-start text-white/60 hover:text-white hover:bg-white/10"
          onClick={handleLogout}
          data-testid="logout-btn"
        >
          <LogOut className="h-4 w-4 mr-3" />
          Logout
        </Button>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen bg-[#f8fafc]">
      <aside className="hidden lg:flex w-64 bg-[#08263e] flex-col flex-shrink-0">
        <SidebarContent />
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
              <SidebarContent />
            </SheetContent>
          </Sheet>
          <div className="flex-1" />
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium text-[#08263e]">{user?.name}</p>
              <p className="text-[11px] text-slate-400 capitalize">{user?.role === 'treasury' ? 'Treasury Ops' : user?.role}</p>
            </div>
            <div className="h-8 w-8 rounded-full bg-[#08263e] flex items-center justify-center text-white text-xs font-semibold">
              {user?.name?.charAt(0)}
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
