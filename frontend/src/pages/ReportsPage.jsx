import { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import { useAuth } from '@/lib/auth';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '@/components/ui/command';
import {
  FileText, Download, FileSpreadsheet, Loader2, Shield, BarChart3,
  Users, Clock, TrendingUp, Briefcase, ChevronLeft, Search, ArrowUpDown, Settings, Check, ChevronsUpDown
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

// ── Report definitions ──────────────────────────────────────────────────────

const REPORTS = {
  'deal-blotter': {
    title: 'Deal Blotter',
    desc: 'Complete log of all deals with full details',
    icon: FileText,
    color: '#08263e',
    roles: ['trader', 'treasury', 'admin'],
    filters: ['dateRange', 'status', 'client', 'currency'],
    columns: [
      { key: 'reference_number', label: 'Ref#', w: 'w-[100px]' },
      { key: 'deal_date', label: 'Deal Date', w: 'w-[90px]' },
      { key: 'value_date', label: 'Value Date', w: 'w-[90px]' },
      { key: 'client_name', label: 'Client' },
      { key: 'transaction_type', label: 'Type', w: 'w-[60px]' },
      { key: 'buy_currency', label: 'Buy', w: 'w-[50px]' },
      { key: 'sell_currency', label: 'Sell', w: 'w-[50px]' },
      { key: 'currency_amount', label: 'CCY Amt', w: 'w-[90px]', numeric: true },
      { key: 'rate', label: 'Rate', w: 'w-[70px]', numeric: true, decimals: 4 },
      { key: 'amount', label: 'Settle Amt', w: 'w-[100px]', numeric: true },
      { key: 'status', label: 'Status', w: 'w-[80px]' },
      { key: 'created_by_name', label: 'Trader', w: 'w-[100px]' },
    ],
  },
  'settlement': {
    title: 'Settlement Report',
    desc: 'Deals by value date with bank details and proof status',
    icon: Clock,
    color: '#ec474e',
    roles: ['trader', 'treasury', 'admin'],
    filters: ['dateRange', 'fromBank', 'toBank'],
    columns: [
      { key: 'value_date', label: 'Value Date', w: 'w-[90px]' },
      { key: 'reference_number', label: 'Ref#', w: 'w-[100px]' },
      { key: 'client_name', label: 'Client' },
      { key: 'buy_currency', label: 'Buy', w: 'w-[50px]' },
      { key: 'sell_currency', label: 'Sell', w: 'w-[50px]' },
      { key: 'currency_amount', label: 'CCY Amt', w: 'w-[90px]', numeric: true },
      { key: 'amount', label: 'Settle Amt', w: 'w-[100px]', numeric: true },
      { key: 'from_bank', label: 'From Bank', w: 'w-[90px]' },
      { key: 'to_bank', label: 'To Bank', w: 'w-[90px]' },
      { key: 'proofs', label: 'Proofs', w: 'w-[50px]', numeric: true },
      { key: 'status', label: 'Status', w: 'w-[80px]' },
    ],
  },
  'open-positions': {
    title: 'Open Positions',
    desc: 'Pending deals by currency pair showing net exposure',
    icon: TrendingUp,
    color: '#518dca',
    roles: ['trader', 'treasury', 'admin'],
    filters: [],
    columns: [
      { key: 'pair', label: 'Currency Pair', w: 'w-[120px]' },
      { key: 'count', label: '# Deals', w: 'w-[80px]', numeric: true },
      { key: 'buy_total', label: 'Total Buy', numeric: true },
      { key: 'sell_total', label: 'Total Sell', numeric: true },
      { key: 'net', label: 'Net Position', numeric: true },
    ],
  },
  'audit-trail': {
    title: 'Transaction Audit Trail',
    desc: 'Full history of every deal action with timestamps',
    icon: Shield,
    color: '#08263e',
    roles: ['admin'],
    filters: ['dateRange', 'auditUser'],
    columns: [
      { key: 'timestamp', label: 'Timestamp', w: 'w-[140px]' },
      { key: 'action', label: 'Action', w: 'w-[110px]' },
      { key: 'entity_type', label: 'Entity', w: 'w-[70px]' },
      { key: 'entity_ref', label: 'Reference', w: 'w-[110px]' },
      { key: 'user_name', label: 'User', w: 'w-[100px]' },
      { key: 'user_role', label: 'Role', w: 'w-[70px]' },
      { key: 'details', label: 'Details' },
    ],
  },
  'user-activity': {
    title: 'User Activity',
    desc: 'Actions per user over a period',
    icon: Users,
    color: '#ec474e',
    roles: ['admin'],
    filters: ['dateRange'],
    columns: [
      { key: 'user_name', label: 'User' },
      { key: 'role', label: 'Role', w: 'w-[80px]' },
      { key: 'created', label: 'Created', w: 'w-[70px]', numeric: true },
      { key: 'processed', label: 'Processed', w: 'w-[80px]', numeric: true },
      { key: 'returned', label: 'Returned', w: 'w-[70px]', numeric: true },
      { key: 'proofs', label: 'Proofs', w: 'w-[70px]', numeric: true },
      { key: 'total', label: 'Total', w: 'w-[60px]', numeric: true },
    ],
  },
  'volume-summary': {
    title: 'Volume Summary',
    desc: 'Deal counts and volumes by period',
    icon: BarChart3,
    color: '#518dca',
    roles: ['trader', 'treasury', 'admin'],
    filters: ['dateRange', 'groupBy'],
    columns: [
      { key: 'period', label: 'Period', w: 'w-[100px]' },
      { key: 'count', label: '# Deals', w: 'w-[70px]', numeric: true },
      { key: 'volume', label: 'Total Volume', numeric: true },
      { key: 'avg', label: 'Avg Deal Size', numeric: true },
      { key: 'confirmed', label: 'Confirmed', w: 'w-[80px]', numeric: true },
      { key: 'pending', label: 'Pending', w: 'w-[70px]', numeric: true },
      { key: 'returned', label: 'Returned', w: 'w-[70px]', numeric: true },
      { key: 'cancelled', label: 'Cancelled', w: 'w-[70px]', numeric: true },
    ],
  },
  'client-activity': {
    title: 'Client Activity',
    desc: 'Per-client volume, frequency, and average deal size',
    icon: Briefcase,
    color: '#08263e',
    roles: ['trader', 'treasury', 'admin'],
    filters: ['dateRange', 'client'],
    columns: [
      { key: 'client', label: 'Client' },
      { key: 'count', label: '# Deals', w: 'w-[70px]', numeric: true },
      { key: 'volume', label: 'Total Volume', numeric: true },
      { key: 'avg', label: 'Avg Deal Size', numeric: true },
      { key: 'pairs', label: 'Currency Pairs' },
      { key: 'last_deal', label: 'Last Deal', w: 'w-[90px]' },
    ],
  },
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function getYTDRange() {
  const now = new Date();
  const yearStart = `${now.getFullYear()}-01-01`;
  const today = now.toISOString().slice(0, 10);
  return { from: yearStart, to: today };
}

function fmtNum(v, decimals = 2) {
  if (v == null || v === '') return '';
  const n = Number(v);
  if (isNaN(n)) return String(v);
  return n.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function StatusBadge({ status }) {
  const colors = {
    pending: 'bg-amber-50 text-amber-700 border-amber-200',
    confirmed: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    returned: 'bg-red-50 text-red-700 border-red-200',
    cancelled: 'bg-gray-100 text-gray-500 border-gray-200',
  };
  return (
    <span className={`inline-block px-1.5 py-0.5 text-[10px] font-medium rounded border uppercase ${colors[status] || 'bg-gray-50 text-gray-600 border-gray-200'}`}>
      {status}
    </span>
  );
}

// ── Report Selector (Landing) ───────────────────────────────────────────────

function ReportSelector({ reports, onSelect, isAdmin, onOpenSettings }) {
  return (
    <div data-testid="reports-page">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo, sans-serif' }}>Reports</h1>
          <p className="text-sm text-gray-500 mt-1">Select a report to view data and export</p>
        </div>
        {isAdmin && (
          <Button variant="outline" size="sm" onClick={onOpenSettings} className="gap-1.5 text-xs" data-testid="report-settings-btn">
            <Settings className="h-3.5 w-3.5" /> Permissions
          </Button>
        )}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {reports.map(([id, r]) => {
          const Icon = r.icon;
          return (
            <button
              key={id}
              onClick={() => onSelect(id)}
              data-testid={`report-select-${id}`}
              className="text-left p-4 rounded-lg border border-gray-200 hover:border-[#518dca] hover:shadow-md transition-all group bg-white"
            >
              <div className="flex items-center gap-3 mb-2">
                <div className="p-2 rounded-lg transition-colors" style={{ backgroundColor: r.color + '10' }}>
                  <Icon className="h-5 w-5 transition-colors" style={{ color: r.color }} />
                </div>
                <h3 className="text-sm font-semibold text-[#08263e] group-hover:text-[#518dca] transition-colors">{r.title}</h3>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">{r.desc}</p>
            </button>
          );
        })}
      </div>
      {reports.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <FileText className="h-10 w-10 mx-auto mb-3 opacity-40" />
          <p className="text-sm">No reports are enabled for your role</p>
          <p className="text-xs mt-1">Contact your administrator to request access</p>
        </div>
      )}
    </div>
  );
}

// ── Debounce hook ───────────────────────────────────────────────────────────

function useDebounce(value, delay = 400) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

// ── Filter Combobox (autocomplete dropdown) ─────────────────────────────────

function FilterCombobox({ label, value, onValueChange, options, placeholder, testId }) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');

  const filtered = useMemo(() => {
    if (!search) return options;
    const q = search.toLowerCase();
    return options.filter(o => o.toLowerCase().includes(q));
  }, [options, search]);

  return (
    <div className="w-[160px]">
      <Label className="text-[10px] text-gray-500 uppercase mb-1 block">{label}</Label>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" role="combobox" aria-expanded={open}
            className="w-full h-8 justify-between text-xs font-normal bg-white px-2"
            data-testid={testId}>
            <span className="truncate">{value || placeholder || 'All'}</span>
            <ChevronsUpDown className="ml-1 h-3 w-3 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[200px] p-0" align="start">
          <Command shouldFilter={false}>
            <CommandInput placeholder={`Search ${label.toLowerCase()}...`} value={search}
              onValueChange={setSearch} className="h-8 text-xs" />
            <CommandList>
              <CommandEmpty className="py-3 text-center text-xs text-gray-400">No results</CommandEmpty>
              <CommandGroup>
                <CommandItem value="__clear__" onSelect={() => { onValueChange(''); setOpen(false); setSearch(''); }}
                  className="text-xs text-gray-400">
                  <Check className={cn("mr-2 h-3 w-3", !value ? "opacity-100" : "opacity-0")} />
                  All
                </CommandItem>
                {filtered.map(opt => (
                  <CommandItem key={opt} value={opt}
                    onSelect={() => { onValueChange(opt); setOpen(false); setSearch(''); }}
                    className="text-xs">
                    <Check className={cn("mr-2 h-3 w-3", value === opt ? "opacity-100" : "opacity-0")} />
                    {opt}
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}

// ── Paginated reports (row-level data that grows with transactions) ─────────
const PAGINATED_REPORTS = new Set(['deal-blotter', 'settlement', 'audit-trail']);

// ── Report Viewer (Table + Filters + Export) ────────────────────────────────

function ReportViewer({ reportId, report, onBack }) {
  const [rows, setRows] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [pages, setPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(null);
  const ytd = getYTDRange();
  const [dateFrom, setDateFrom] = useState(report.filters.includes('dateRange') ? ytd.from : '');
  const [dateTo, setDateTo] = useState(report.filters.includes('dateRange') ? ytd.to : '');
  const [status, setStatus] = useState('');
  const [client, setClient] = useState('');
  const [currency, setCurrency] = useState('');
  const [fromBank, setFromBank] = useState('');
  const [toBank, setToBank] = useState('');
  const [auditUser, setAuditUser] = useState('');
  const [groupBy, setGroupBy] = useState('daily');
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('desc');
  const [filterOptions, setFilterOptions] = useState(null);
  const abortRef = useRef(null);

  // Fetch filter options once
  useEffect(() => {
    api.get('/reports/filter-options').then(r => setFilterOptions(r.data)).catch(() => {});
  }, []);

  const isPaginated = PAGINATED_REPORTS.has(reportId);
  const hasFilters = report.filters.length > 0;
  const Icon = report.icon;

  // Reset to page 1 when filters change
  useEffect(() => { setPage(1); }, [dateFrom, dateTo, status, client, currency, fromBank, toBank, auditUser, groupBy]);

  const buildParams = useCallback((format, forExport = false) => {
    const params = { format };
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    if (status && status !== 'all_statuses' && report.filters.includes('status')) params.status = status;
    if (client && report.filters.includes('client')) params.client = client;
    if (currency && report.filters.includes('currency')) params.currency = currency;
    if (fromBank && report.filters.includes('fromBank')) params.from_bank = fromBank;
    if (toBank && report.filters.includes('toBank')) params.to_bank = toBank;
    if (auditUser && report.filters.includes('auditUser')) params.user_name = auditUser;
    if (report.filters.includes('groupBy')) params.group_by = groupBy;
    // Pagination + server sort only for JSON on paginated reports
    if (format === 'json' && isPaginated && !forExport) {
      params.page = page;
      params.limit = pageSize;
      if (sortKey) {
        params.sort_by = sortKey;
        params.sort_dir = sortDir;
      }
    }
    return params;
  }, [dateFrom, dateTo, status, client, currency, fromBank, toBank, auditUser, groupBy, page, pageSize, sortKey, sortDir, report, isPaginated]);

  const fetchData = useCallback(async () => {
    if (abortRef.current) abortRef.current.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    try {
      const params = buildParams('json');
      const { data } = await api.get(`/reports/${reportId}`, { params, signal: controller.signal });
      setRows(data.rows || []);
      setTotal(data.total || data.rows?.length || 0);
      setPages(data.pages || 1);
    } catch (err) {
      if (err.name !== 'CanceledError' && err.code !== 'ERR_CANCELED') {
        toast.error('Failed to load report data');
      }
    } finally {
      setLoading(false);
    }
  }, [reportId, buildParams]);

  useEffect(() => {
    fetchData();
    return () => { if (abortRef.current) abortRef.current.abort(); };
  }, [fetchData]);

  const handleExport = useCallback(async (format) => {
    setExporting(format);
    try {
      const params = buildParams(format, true);
      const resp = await api.get(`/reports/${reportId}`, { params, responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([resp.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reportId}_${new Date().toISOString().slice(0, 10)}.${format}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      toast.success(`Exported as ${format.toUpperCase()}`);
    } catch {
      toast.error('Export failed');
    } finally {
      setExporting(null);
    }
  }, [reportId, buildParams]);

  const handleSort = useCallback((key) => {
    if (isPaginated) {
      // Server-side sort: update sort params and reset to page 1
      setSortDir(prev => sortKey === key ? (prev === 'asc' ? 'desc' : 'asc') : 'desc');
      setSortKey(key);
      setPage(1);
    } else {
      // Client-side sort for aggregation reports
      setSortDir(prev => sortKey === key ? (prev === 'asc' ? 'desc' : 'asc') : 'desc');
      setSortKey(key);
    }
  }, [sortKey, isPaginated]);

  // Client-side sort only for non-paginated (aggregation) reports
  const displayRows = (!isPaginated && sortKey)
    ? [...rows].sort((a, b) => {
        const col = report.columns.find(c => c.key === sortKey);
        let va = a[sortKey], vb = b[sortKey];
        if (col?.numeric) { va = Number(va) || 0; vb = Number(vb) || 0; }
        else { va = String(va || '').toLowerCase(); vb = String(vb || '').toLowerCase(); }
        return sortDir === 'asc' ? (va > vb ? 1 : -1) : (va < vb ? 1 : -1);
      })
    : rows;

  return (
    <div data-testid={`report-view-${reportId}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="sm" onClick={onBack} className="gap-1 text-gray-500 hover:text-[#08263e]" data-testid="report-back-btn">
            <ChevronLeft className="h-4 w-4" /> Back
          </Button>
          <div className="h-5 w-px bg-gray-200" />
          <div className="p-1.5 rounded-md" style={{ backgroundColor: report.color + '10' }}>
            <Icon className="h-4 w-4" style={{ color: report.color }} />
          </div>
          <div>
            <h1 className="text-lg font-bold text-[#08263e]" style={{ fontFamily: 'Chivo, sans-serif' }}>{report.title}</h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400 mr-2" data-testid="report-row-count">{total} records</span>
          <Button variant="outline" size="sm" disabled={!!exporting || loading}
            onClick={() => handleExport('csv')}
            className="gap-1.5 text-xs border-[#518dca] text-[#518dca] hover:bg-[#518dca]/5"
            data-testid="report-export-csv">
            {exporting === 'csv' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <FileSpreadsheet className="h-3.5 w-3.5" />}
            CSV
          </Button>
          <Button size="sm" disabled={!!exporting || loading}
            onClick={() => handleExport('pdf')}
            className="gap-1.5 text-xs text-white"
            style={{ backgroundColor: report.color }}
            data-testid="report-export-pdf">
            {exporting === 'pdf' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
            PDF
          </Button>
        </div>
      </div>

      {/* Filters */}
      {hasFilters && (
        <div className="flex flex-wrap items-end gap-3 mb-4 p-3 bg-[#f1f2f2]/60 rounded-lg border border-gray-100">
          {report.filters.includes('dateRange') && (
            <>
              <div className="w-[140px]">
                <Label className="text-[10px] text-gray-500 uppercase mb-1 block">From</Label>
                <Input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)}
                  className="h-8 text-xs bg-white" data-testid="filter-date-from" />
              </div>
              <div className="w-[140px]">
                <Label className="text-[10px] text-gray-500 uppercase mb-1 block">To</Label>
                <Input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)}
                  className="h-8 text-xs bg-white" data-testid="filter-date-to" />
              </div>
            </>
          )}
          {report.filters.includes('status') && (
            <FilterCombobox label="Status" value={status} onValueChange={setStatus}
              options={filterOptions?.statuses || ['pending', 'confirmed', 'returned', 'cancelled']}
              placeholder="All" testId="filter-status" />
          )}
          {report.filters.includes('client') && (
            <FilterCombobox label="Client" value={client} onValueChange={setClient}
              options={filterOptions?.clients || []} placeholder="All" testId="filter-client" />
          )}
          {report.filters.includes('currency') && (
            <FilterCombobox label="Currency" value={currency} onValueChange={setCurrency}
              options={filterOptions?.currencies || []} placeholder="All" testId="filter-currency" />
          )}
          {report.filters.includes('fromBank') && (
            <FilterCombobox label="From Bank" value={fromBank} onValueChange={setFromBank}
              options={filterOptions?.from_banks || []} placeholder="All" testId="filter-from-bank" />
          )}
          {report.filters.includes('toBank') && (
            <FilterCombobox label="To Bank" value={toBank} onValueChange={setToBank}
              options={filterOptions?.to_banks || []} placeholder="All" testId="filter-to-bank" />
          )}
          {report.filters.includes('auditUser') && (
            <FilterCombobox label="User" value={auditUser} onValueChange={setAuditUser}
              options={filterOptions?.users || []} placeholder="All" testId="filter-audit-user" />
          )}
          {report.filters.includes('groupBy') && (
            <div className="w-[110px]">
              <Label className="text-[10px] text-gray-500 uppercase mb-1 block">Group By</Label>
              <Select value={groupBy} onValueChange={setGroupBy}>
                <SelectTrigger className="h-8 text-xs bg-white" data-testid="filter-group-by">
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

      {/* Table */}
      <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
        <div className="overflow-x-auto max-h-[calc(100vh-260px)]">
          <table className="w-full text-xs" data-testid="report-table">
            <thead className="sticky top-0 z-10">
              <tr className="bg-[#08263e] text-white">
                {report.columns.map(col => (
                  <th key={col.key}
                    className={`px-3 py-2.5 text-left font-medium cursor-pointer select-none hover:bg-[#0d3354] transition-colors whitespace-nowrap ${col.w || ''} ${col.numeric ? 'text-right' : ''}`}
                    onClick={() => handleSort(col.key)}
                    data-testid={`sort-${col.key}`}
                  >
                    <span className="inline-flex items-center gap-1">
                      {col.label}
                      {sortKey === col.key && (
                        <ArrowUpDown className="h-3 w-3 opacity-70" />
                      )}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={report.columns.length} className="text-center py-16 text-gray-400">
                    <Loader2 className="h-5 w-5 animate-spin mx-auto mb-2" />
                    Loading report data...
                  </td>
                </tr>
              ) : displayRows.length === 0 ? (
                <tr>
                  <td colSpan={report.columns.length} className="text-center py-16 text-gray-400">
                    No data found for the selected filters
                  </td>
                </tr>
              ) : (
                displayRows.map((row, i) => (
                  <tr key={i} className={`border-t border-gray-100 hover:bg-[#518dca]/5 transition-colors ${i % 2 === 1 ? 'bg-[#f1f2f2]/40' : ''}`}>
                    {report.columns.map(col => {
                      const val = row[col.key];
                      if (col.key === 'status') {
                        return <td key={col.key} className="px-3 py-2"><StatusBadge status={val} /></td>;
                      }
                      if (col.numeric && val != null) {
                        return <td key={col.key} className="px-3 py-2 text-right tabular-nums font-medium">{fmtNum(val, col.decimals || 2)}</td>;
                      }
                      return <td key={col.key} className="px-3 py-2 truncate max-w-[200px]" title={String(val || '')}>{val || ''}</td>;
                    })}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {/* Footer with pagination */}
        {!loading && displayRows.length > 0 && (
          <div className="px-3 py-2 bg-[#f1f2f2]/60 border-t border-gray-200 flex items-center justify-between text-[10px] text-gray-500">
            <span>
              {isPaginated
                ? `Showing ${(page - 1) * pageSize + 1}-${Math.min(page * pageSize, total)} of ${total.toLocaleString()} records`
                : `Showing ${displayRows.length} of ${total} records`}
            </span>
            {isPaginated && pages > 1 && (
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]"
                  disabled={page <= 1} onClick={() => setPage(1)} data-testid="page-first">
                  First
                </Button>
                <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]"
                  disabled={page <= 1} onClick={() => setPage(p => p - 1)} data-testid="page-prev">
                  Prev
                </Button>
                <span className="px-2 text-[11px] font-medium text-[#08263e]">
                  Page {page} of {pages}
                </span>
                <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]"
                  disabled={page >= pages} onClick={() => setPage(p => p + 1)} data-testid="page-next">
                  Next
                </Button>
                <Button variant="ghost" size="sm" className="h-6 px-2 text-[10px]"
                  disabled={page >= pages} onClick={() => setPage(pages)} data-testid="page-last">
                  Last
                </Button>
              </div>
            )}
            <span>{new Date().toLocaleString()}</span>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Permissions Dialog (Admin) ───────────────────────────────────────────────

const REPORT_LABELS = {
  'deal-blotter': 'Deal Blotter',
  'settlement': 'Settlement Report',
  'open-positions': 'Open Positions',
  'audit-trail': 'Transaction Audit Trail',
  'user-activity': 'User Activity',
  'volume-summary': 'Volume Summary',
  'client-activity': 'Client Activity',
};

function PermissionsDialog({ open, onClose }) {
  const [perms, setPerms] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      api.get('/reports/permissions').then(res => setPerms(res.data.permissions));
    }
  }, [open]);

  const handleToggle = (reportId, role, value) => {
    setPerms(prev => ({
      ...prev,
      [reportId]: { ...prev[reportId], [role]: value },
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put('/reports/permissions', { permissions: perms });
      toast.success('Report permissions saved');
      onClose();
    } catch {
      toast.error('Failed to save permissions');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-lg" data-testid="permissions-dialog">
        <DialogHeader>
          <DialogTitle className="text-[#08263e]">Report Permissions</DialogTitle>
        </DialogHeader>
        <p className="text-xs text-gray-500 -mt-2 mb-4">Enable or disable reports for each role</p>
        {!perms ? (
          <div className="flex justify-center py-8"><Loader2 className="h-5 w-5 animate-spin text-[#518dca]" /></div>
        ) : (
          <div className="space-y-0">
            {/* Header */}
            <div className="grid grid-cols-[1fr_60px_60px_60px] gap-2 pb-2 border-b border-gray-200 mb-2">
              <span className="text-[10px] font-medium text-gray-500 uppercase">Report</span>
              <span className="text-[10px] font-medium text-gray-500 uppercase text-center">Trader</span>
              <span className="text-[10px] font-medium text-gray-500 uppercase text-center">Treasury</span>
              <span className="text-[10px] font-medium text-gray-500 uppercase text-center">Admin</span>
            </div>
            {Object.entries(perms).map(([rid, roles]) => (
              <div key={rid} className="grid grid-cols-[1fr_60px_60px_60px] gap-2 items-center py-2 border-b border-gray-50">
                <span className="text-xs font-medium text-[#08263e]">{REPORT_LABELS[rid] || rid}</span>
                {['trader', 'treasury', 'admin'].map(role => (
                  <div key={role} className="flex justify-center">
                    <Switch
                      checked={roles[role] ?? false}
                      onCheckedChange={(v) => handleToggle(rid, role, v)}
                      data-testid={`perm-${rid}-${role}`}
                      disabled={rid === 'audit-trail' && role === 'admin'}
                    />
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline" size="sm" onClick={onClose}>Cancel</Button>
          <Button size="sm" onClick={handleSave} disabled={saving || !perms}
            className="bg-[#08263e] text-white" data-testid="perm-save-btn">
            {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : null}
            Save Permissions
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ── Main Page ───────────────────────────────────────────────────────────────

export default function ReportsPage() {
  const { user } = useAuth();
  const role = user?.role || '';
  const [activeReport, setActiveReport] = useState(null);
  const [permissions, setPermissions] = useState(null);
  const [showSettings, setShowSettings] = useState(false);

  // Fetch permissions on mount
  useEffect(() => {
    let cancelled = false;
    api.get('/reports/permissions').then(res => {
      if (!cancelled) setPermissions(res.data.permissions);
    }).catch(() => {});
    return () => { cancelled = true; };
  }, [showSettings]); // refetch after settings dialog closes

  // Filter reports based on permissions
  const visibleReports = Object.entries(REPORTS).filter(([id]) => {
    if (!permissions) return false;
    const rp = permissions[id];
    if (!rp) return false;
    // For admin, the full permissions object is returned
    if (role === 'admin') return rp.admin !== false;
    // For other roles, check their specific role
    return rp[role] === true;
  });

  if (activeReport && REPORTS[activeReport]) {
    return (
      <ReportViewer
        reportId={activeReport}
        report={REPORTS[activeReport]}
        onBack={() => setActiveReport(null)}
      />
    );
  }

  return (
    <>
      <ReportSelector
        reports={visibleReports}
        onSelect={setActiveReport}
        isAdmin={role === 'admin'}
        onOpenSettings={() => setShowSettings(true)}
      />
      {role === 'admin' && (
        <PermissionsDialog open={showSettings} onClose={() => setShowSettings(false)} />
      )}
    </>
  );
}
