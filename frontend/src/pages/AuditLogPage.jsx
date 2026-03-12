import { useState, useEffect, useCallback, memo } from 'react';
import api from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Filter, X, ChevronLeft, ChevronRight, Activity } from 'lucide-react';
import { format } from 'date-fns';

const ACTION_LABELS = {
  deal_created: { label: 'Deal Created', color: 'bg-blue-100 text-blue-800' },
  deal_confirmed: { label: 'Deal Confirmed', color: 'bg-green-100 text-green-800' },
  deal_returned: { label: 'Deal Returned', color: 'bg-red-100 text-red-800' },
  deal_cancelled: { label: 'Deal Cancelled', color: 'bg-slate-200 text-slate-600' },
  proof_uploaded: { label: 'Proof Uploaded', color: 'bg-purple-100 text-purple-800' },
  proof_deleted: { label: 'Proof Deleted', color: 'bg-orange-100 text-orange-800' },
  user_created: { label: 'User Created', color: 'bg-teal-100 text-teal-800' },
  user_updated: { label: 'User Updated', color: 'bg-yellow-100 text-yellow-800' },
  user_deleted: { label: 'User Deleted', color: 'bg-red-100 text-red-800' },
};

const ENTITY_BADGE = {
  deal: 'bg-[#08263e]/10 text-[#08263e]',
  user: 'bg-[#518dca]/10 text-[#518dca]',
};

