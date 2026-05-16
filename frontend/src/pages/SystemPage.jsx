import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import {
  Database, Download, FileSpreadsheet, FileJson, Loader2,
  AlertTriangle, HardDrive, Trash2, RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';

const EXPORT_ENTITIES = [
  { key: 'deals', label: 'Deals', desc: 'All deal tickets with full details', icon: '📋', category: 'Transactional' },
  { key: 'audit_logs', label: 'Audit Logs', desc: 'Complete audit trail', icon: '📜', category: 'Transactional' },
  { key: 'users', label: 'Users', desc: 'User accounts (passwords excluded)', icon: '👤', category: 'System' },
  { key: 'companies', label: 'Companies', desc: 'Client/counterparty companies', icon: '🏢', category: 'Reference' },
  { key: 'banks', label: 'Banks', desc: 'Banking institutions with SWIFT codes', icon: '🏦', category: 'Reference' },
  { key: 'bank_accounts', label: 'Bank Accounts', desc: 'Account numbers per bank', icon: '💳', category: 'Reference' },
  { key: 'currencies', label: 'Currencies', desc: 'Fiat, crypto, and stablecoin', icon: '💱', category: 'Reference' },
  { key: 'transaction_types', label: 'Transaction Types', desc: 'Today, Tomorrow, Spot', icon: '📅', category: 'Reference' },
  { key: 'transfer_types', label: 'Transfer Types', desc: 'FX Crypto, FX Local, FX Bank Deal', icon: '🔄', category: 'Reference' },
];

function StatCard({ label, count }) {
  return (
    <div className="flex items-center justify-between py-2 px-3 rounded-md bg-white border border-gray-100">
      <span className="text-xs text-gray-600">{label}</span>
      <span className="text-sm font-semibold text-[#08263e] tabular-nums">{(count ?? 0).toLocaleString()}</span>
    </div>
  );
}

export default function SystemPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showReset, setShowReset] = useState(false);
  const [resetConfirm, setResetConfirm] = useState('');
  const [resetting, setResetting] = useState(false);
  const [exporting, setExporting] = useState(null);

  const fetchStats = useCallback(async () => {
    try {
      const { data } = await api.get('/system/db-stats');
      setStats(data.stats);
    } catch {
      toast.error('Failed to load database stats');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchStats(); }, [fetchStats]);

  // Route guard: only sysadmin
  if (user?.role !== 'sysadmin') {
    navigate('/dashboard', { replace: true });
    return null;
  }

  const handleExport = async (entity, format) => {
    const id = `${entity}-${format}`;
    setExporting(id);
    try {
      const resp = await api.get(`/system/export/${entity}`, { params: { format }, responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([resp.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `${entity}_${new Date().toISOString().slice(0, 10)}.${format === 'json' ? 'json' : 'csv'}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success(`${entity} exported as ${format.toUpperCase()}`);
    } catch {
      toast.error(`Export failed for ${entity}`);
    } finally {
      setExporting(null);
    }
  };

  const handleReset = async () => {
    if (resetConfirm !== 'RESET DATABASE') return;
    setResetting(true);
    try {
      const { data } = await api.post('/system/db-reset', { confirm: resetConfirm });
      toast.success(`Database reset: ${data.wiped.deals} deals, ${data.wiped.audit_logs} audit logs wiped`);
      setShowReset(false);
      setResetConfirm('');
      fetchStats();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Reset failed');
    } finally {
      setResetting(false);
    }
  };

  const grouped = {};
  EXPORT_ENTITIES.forEach(e => {
    if (!grouped[e.category]) grouped[e.category] = [];
    grouped[e.category].push(e);
  });

  return (
    <div className="space-y-6" data-testid="system-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo, sans-serif' }}>System Administration</h1>
          <p className="text-sm text-gray-500 mt-1">Database management, export, and maintenance</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchStats} className="gap-1.5 text-xs" data-testid="refresh-stats-btn">
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </Button>
      </div>

      {/* Database Stats */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <HardDrive className="h-4 w-4 text-[#518dca]" />
            <CardTitle className="text-sm text-[#08263e]">Database Overview</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-6"><Loader2 className="h-5 w-5 animate-spin text-[#518dca]" /></div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
              {stats && Object.entries(stats).map(([k, v]) => (
                <StatCard key={k} label={k.replace(/_/g, ' ')} count={v} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Export Data */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Download className="h-4 w-4 text-[#518dca]" />
            <CardTitle className="text-sm text-[#08263e]">Export Data</CardTitle>
          </div>
          <CardDescription className="text-xs">Download database records as CSV or JSON</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {Object.entries(grouped).map(([category, entities]) => (
            <div key={category}>
              <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-2">{category} Data</p>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {entities.map(e => (
                  <div key={e.key} className="flex items-center justify-between p-3 border border-gray-100 rounded-lg bg-white hover:bg-gray-50/50 transition-colors" data-testid={`export-${e.key}`}>
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-[#08263e] truncate">{e.label}</p>
                      <p className="text-[10px] text-gray-400 truncate">{e.desc}</p>
                      {stats && <p className="text-[10px] text-[#518dca] font-medium">{(stats[e.key] ?? 0).toLocaleString()} records</p>}
                    </div>
                    <div className="flex gap-1 ml-2 shrink-0">
                      <Button variant="ghost" size="sm" className="h-7 px-2 text-[10px] gap-1"
                        disabled={!!exporting}
                        onClick={() => handleExport(e.key, 'csv')}
                        data-testid={`export-${e.key}-csv`}>
                        {exporting === `${e.key}-csv` ? <Loader2 className="h-3 w-3 animate-spin" /> : <FileSpreadsheet className="h-3 w-3" />}
                        CSV
                      </Button>
                      <Button variant="ghost" size="sm" className="h-7 px-2 text-[10px] gap-1"
                        disabled={!!exporting}
                        onClick={() => handleExport(e.key, 'json')}
                        data-testid={`export-${e.key}-json`}>
                        {exporting === `${e.key}-json` ? <Loader2 className="h-3 w-3 animate-spin" /> : <FileJson className="h-3 w-3" />}
                        JSON
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Database Reset */}
      <Card className="border-red-200">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-[#ec474e]" />
            <CardTitle className="text-sm text-[#ec474e]">Danger Zone</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 border border-red-100 rounded-lg bg-red-50/30">
            <div>
              <p className="text-sm font-medium text-[#08263e]">Reset Database</p>
              <p className="text-xs text-gray-500 mt-0.5">
                Wipes all deals, audit logs, and counters. Users and reference data are retained.
              </p>
            </div>
            <Button variant="outline" className="border-[#ec474e] text-[#ec474e] hover:bg-[#ec474e]/5"
              onClick={() => setShowReset(true)} data-testid="reset-db-btn">
              <Trash2 className="h-3.5 w-3.5 mr-1.5" /> Reset Database
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Reset Confirmation Dialog */}
      <Dialog open={showReset} onOpenChange={setShowReset}>
        <DialogContent className="max-w-sm" data-testid="reset-confirm-dialog" aria-describedby="reset-desc">
          <DialogHeader>
            <DialogTitle className="text-[#ec474e] flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" /> Confirm Database Reset
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4" id="reset-desc">
            <div className="p-3 bg-red-50 border border-red-200 rounded-md text-xs text-red-700 space-y-1">
              <p className="font-semibold">This action will permanently delete:</p>
              <ul className="list-disc ml-4 space-y-0.5">
                <li>All deal tickets ({stats?.deals?.toLocaleString() || 0} records)</li>
                <li>All audit logs ({stats?.audit_logs?.toLocaleString() || 0} records)</li>
                <li>Deal reference counters</li>
                <li>Report permission overrides</li>
              </ul>
              <p className="font-semibold mt-2">The following will be retained:</p>
              <ul className="list-disc ml-4 space-y-0.5">
                <li>All user accounts</li>
                <li>All reference data (companies, banks, currencies, etc.)</li>
              </ul>
            </div>
            <div>
              <Label className="text-xs text-gray-600">Type <span className="font-mono font-bold text-[#ec474e]">RESET DATABASE</span> to confirm</Label>
              <Input value={resetConfirm} onChange={e => setResetConfirm(e.target.value)}
                placeholder="RESET DATABASE" className="mt-1 font-mono text-sm"
                data-testid="reset-confirm-input" />
            </div>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => { setShowReset(false); setResetConfirm(''); }}>Cancel</Button>
            <Button className="bg-[#ec474e] hover:bg-[#ec474e]/90 text-white"
              disabled={resetConfirm !== 'RESET DATABASE' || resetting}
              onClick={handleReset}
              data-testid="reset-confirm-btn">
              {resetting ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Trash2 className="h-4 w-4 mr-1" />}
              Reset Database
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
