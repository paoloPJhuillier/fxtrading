import { useState, useCallback } from 'react';
import { useAuth } from '@/lib/auth';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { FileText, Download, FileSpreadsheet, Loader2, Shield, BarChart3, Users, Clock, TrendingUp, Briefcase } from 'lucide-react';
import { toast } from 'sonner';

const REPORTS = [
  {
    id: 'deal-blotter',
    title: 'Deal Blotter',
    desc: 'Complete log of all executed deals with full details',
    icon: FileText,
    color: '#08263e',
    roles: ['trader', 'treasury', 'admin'],
    filters: ['dateRange', 'status', 'client', 'currency'],
  },
  {
    id: 'settlement',
    title: 'Settlement Report',
    desc: 'Deals grouped by value date with bank details and proof status',
    icon: Clock,
    color: '#ec474e',
    roles: ['trader', 'treasury', 'admin'],
    filters: ['dateRange'],
  },
  {
    id: 'open-positions',
    title: 'Open Positions',
    desc: 'Pending deals grouped by currency pair showing net exposure',
    icon: TrendingUp,
    color: '#518dca',
    roles: ['trader', 'treasury', 'admin'],
    filters: [],
  },
  {
    id: 'audit-trail',
    title: 'Transaction Audit Trail',
    desc: 'Full history of every deal action with timestamps and change logs',
    icon: Shield,
    color: '#08263e',
    roles: ['admin'],
    filters: ['dateRange'],
  },
  {
    id: 'user-activity',
    title: 'User Activity',
    desc: 'Actions per user: deals created, processed, returned, proofs uploaded',
    icon: Users,
    color: '#ec474e',
    roles: ['admin'],
    filters: ['dateRange'],
  },
  {
    id: 'volume-summary',
    title: 'Volume Summary',
    desc: 'Deal counts and volumes grouped by day, week, or month',
    icon: BarChart3,
    color: '#518dca',
    roles: ['trader', 'treasury', 'admin'],
    filters: ['dateRange', 'groupBy'],
  },
  {
    id: 'client-activity',
    title: 'Client Activity',
    desc: 'Per-client breakdown of deal volume, frequency, and average size',
    icon: Briefcase,
    color: '#08263e',
    roles: ['trader', 'treasury', 'admin'],
    filters: ['dateRange'],
  },
];

