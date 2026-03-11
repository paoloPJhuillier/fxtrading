import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import api from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';
import { TrendingUp, Clock, CheckCircle, XCircle, Users, DollarSign } from 'lucide-react';
import { format } from 'date-fns';

const RANGES = [
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
  { value: 'ytd', label: 'YTD' },
  { value: 'all', label: 'All Time' },
];

const STATUS_COLORS = {
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-green-100 text-green-800',
  returned: 'bg-red-100 text-red-800',
};

const PIE_COLORS = ['#f59e0b', '#10b981', '#ec474e'];

function formatVol(v) {
  if (v >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
  if (v >= 1e3) return `${(v / 1e3).toFixed(1)}K`;
  return Number(v).toFixed(0);
}

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [range, setRange] = useState('30d');
  const [loading, setLoading] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(`/dashboard/stats?range=${range}`);
      setStats(res.data);
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, [range]);

  useEffect(() => { fetch(); }, [fetch]);

  if (loading || !stats) return (
    <div className="flex items-center justify-center h-64">
      <div className="animate-spin h-8 w-8 border-4 border-[#518dca] border-t-transparent rounded-full" />
    </div>
  );

  const pieData = [
    { name: 'Pending', value: stats.pending_deals },
    { name: 'Confirmed', value: stats.confirmed_deals },
    { name: 'Returned', value: stats.returned_deals },
  ].filter(d => d.value > 0);

  return (
    <div data-testid="dashboard-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">
            {user?.role === 'trader' ? 'Your trading overview' : user?.role === 'treasury' ? 'Operations overview' : 'System overview'}
          </p>
        </div>
        <div className="flex gap-2 flex-wrap" data-testid="date-range-toggles">
          {RANGES.map(r => (
            <Button
              key={r.value}
              variant={range === r.value ? 'default' : 'outline'}
              size="sm"
              onClick={() => setRange(r.value)}
              className={range === r.value ? 'bg-[#08263e] hover:bg-[#08263e]/90' : ''}
              data-testid={`range-${r.value}`}
            >
              {r.label}
            </Button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Metric icon={TrendingUp} label="Total Deals" value={stats.total_deals} color="#08263e" />
        <Metric icon={Clock} label="Pending" value={stats.pending_deals} color="#f59e0b" />
        <Metric icon={CheckCircle} label="Confirmed" value={stats.confirmed_deals} color="#10b981" />
        <Metric icon={XCircle} label="Returned" value={stats.returned_deals} color="#ec474e" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <Metric icon={DollarSign} label="Total Volume" value={formatVol(stats.total_volume)} color="#518dca" />
        {user?.role === 'admin' && <Metric icon={Users} label="Total Users" value={stats.total_users || 0} color="#08263e" />}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card>
          <CardHeader><CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Deals Over Time</CardTitle></CardHeader>
          <CardContent>
            {stats.deals_by_date?.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={stats.deals_by_date}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={d => format(new Date(d + 'T00:00:00'), 'dd MMM')} />
                  <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#518dca" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <p className="text-sm text-slate-400 text-center py-16">No data for selected period</p>}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Status Distribution</CardTitle></CardHeader>
          <CardContent>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={90} dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`} labelLine={false}>
                    {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : <p className="text-sm text-slate-400 text-center py-16">No data for selected period</p>}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Recent Deals</CardTitle></CardHeader>
        <CardContent className="p-0">
          {stats.recent_deals?.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Reference</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Pair</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right">Rate</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Date</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {stats.recent_deals.map(d => (
                  <TableRow key={d.id}>
                    <TableCell className="font-mono text-xs font-medium text-[#08263e]">{d.reference_number}</TableCell>
                    <TableCell className="text-sm">{d.transaction_type}</TableCell>
                    <TableCell className="font-mono text-xs">{d.buy_currency}/{d.sell_currency}</TableCell>
                    <TableCell className="text-right font-mono text-xs">{Number(d.amount).toLocaleString()}</TableCell>
                    <TableCell className="text-right font-mono text-xs">{d.rate}</TableCell>
                    <TableCell><Badge className={STATUS_COLORS[d.status]}>{d.status}</Badge></TableCell>
                    <TableCell className="text-xs text-slate-500">{format(new Date(d.created_at), 'dd MMM yyyy')}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : <p className="text-sm text-slate-400 text-center py-12">No deals in selected period</p>}
        </CardContent>
      </Card>
    </div>
  );
}

function Metric({ icon: Icon, label, value, color }) {
  return (
    <Card data-testid={`metric-${label.toLowerCase().replace(/\s/g, '-')}`}>
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[11px] font-medium uppercase tracking-wider text-slate-400">{label}</p>
            <p className="text-2xl font-bold font-mono mt-1" style={{ color }}>{value}</p>
          </div>
          <div className="h-10 w-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `${color}12` }}>
            <Icon className="h-5 w-5" style={{ color }} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