export default function AuditLogPage() {
  const [data, setData] = useState({ logs: [], total: 0, page: 1, pages: 1 });
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState({ action: 'all', entity_type: 'all', user_name: '', date_from: '', date_to: '' });
  const [debouncedFilter, setDebouncedFilter] = useState(filter);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedFilter(filter), 400);
    return () => clearTimeout(t);
  }, [filter]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', page);
      params.append('limit', 50);
      if (debouncedFilter.action !== 'all') params.append('action', debouncedFilter.action);
      if (debouncedFilter.entity_type !== 'all') params.append('entity_type', debouncedFilter.entity_type);
      if (debouncedFilter.user_name) params.append('user_name', debouncedFilter.user_name);
      if (debouncedFilter.date_from) params.append('date_from', debouncedFilter.date_from);
      if (debouncedFilter.date_to) params.append('date_to', debouncedFilter.date_to);
      const res = await api.get(`/audit-logs?${params.toString()}`);
      setData(res.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [page, debouncedFilter]);

  useEffect(() => { load(); }, [load]);

  const clearFilters = () => { setFilter({ action: 'all', entity_type: 'all', user_name: '', date_from: '', date_to: '' }); setPage(1); };
  const hasFilters = filter.action !== 'all' || filter.entity_type !== 'all' || filter.user_name || filter.date_from || filter.date_to;

  return (
    <div data-testid="audit-log-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Audit Trail</h1>
          <p className="text-sm text-slate-500 mt-1">{data.total} log entries</p>
        </div>
        <Button variant={showFilters ? 'default' : 'outline'} size="sm" onClick={() => setShowFilters(!showFilters)} data-testid="audit-toggle-filters" className={showFilters ? 'bg-[#518dca]' : ''}>
          <Filter className="h-3.5 w-3.5 mr-1.5" /> Filters {hasFilters && <Badge className="ml-1.5 bg-[#ec474e] text-white text-[10px] px-1.5 py-0">Active</Badge>}
        </Button>
      </div>

      {showFilters && (
        <Card className="mb-6" data-testid="audit-filters-panel">
          <CardContent className="py-4">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              <div className="space-y-1"><Label className="text-xs">Action</Label>
                <Select value={filter.action} onValueChange={v => { setFilter(p => ({ ...p, action: v })); setPage(1); }}>
                  <SelectTrigger className="h-8 text-xs" data-testid="audit-filter-action"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Actions</SelectItem>
                    {Object.entries(ACTION_LABELS).map(([k, v]) => <SelectItem key={k} value={k}>{v.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1"><Label className="text-xs">Entity Type</Label>
                <Select value={filter.entity_type} onValueChange={v => { setFilter(p => ({ ...p, entity_type: v })); setPage(1); }}>
                  <SelectTrigger className="h-8 text-xs" data-testid="audit-filter-entity"><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="all">All</SelectItem><SelectItem value="deal">Deals</SelectItem><SelectItem value="user">Users</SelectItem></SelectContent>
                </Select>
              </div>
              <div className="space-y-1"><Label className="text-xs">User</Label>
                <Input className="h-8 text-xs" placeholder="Search user..." value={filter.user_name} onChange={e => { setFilter(p => ({ ...p, user_name: e.target.value })); setPage(1); }} data-testid="audit-filter-user" />
              </div>
              <div className="space-y-1"><Label className="text-xs">Date From</Label>
                <Input type="date" className="h-8 text-xs" value={filter.date_from} onChange={e => { setFilter(p => ({ ...p, date_from: e.target.value })); setPage(1); }} data-testid="audit-filter-date-from" />
              </div>
              <div className="space-y-1"><Label className="text-xs">Date To</Label>
                <Input type="date" className="h-8 text-xs" value={filter.date_to} onChange={e => { setFilter(p => ({ ...p, date_to: e.target.value })); setPage(1); }} data-testid="audit-filter-date-to" />
              </div>
            </div>
            {hasFilters && <Button variant="ghost" size="sm" className="mt-3 text-xs text-slate-500" onClick={clearFilters} data-testid="audit-clear-filters"><X className="h-3 w-3 mr-1" /> Clear Filters</Button>}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-32"><div className="animate-spin h-6 w-6 border-4 border-[#518dca] border-t-transparent rounded-full" /></div>
          ) : data.logs.length === 0 ? (
            <div className="text-center py-16">
              <Activity className="h-12 w-12 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500">No audit entries found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Entity</TableHead>
                  <TableHead>Reference</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Details</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.logs.map(log => (
                  <AuditRow key={log.id} log={log} />
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {data.pages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-xs text-slate-400">Page {data.page} of {data.pages} ({data.total} entries)</p>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" disabled={page <= 1} onClick={() => setPage(p => p - 1)} data-testid="audit-prev-page">
              <ChevronLeft className="h-3.5 w-3.5 mr-1" /> Previous
            </Button>
            <Button size="sm" variant="outline" disabled={page >= data.pages} onClick={() => setPage(p => p + 1)} data-testid="audit-next-page">
              Next <ChevronRight className="h-3.5 w-3.5 ml-1" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

const AuditRow = memo(function AuditRow({ log }) {
  const actionInfo = ACTION_LABELS[log.action] || { label: log.action, color: 'bg-slate-100 text-slate-600' };
  const entityColor = ENTITY_BADGE[log.entity_type] || 'bg-slate-100 text-slate-600';
  return (
    <TableRow data-testid={`audit-row-${log.id}`}>
      <TableCell className="text-xs text-slate-500 whitespace-nowrap">{format(new Date(log.created_at), 'dd MMM yyyy HH:mm:ss')}</TableCell>
      <TableCell><Badge className={`${actionInfo.color} text-[10px]`}>{actionInfo.label}</Badge></TableCell>
      <TableCell><Badge variant="outline" className={`${entityColor} text-[10px] border-0`}>{log.entity_type}</Badge></TableCell>
      <TableCell className="font-mono text-xs">{log.entity_ref || '-'}</TableCell>
      <TableCell>
        <div>
          <p className="text-xs font-medium">{log.user_name}</p>
          <p className="text-[10px] text-slate-400 capitalize">{log.user_role}</p>
        </div>
      </TableCell>
      <TableCell className="text-xs text-slate-600 max-w-xs truncate">{log.details}</TableCell>
    </TableRow>
  );
});
