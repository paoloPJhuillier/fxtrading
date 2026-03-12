import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { Eye, FileText, Filter, X, Image as ImageIcon, Download, ChevronLeft, ChevronRight } from 'lucide-react';
import { format } from 'date-fns';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const SB = { pending: 'bg-yellow-100 text-yellow-800', confirmed: 'bg-green-100 text-green-800', returned: 'bg-red-100 text-red-800', cancelled: 'bg-slate-200 text-slate-600' };
const PAGE_SIZE = 20;

export default function TransactionHistoryPage() {
  const [data, setData] = useState({ deals: [], total: 0, page: 1, pages: 1 });
  const [filter, setFilter] = useState({ status: 'all', client: '', currency: '', date_from: '', date_to: '' });
  const [debouncedFilter, setDebouncedFilter] = useState(filter);
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [loading, setLoading] = useState(true);
  const [sel, setSel] = useState(null);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedFilter(filter), 400);
    return () => clearTimeout(t);
  }, [filter]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', page);
      params.append('limit', PAGE_SIZE);
      if (debouncedFilter.status !== 'all') params.append('status', debouncedFilter.status);
      if (debouncedFilter.client) params.append('client', debouncedFilter.client);
      if (debouncedFilter.currency) params.append('currency', debouncedFilter.currency);
      if (debouncedFilter.date_from) params.append('date_from', debouncedFilter.date_from);
      if (debouncedFilter.date_to) params.append('date_to', debouncedFilter.date_to);
      const res = await api.get(`/deals?${params.toString()}`);
      setData(res.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [debouncedFilter, page]);

  useEffect(() => { load(); }, [load]);

  const clearFilters = () => { setFilter({ status: 'all', client: '', currency: '', date_from: '', date_to: '' }); setPage(1); };
  const hasFilters = filter.status !== 'all' || filter.client || filter.currency || filter.date_from || filter.date_to;
  const updateFilter = (k, v) => { setFilter(p => ({ ...p, [k]: v })); setPage(1); };

  const exportCSV = async () => {
    try {
      const params = new URLSearchParams();
      if (filter.status !== 'all') params.append('status', filter.status);
      if (filter.client) params.append('client', filter.client);
      if (filter.currency) params.append('currency', filter.currency);
      if (filter.date_from) params.append('date_from', filter.date_from);
      if (filter.date_to) params.append('date_to', filter.date_to);
      const q = params.toString();
      const res = await api.get(`/deals/export${q ? '?' + q : ''}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `deals_export_${new Date().toISOString().slice(0,10)}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) { console.error('Export failed', e); }
  };

  return (
    <div data-testid="transaction-history-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Transaction History</h1>
          <p className="text-sm text-slate-500 mt-1">{data.total} transaction{data.total !== 1 ? 's' : ''}</p>
        </div>
        <div className="flex gap-2">
          <Button variant={showFilters ? 'default' : 'outline'} size="sm" onClick={() => setShowFilters(!showFilters)} className={showFilters ? 'bg-[#518dca]' : ''} data-testid="tx-toggle-filters">
            <Filter className="h-3.5 w-3.5 mr-1.5" /> Filters {hasFilters && <Badge className="ml-1.5 bg-[#ec474e] text-white text-[10px] px-1.5 py-0">Active</Badge>}
          </Button>
          <Button variant="outline" size="sm" onClick={exportCSV} data-testid="export-csv-btn">
            <Download className="h-3.5 w-3.5 mr-1.5" /> Export CSV
          </Button>
        </div>
      </div>

      {showFilters && (
        <Card className="mb-6" data-testid="tx-filters-panel">
          <CardContent className="py-4">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              <div className="space-y-1"><Label className="text-xs">Status</Label>
                <Select value={filter.status} onValueChange={v => updateFilter('status', v)}>
                  <SelectTrigger className="h-8 text-xs"><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="all">All</SelectItem><SelectItem value="pending">Pending</SelectItem><SelectItem value="confirmed">Confirmed</SelectItem><SelectItem value="returned">Returned</SelectItem><SelectItem value="cancelled">Cancelled</SelectItem></SelectContent>
                </Select>
              </div>
              <div className="space-y-1"><Label className="text-xs">Client</Label>
                <Input className="h-8 text-xs" placeholder="Search client..." value={filter.client} onChange={e => updateFilter('client', e.target.value)} />
              </div>
              <div className="space-y-1"><Label className="text-xs">Currency</Label>
                <Input className="h-8 text-xs" placeholder="e.g. USD" value={filter.currency} onChange={e => updateFilter('currency', e.target.value.toUpperCase())} />
              </div>
              <div className="space-y-1"><Label className="text-xs">Date From</Label>
                <Input type="date" className="h-8 text-xs" value={filter.date_from} onChange={e => updateFilter('date_from', e.target.value)} />
              </div>
              <div className="space-y-1"><Label className="text-xs">Date To</Label>
                <Input type="date" className="h-8 text-xs" value={filter.date_to} onChange={e => updateFilter('date_to', e.target.value)} />
              </div>
            </div>
            {hasFilters && <Button variant="ghost" size="sm" className="mt-3 text-xs text-slate-500" onClick={clearFilters}><X className="h-3 w-3 mr-1" /> Clear Filters</Button>}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-32"><div className="animate-spin h-6 w-6 border-4 border-[#518dca] border-t-transparent rounded-full" /></div>
          ) : data.deals.length === 0 ? (
            <div className="text-center py-16"><FileText className="h-12 w-12 text-slate-300 mx-auto mb-3" /><p className="text-slate-500">No transactions found</p></div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Reference</TableHead><TableHead>Client</TableHead><TableHead>Trader</TableHead>
                  <TableHead>Pair</TableHead><TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right">Rate</TableHead><TableHead>Deal Date</TableHead>
                  <TableHead>Status</TableHead><TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.deals.map(d => (
                  <TableRow key={d.id} data-testid={`tx-row-${d.id}`}>
                    <TableCell className="font-mono text-xs font-medium text-[#08263e]">{d.reference_number}</TableCell>
                    <TableCell className="text-sm">{d.client_name || '-'}</TableCell>
                    <TableCell className="text-sm">{d.created_by_name}</TableCell>
                    <TableCell className="font-mono text-xs">{d.buy_currency}/{d.sell_currency}</TableCell>
                    <TableCell className="text-right font-mono text-xs">{Number(d.amount).toLocaleString()}</TableCell>
                    <TableCell className="text-right font-mono text-xs">{d.rate}</TableCell>
                    <TableCell className="text-xs">{format(new Date(d.deal_date + 'T00:00:00'), 'dd MMM yyyy')}</TableCell>
                    <TableCell><Badge className={SB[d.status]}>{d.status}</Badge></TableCell>
                    <TableCell><Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => setSel(d)} data-testid={`tx-view-${d.id}`}><Eye className="h-3.5 w-3.5" /></Button></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {data.pages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-xs text-slate-400">Page {data.page} of {data.pages} ({data.total} transactions)</p>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" disabled={page <= 1} onClick={() => setPage(p => p - 1)} data-testid="tx-prev-page">
              <ChevronLeft className="h-3.5 w-3.5 mr-1" /> Previous
            </Button>
            <Button size="sm" variant="outline" disabled={page >= data.pages} onClick={() => setPage(p => p + 1)} data-testid="tx-next-page">
              Next <ChevronRight className="h-3.5 w-3.5 ml-1" />
            </Button>
          </div>
        </div>
      )}

      <Dialog open={!!sel} onOpenChange={o => !o && setSel(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="tx-detail-dialog">
          <DialogHeader><DialogTitle style={{ fontFamily: 'Chivo' }} className="text-[#08263e]">Deal Details - {sel?.reference_number}</DialogTitle></DialogHeader>
          {sel && (
            <div className="space-y-4">
              <Badge className={SB[sel.status] + ' text-xs'}>{sel.status}</Badge>
              <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
                <DI label="Client" val={sel.client_name} />
                <DI label="Transaction Type" val={sel.transaction_type} />
                <DI label="Transfer Type" val={sel.transfer_type} />
                <DI label="Deal Date" val={format(new Date(sel.deal_date + 'T00:00:00'), 'dd MMM yyyy')} />
                <DI label="Value Date" val={format(new Date(sel.value_date + 'T00:00:00'), 'dd MMM yyyy')} />
                <DI label="Buy Currency" val={sel.buy_currency} />
                <DI label="Sell Currency" val={sel.sell_currency} />
                <DI label={`Currency Amount (${sel.buy_currency})`} val={Number(sel.currency_amount).toLocaleString()} mono />
                <DI label="Exchange Rate" val={sel.rate} mono />
                <DI label={`Converted Amount (${sel.sell_currency})`} val={Number(sel.amount).toLocaleString()} mono />
                <AcctInfo deal={sel} prefix="from" label="From" />
                <AcctInfo deal={sel} prefix="to" label="To" />
                <DI label="Created By" val={sel.created_by_name} />
                {sel.processed_by_name && <DI label="Processed By" val={sel.processed_by_name} />}
              </div>
              <OursInfo deal={sel} />
              {sel.remarks && (<div className="bg-slate-50 p-3 rounded-md"><p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Remarks</p><p className="text-sm">{sel.remarks}</p></div>)}
              {sel.treasury_remarks && (<div className="bg-blue-50 p-3 rounded-md"><p className="text-[10px] text-blue-400 uppercase tracking-wider mb-1">Treasury Remarks</p><p className="text-sm">{sel.treasury_remarks}</p></div>)}
              {sel.cancellation_reason && (<div className="bg-red-50 border border-red-200 p-3 rounded-md"><p className="text-[10px] text-red-400 uppercase tracking-wider mb-1">Cancellation Reason</p><p className="text-sm text-red-700">{sel.cancellation_reason}</p></div>)}
              {sel.settlement_proofs?.length > 0 && (
                <>
                  <Separator />
                  <div>
                    <p className="text-xs font-medium text-slate-600 uppercase tracking-wider mb-2">Settlement Proofs</p>
                    <div className="grid grid-cols-3 gap-2">
                      {sel.settlement_proofs.map(p => (
                        <a key={p.id} href={`${BACKEND_URL}/api/files/${p.path}`} target="_blank" rel="noopener noreferrer" className="block border rounded overflow-hidden hover:ring-2 ring-[#518dca]">
                          <img src={`${BACKEND_URL}/api/files/${p.path}`} alt={p.filename} className="w-full h-20 object-cover" />
                          <p className="text-[10px] text-slate-500 p-1 truncate">{p.filename}</p>
                        </a>
                      ))}
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function DI({ label, val, mono }) {
  return (<div><p className="text-[10px] text-slate-400 uppercase tracking-wider">{label}</p><p className={`text-sm font-medium ${mono ? 'font-mono' : ''}`}>{val || '-'}</p></div>);
}
function AcctInfo({ deal, prefix, label }) {
  const type = deal[`${prefix}_type`] || 'bank';
  return (<div><p className="text-[10px] text-slate-400 uppercase tracking-wider">{label}</p>
    {type === 'crypto' ? (<p className="text-sm font-medium">{deal[`${prefix}_company`]} / <span className="font-mono text-xs">{deal[`${prefix}_wallet_address`] || '-'}</span></p>)
    : (<p className="text-sm font-medium">{deal[`${prefix}_company`] || ''} / {deal[`${prefix}_bank`] || ''} <span className="font-mono text-xs">({deal[`${prefix}_account_num`] || '-'})</span></p>)}
  </div>);
}
function OursInfo({ deal }) {
  const type = deal.ours_type || 'bank';
  return (<div className="bg-yellow-50 border border-yellow-200 p-3 rounded-md"><p className="text-[10px] text-yellow-700 uppercase tracking-wider font-semibold mb-1">Ours (Receiving Account)</p>
    {type === 'crypto' ? (<p className="text-sm font-medium font-mono">{deal.ours_wallet_address || '-'}</p>)
    : (<p className="text-sm font-medium">{deal.ours_bank || '-'} <span className="font-mono text-xs">({deal.ours_account_num || '-'})</span></p>)}
  </div>);
}
