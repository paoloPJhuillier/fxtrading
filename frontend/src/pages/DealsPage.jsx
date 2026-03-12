import { useState, useEffect, useCallback, useRef, memo, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { Plus, FileText, Eye, Filter, X, Ban, Image as ImageIcon, Download, Upload, Trash2, RotateCcw, ChevronLeft, ChevronRight } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const SB = {
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-green-100 text-green-800',
  returned: 'bg-red-100 text-red-800',
  cancelled: 'bg-slate-200 text-slate-600',
};
const PAGE_SIZE = 20;

export default function DealsPage() {
  const [data, setData] = useState({ deals: [], total: 0, page: 1, pages: 1 });
  const [filter, setFilter] = useState({ status: 'all', client: '', currency: '', date_from: '', date_to: '' });
  const [debouncedFilter, setDebouncedFilter] = useState(filter);
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [loading, setLoading] = useState(true);
  const [_sel, _setSel] = useState(null);
  const selRef = useRef(null);
  if (_sel) selRef.current = _sel;
  const sel = _sel || selRef.current;
  const [cancelOpen, setCancelOpen] = useState(false);
  const [cancelReason, setCancelReason] = useState('');
  const [cancelling, setCancelling] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [resubmitting, setResubmitting] = useState(false);
  const fileRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const t = setTimeout(() => setDebouncedFilter(filter), 400);
    return () => clearTimeout(t);
  }, [filter]);

  const fetchDeals = useCallback(async () => {
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
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, [debouncedFilter, page]);

  useEffect(() => { fetchDeals(); }, [fetchDeals]);

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
      a.download = `my_deals_export_${new Date().toISOString().slice(0,10)}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) { console.error('Export failed', e); }
  };

  const handleCancel = async () => {
    if (!cancelReason.trim()) { toast.error('Cancellation reason is required'); return; }
    setCancelling(true);
    try {
      await api.put(`/deals/${sel.id}/cancel`, { cancellation_reason: cancelReason });
      toast.success('Deal cancelled successfully');
      setCancelOpen(false); setCancelReason(''); _setSel(null); fetchDeals();
    } catch (err) { toast.error(err.response?.data?.detail || 'Cancel failed'); }
    finally { setCancelling(false); }
  };

  const uploadProof = async (e) => {
    if (!sel || !e.target.files?.length) return;
    setUploading(true);
    try {
      for (const file of e.target.files) {
        const fd = new FormData();
        fd.append('file', file);
        await api.post(`/deals/${sel.id}/upload`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      }
      const res = await api.get(`/deals/${sel.id}`);
      _setSel(res.data);
      toast.success('Proof of payment uploaded');
    } catch (err) { toast.error(err.response?.data?.detail || 'Upload failed'); }
    finally { setUploading(false); e.target.value = ''; }
  };

  const deleteProof = async (proofId) => {
    if (!sel) return;
    try {
      await api.delete(`/deals/${sel.id}/proofs/${proofId}`);
      const res = await api.get(`/deals/${sel.id}`);
      _setSel(res.data);
      toast.success('Proof removed');
    } catch (err) { toast.error('Delete failed'); }
  };

  const handleResubmit = async () => {
    if (!sel) return;
    setResubmitting(true);
    try {
      await api.put(`/deals/${sel.id}/resubmit`);
      toast.success('Deal resubmitted for review');
      _setSel(null); fetchDeals();
    } catch (err) { toast.error(err.response?.data?.detail || 'Resubmit failed'); }
    finally { setResubmitting(false); }
  };

  const viewDeal = useCallback(async (dealId) => {
    const r = await api.get(`/deals/${dealId}`);
    _setSel(r.data);
  }, []);

  return (
    <div data-testid="deals-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo' }}>My Deals</h1>
          <p className="text-sm text-slate-500 mt-1">{data.total} deal{data.total !== 1 ? 's' : ''}</p>
        </div>
        <div className="flex gap-2">
          <Button variant={showFilters ? 'default' : 'outline'} size="sm" onClick={() => setShowFilters(!showFilters)} data-testid="toggle-filters-btn" className={showFilters ? 'bg-[#518dca]' : ''}>
            <Filter className="h-3.5 w-3.5 mr-1.5" /> Filters {hasFilters && <Badge className="ml-1.5 bg-[#ec474e] text-white text-[10px] px-1.5 py-0">Active</Badge>}
          </Button>
          <Button variant="outline" size="sm" onClick={exportCSV} data-testid="export-csv-btn">
            <Download className="h-3.5 w-3.5 mr-1.5" /> Export CSV
          </Button>
          <Button className="bg-[#08263e] hover:bg-[#08263e]/90" size="sm" onClick={() => navigate('/deals/new')} data-testid="new-deal-btn">
            <Plus className="h-4 w-4 mr-1.5" /> New Deal
          </Button>
        </div>
      </div>

      {showFilters && (
        <Card className="mb-6" data-testid="filters-panel">
          <CardContent className="py-4">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              <div className="space-y-1"><Label className="text-xs">Status</Label>
                <Select value={filter.status} onValueChange={v => updateFilter('status', v)}>
                  <SelectTrigger className="h-8 text-xs" data-testid="filter-status"><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="all">All</SelectItem><SelectItem value="pending">Pending</SelectItem><SelectItem value="confirmed">Confirmed</SelectItem><SelectItem value="returned">Returned</SelectItem><SelectItem value="cancelled">Cancelled</SelectItem></SelectContent>
                </Select>
              </div>
              <div className="space-y-1"><Label className="text-xs">Client</Label>
                <Input className="h-8 text-xs" placeholder="Search client..." value={filter.client} onChange={e => updateFilter('client', e.target.value)} data-testid="filter-client" />
              </div>
              <div className="space-y-1"><Label className="text-xs">Currency</Label>
                <Input className="h-8 text-xs" placeholder="e.g. USD" value={filter.currency} onChange={e => updateFilter('currency', e.target.value.toUpperCase())} data-testid="filter-currency" />
              </div>
              <div className="space-y-1"><Label className="text-xs">Date From</Label>
                <Input type="date" className="h-8 text-xs" value={filter.date_from} onChange={e => updateFilter('date_from', e.target.value)} data-testid="filter-date-from" />
              </div>
              <div className="space-y-1"><Label className="text-xs">Date To</Label>
                <Input type="date" className="h-8 text-xs" value={filter.date_to} onChange={e => updateFilter('date_to', e.target.value)} data-testid="filter-date-to" />
              </div>
            </div>
            {hasFilters && <Button variant="ghost" size="sm" className="mt-3 text-xs text-slate-500" onClick={clearFilters} data-testid="clear-filters-btn"><X className="h-3 w-3 mr-1" /> Clear Filters</Button>}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          {loading && data.deals.length === 0 ? (
            <div className="flex items-center justify-center h-32"><div className="animate-spin h-6 w-6 border-4 border-[#518dca] border-t-transparent rounded-full" /></div>
          ) : data.deals.length === 0 ? (
            <div className="text-center py-16">
              <FileText className="h-12 w-12 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500">No deals found</p>
              <Button className="mt-4 bg-[#08263e] hover:bg-[#08263e]/90" onClick={() => navigate('/deals/new')} data-testid="empty-new-deal-btn"><Plus className="h-4 w-4 mr-2" /> Create First Deal</Button>
            </div>
          ) : (
            <div className={loading ? 'opacity-60 pointer-events-none transition-opacity' : 'transition-opacity'}>
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Reference</TableHead><TableHead>Client</TableHead><TableHead>Type</TableHead>
                  <TableHead>Pair</TableHead><TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right">Rate</TableHead><TableHead>Deal Date</TableHead>
                  <TableHead>Status</TableHead><TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.deals.map(deal => (
                  <DealRow key={deal.id} deal={deal} onView={viewDeal} />
                ))}
              </TableBody>
            </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {data.pages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-xs text-slate-400">Page {data.page} of {data.pages} ({data.total} deals)</p>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" disabled={page <= 1} onClick={() => setPage(p => p - 1)} data-testid="deals-prev-page">
              <ChevronLeft className="h-3.5 w-3.5 mr-1" /> Previous
            </Button>
            <Button size="sm" variant="outline" disabled={page >= data.pages} onClick={() => setPage(p => p + 1)} data-testid="deals-next-page">
              Next <ChevronRight className="h-3.5 w-3.5 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Deal Detail Dialog */}
      <Dialog open={!!_sel && !cancelOpen} onOpenChange={o => { if (!o) _setSel(null); }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="deal-detail-dialog">
          <DialogHeader><DialogTitle className="text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Deal Details - {sel?.reference_number}</DialogTitle></DialogHeader>
          {sel && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <Badge className={SB[sel.status] + ' text-xs'}>{sel.status}</Badge>
                <div className="flex gap-2">
                  {sel.status === 'returned' && (
                    <Button size="sm" className="bg-[#518dca] hover:bg-[#518dca]/90 text-white" onClick={handleResubmit} disabled={resubmitting} data-testid="resubmit-deal-btn">
                      <RotateCcw className="h-3.5 w-3.5 mr-1.5" /> {resubmitting ? 'Resubmitting...' : 'Resubmit'}
                    </Button>
                  )}
                  {sel.status === 'pending' && (
                    <Button size="sm" variant="outline" className="text-red-600 border-red-200 hover:bg-red-50" onClick={() => setCancelOpen(true)} data-testid="cancel-deal-btn">
                      <Ban className="h-3.5 w-3.5 mr-1.5" /> Cancel / Recall
                    </Button>
                  )}
                </div>
              </div>
              {sel.status === 'returned' && sel.treasury_remarks && (
                <div className="bg-red-50 border border-red-300 p-4 rounded-md" data-testid="returned-alert">
                  <p className="text-xs font-semibold text-red-700 uppercase tracking-wider mb-1">Deal Returned by Treasury</p>
                  <p className="text-sm text-red-800">{sel.treasury_remarks}</p>
                  <p className="text-[10px] text-red-500 mt-2">Please upload an acceptable proof of payment and click Resubmit.</p>
                </div>
              )}
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
              <div className="bg-slate-50 p-3 rounded-md text-center font-mono text-sm font-medium text-[#08263e]">
                {Number(sel.currency_amount).toLocaleString()} {sel.buy_currency} x {sel.rate} = {Number(sel.amount).toLocaleString()} {sel.sell_currency}
              </div>
              <OursInfo deal={sel} />
              {sel.remarks && (<div className="bg-slate-50 p-3 rounded-md"><p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Remarks</p><p className="text-sm">{sel.remarks}</p></div>)}
              {sel.status !== 'returned' && sel.treasury_remarks && (<div className="bg-blue-50 p-3 rounded-md"><p className="text-[10px] text-blue-400 uppercase tracking-wider mb-1">Treasury Remarks</p><p className="text-sm">{sel.treasury_remarks}</p></div>)}
              {sel.cancellation_reason && (<div className="bg-red-50 border border-red-200 p-3 rounded-md"><p className="text-[10px] text-red-400 uppercase tracking-wider mb-1">Cancellation Reason</p><p className="text-sm text-red-700">{sel.cancellation_reason}</p></div>)}
              <Separator />
              <div>
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs font-medium text-slate-600 uppercase tracking-wider">Proof of Payment</p>
                  {(sel.status === 'pending' || sel.status === 'returned') && (
                    <div>
                      <input type="file" ref={fileRef} className="hidden" accept="image/*" multiple onChange={uploadProof} />
                      <Button size="sm" variant="outline" onClick={() => fileRef.current?.click()} disabled={uploading} data-testid="upload-proof-btn">
                        <Upload className="h-3 w-3 mr-1.5" /> {uploading ? 'Uploading...' : 'Upload Proof'}
                      </Button>
                    </div>
                  )}
                </div>
                {sel.settlement_proofs?.length > 0 ? (
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {sel.settlement_proofs.map(p => (
                      <div key={p.id} className="relative group border rounded-lg overflow-hidden">
                        <img src={`${BACKEND_URL}/api/files/${p.path}`} alt={p.filename} className="w-full h-28 object-cover" loading="lazy" decoding="async" />
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                          <a href={`${BACKEND_URL}/api/files/${p.path}`} target="_blank" rel="noopener noreferrer" className="text-white"><Eye className="h-4 w-4" /></a>
                          {(sel.status === 'pending' || sel.status === 'returned') && (
                            <button onClick={() => deleteProof(p.id)} className="text-white hover:text-red-300"><Trash2 className="h-4 w-4" /></button>
                          )}
                        </div>
                        <p className="text-[10px] text-slate-500 p-1.5 truncate">{p.filename}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6 border border-dashed rounded-lg">
                    <ImageIcon className="h-8 w-8 text-slate-300 mx-auto mb-2" />
                    <p className="text-xs text-slate-400">No proof of payment uploaded yet</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Cancel Deal Dialog */}
      <Dialog open={cancelOpen} onOpenChange={o => { if (!o) { setCancelOpen(false); setCancelReason(''); } }}>
        <DialogContent className="max-w-md" data-testid="cancel-deal-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600" style={{ fontFamily: 'Chivo' }}>
              <Ban className="h-5 w-5" /> Cancel / Recall Deal
            </DialogTitle>
          </DialogHeader>
          <p className="text-sm text-slate-500">You are about to cancel deal <span className="font-mono font-medium">{sel?.reference_number}</span>. This action cannot be undone.</p>
          <div className="space-y-1.5">
            <Label className="text-xs">Cancellation Reason <span className="text-red-500">*</span></Label>
            <Textarea value={cancelReason} onChange={e => setCancelReason(e.target.value)} placeholder="Please explain the reason for cancellation..." rows={4} data-testid="cancel-reason-input" />
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => { setCancelOpen(false); setCancelReason(''); }} data-testid="cancel-dialog-back-btn">Go Back</Button>
            <Button className="bg-red-600 hover:bg-red-700 text-white" onClick={handleCancel} disabled={cancelling || !cancelReason.trim()} data-testid="confirm-cancel-deal-btn">
              {cancelling ? 'Cancelling...' : 'Confirm Cancellation'}
            </Button>
          </DialogFooter>
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
  return (
    <div>
      <p className="text-[10px] text-slate-400 uppercase tracking-wider">{label}</p>
      {type === 'crypto' ? (
        <p className="text-sm font-medium">{deal[`${prefix}_company`]} / <span className="font-mono text-xs">{deal[`${prefix}_wallet_address`] || '-'}</span></p>
      ) : (
        <p className="text-sm font-medium">{deal[`${prefix}_company`] || ''} / {deal[`${prefix}_bank`] || ''} <span className="font-mono text-xs">({deal[`${prefix}_account_num`] || '-'})</span></p>
      )}
    </div>
  );
}

function OursInfo({ deal }) {
  const type = deal.ours_type || 'bank';
  return (
    <div className="bg-yellow-50 border border-yellow-200 p-3 rounded-md">
      <p className="text-[10px] text-yellow-700 uppercase tracking-wider font-semibold mb-1">Ours (Receiving Account)</p>
      {type === 'crypto' ? (
        <p className="text-sm font-medium font-mono">{deal.ours_wallet_address || '-'}</p>
      ) : (
        <p className="text-sm font-medium">{deal.ours_bank || '-'} <span className="font-mono text-xs">({deal.ours_account_num || '-'})</span></p>
      )}
    </div>
  );
}

const DealRow = memo(function DealRow({ deal, onView }) {
  return (
    <TableRow data-testid={`deal-row-${deal.id}`}>
      <TableCell className="font-mono text-xs font-medium text-[#08263e]">{deal.reference_number}</TableCell>
      <TableCell className="text-sm">{deal.client_name || '-'}</TableCell>
      <TableCell className="text-sm">{deal.transaction_type}</TableCell>
      <TableCell className="font-mono text-xs">{deal.buy_currency}/{deal.sell_currency}</TableCell>
      <TableCell className="text-right font-mono text-xs">{Number(deal.amount).toLocaleString()}</TableCell>
      <TableCell className="text-right font-mono text-xs">{deal.rate}</TableCell>
      <TableCell className="text-xs">{format(new Date(deal.deal_date + 'T00:00:00'), 'dd MMM yyyy')}</TableCell>
      <TableCell><Badge className={SB[deal.status]}>{deal.status}</Badge></TableCell>
      <TableCell>
        <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => onView(deal.id)} data-testid={`view-deal-${deal.id}`}>
          <Eye className="h-3.5 w-3.5" />
        </Button>
      </TableCell>
    </TableRow>
  );
});