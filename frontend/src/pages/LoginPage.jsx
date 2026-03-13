import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { TrendingUp, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success('Welcome back!');
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" data-testid="login-page">
      <div className="hidden lg:flex lg:w-1/2 bg-[#08263e] relative items-center justify-center overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1768101225267-c6fc5678c113?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NzR8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBjb3Jwb3JhdGUlMjBhcmNoaXRlY3R1cmUlMjBmaW5hbmNlJTIwYWJzdHJhY3R8ZW58MHx8fHwxNzczMTk4ODI0fDA&ixlib=rb-4.1.0&q=60&w=800"
          alt=""
          className="absolute inset-0 w-full h-full object-cover opacity-20"
          loading="eager"
          decoding="async"
          fetchPriority="low"
        />
        <div className="relative z-10 p-12 max-w-lg">
          <TrendingUp className="h-14 w-14 text-[#518dca] mb-8" />
          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4" style={{ fontFamily: 'Chivo, sans-serif' }}>
            FX Trading Tracker
          </h1>
          <p className="text-base text-white/70 leading-relaxed">
            Streamline your foreign exchange operations with real-time deal tracking, treasury management, and comprehensive reporting.
          </p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-6 sm:p-8 bg-[#f8fafc]">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <TrendingUp className="h-9 w-9 text-[#518dca]" />
            <h1 className="text-2xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo, sans-serif' }}>FX Tracker</h1>
          </div>
          <Card className="border-slate-200 shadow-sm">
            <CardHeader className="pb-4">
              <CardTitle className="text-2xl text-[#08263e]" style={{ fontFamily: 'Chivo, sans-serif' }}>Sign In</CardTitle>
              <CardDescription>Enter your credentials to access the platform</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email" type="email" placeholder="your@email.com"
                    value={email} onChange={e => setEmail(e.target.value)}
                    required data-testid="login-email-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Input
                      id="password" type={showPw ? 'text' : 'password'}
                      value={password} onChange={e => setPassword(e.target.value)}
                      required data-testid="login-password-input"
                    />
                    <button
                      type="button"
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                      onClick={() => setShowPw(!showPw)}
                      data-testid="toggle-password-btn"
                    >
                      {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
                <Button
                  type="submit" className="w-full bg-[#08263e] hover:bg-[#08263e]/90 text-white"
                  disabled={loading} data-testid="login-submit-btn"
                >
                  {loading ? 'Signing in...' : 'Sign In'}
                </Button>
              </form>
              <div className="mt-6 p-4 bg-slate-50 rounded-md border border-slate-100">
                <p className="text-xs text-slate-500 font-medium mb-2 uppercase tracking-wider">Demo Accounts</p>
                <div className="space-y-1.5 text-xs text-slate-600" style={{ fontFamily: 'JetBrains Mono, monospace' }}>
                  <p>admin@fxtracker.com / Admin@123</p>
                  <p>trader@fxtracker.com / Trader@123</p>
                  <p>treasury@fxtracker.com / Treasury@123</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