function ReportCard({ report, role }) {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [status, setStatus] = useState('');
  const [client, setClient] = useState('');
  const [currency, setCurrency] = useState('');
  const [groupBy, setGroupBy] = useState('daily');
  const [loading, setLoading] = useState(null); // 'csv' | 'pdf' | null

  const canAccess = report.roles.includes(role);
  const hasFilters = report.filters.length > 0;

  const handleExport = useCallback(async (format) => {
    setLoading(format);
    try {
      const params = { format };
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (status && status !== 'all_statuses' && report.filters.includes('status')) params.status = status;
      if (client && report.filters.includes('client')) params.client = client;
      if (currency && report.filters.includes('currency')) params.currency = currency;
      if (report.filters.includes('groupBy')) params.group_by = groupBy;

      const resp = await api.get(`/reports/${report.id}`, { params, responseType: 'blob' });
      const blob = new Blob([resp.data]);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const ext = format === 'pdf' ? 'pdf' : 'csv';
      a.download = `${report.id}_${new Date().toISOString().slice(0, 10)}.${ext}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success(`${report.title} exported as ${format.toUpperCase()}`);
    } catch (err) {
      const msg = err.response?.data?.detail || err.message || 'Export failed';
      toast.error(`Export failed: ${msg}`);
    } finally {
      setLoading(null);
    }
  }, [dateFrom, dateTo, status, client, currency, groupBy, report]);

  if (!canAccess) return null;

  const Icon = report.icon;

  return (
    <Card className="border border-gray-200 hover:shadow-md transition-shadow" data-testid={`report-card-${report.id}`}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg" style={{ backgroundColor: report.color + '12' }}>
              <Icon className="h-5 w-5" style={{ color: report.color }} />
            </div>
            <div>
              <CardTitle className="text-sm font-semibold text-[#08263e]">{report.title}</CardTitle>
              <CardDescription className="text-xs mt-0.5">{report.desc}</CardDescription>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0 space-y-3">
        {hasFilters && (
          <div className="grid grid-cols-2 gap-2">
            {report.filters.includes('dateRange') && (
              <>
                <div>
                  <Label className="text-[10px] text-gray-500 uppercase">From</Label>
                  <Input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)}
                    className="h-8 text-xs" data-testid={`${report.id}-date-from`} />
                </div>
                <div>
                  <Label className="text-[10px] text-gray-500 uppercase">To</Label>
                  <Input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)}
                    className="h-8 text-xs" data-testid={`${report.id}-date-to`} />
                </div>
              </>
            )}
            {report.filters.includes('status') && (
              <div>
                <Label className="text-[10px] text-gray-500 uppercase">Status</Label>
                <Select value={status} onValueChange={setStatus}>
                  <SelectTrigger className="h-8 text-xs" data-testid={`${report.id}-status-filter`}>
                    <SelectValue placeholder="All" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all_statuses">All</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="confirmed">Confirmed</SelectItem>
                    <SelectItem value="returned">Returned</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
            {report.filters.includes('client') && (
              <div>
                <Label className="text-[10px] text-gray-500 uppercase">Client</Label>
                <Input placeholder="Search..." value={client} onChange={e => setClient(e.target.value)}
                  className="h-8 text-xs" data-testid={`${report.id}-client-filter`} />
              </div>
            )}
            {report.filters.includes('currency') && (
              <div>
                <Label className="text-[10px] text-gray-500 uppercase">Currency</Label>
                <Input placeholder="e.g. USD" value={currency} onChange={e => setCurrency(e.target.value)}
                  className="h-8 text-xs" data-testid={`${report.id}-currency-filter`} />
              </div>
            )}
            {report.filters.includes('groupBy') && (
              <div className="col-span-2">
                <Label className="text-[10px] text-gray-500 uppercase">Group By</Label>
                <Select value={groupBy} onValueChange={setGroupBy}>
                  <SelectTrigger className="h-8 text-xs" data-testid={`${report.id}-group-by`}>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="weekly">Weekly</SelectItem>
                    <SelectItem value="monthly">Monthly</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
        )}

        <div className="flex gap-2 pt-1">
          <Button
            variant="outline" size="sm"
            className="flex-1 h-8 text-xs gap-1.5 border-[#518dca] text-[#518dca] hover:bg-[#518dca]/5"
            disabled={!!loading}
            onClick={() => handleExport('csv')}
            data-testid={`${report.id}-export-csv`}
          >
            {loading === 'csv' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FileSpreadsheet className="h-3.5 w-3.5" />}
            CSV
          </Button>
          <Button
            size="sm"
            className="flex-1 h-8 text-xs gap-1.5"
            style={{ backgroundColor: report.color }}
            disabled={!!loading}
            onClick={() => handleExport('pdf')}
            data-testid={`${report.id}-export-pdf`}
          >
            {loading === 'pdf' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
            PDF
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function ReportsPage() {
  const { user } = useAuth();
  const role = user?.role || '';

  const visibleReports = REPORTS.filter(r => r.roles.includes(role));

  return (
    <div className="space-y-6" data-testid="reports-page">
      <div>
        <h1 className="text-2xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo, sans-serif' }}>Reports</h1>
        <p className="text-sm text-gray-500 mt-1">Generate and export FX trading reports</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {visibleReports.map(report => (
          <ReportCard key={report.id} report={report} role={role} />
        ))}
      </div>

      {visibleReports.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p>No reports available for your role</p>
        </div>
      )}
    </div>
  );
}
