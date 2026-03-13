import { useState, useEffect, useCallback, useRef, memo, useMemo } from 'react';
import api from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CheckCircle, XCircle, Eye, Filter, X, Image as ImageIcon, AlertTriangle, Upload, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
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

export default function TreasuryPage() {
  const [data, setData] = useState({ deals: [], total: 0, page: 1, pages: 1 });
  const [_sel, _setSel] = useState(null);
  const selRef = useRef(null);
  if (_sel) selRef.current = _sel;
  const sel = _sel || selRef.current;
  const [remarks, setRemarks] = useState('');
  const [processing, setProcessing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('pending');
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [filter, setFilter] = useState({ client: '', currency: '', date_from: '', date_to: '' });
  const [debouncedFilter, setDebouncedFilter] = useState(filter);
  const [confirmAction, setConfirmAction] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef(null);
  const hasLoaded = useRef(false);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedFilter(filter), 250);
    return () => clearTimeout(t);
  }, [filter]);

  const load = useCallback(async (signal) => {
    if (!hasLoaded.current) setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', page);
      params.append('limit', PAGE_SIZE);
      if (debouncedFilter.client) params.append('client', debouncedFilter.client);
      if (debouncedFilter.currency) params.append('currency', debouncedFilter.currency);
      if (debouncedFilter.date_from) params.append('date_from', debouncedFilter.date_from);
      if (debouncedFilter.date_to) params.append('date_to', debouncedFilter.date_to);
      const r = await api.get(`/deals?${params.toString()}`, { signal });
      setData(r.data);
      hasLoaded.current = true;
    } catch (e) { if (!signal?.aborted) console.error(e); }
    finally { if (!signal?.aborted) setLoading(false); }
  }, [debouncedFilter, page]);

  useEffect(() => {
    const c = new AbortController();
    load(c.signal);
    return () => c.abort();
  }, [load]);

  const tryProcess = (status) => {
    if (!remarks.trim()) { toast.error('Treasury remarks are required'); return; }
    setConfirmAction(status);
  };

  const process = async () => {
    if (!sel || !confirmAction) return;
    setProcessing(true);
    try {
      await api.put(`/deals/${sel.id}/process`, { status: confirmAction, treasury_remarks: remarks });
      toast.success(`Deal ${confirmAction === 'confirmed' ? 'confirmed' : 'returned'}`);
      setConfirmAction(null); _setSel(null); setRemarks(''); load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
    finally { setProcessing(false); setConfirmAction(null); }
  };

  const clearFilters = () => { setFilter({ client: '', currency: '', date_from: '', date_to: '' }); setPage(1); };
  const hasFilters = filter.client || filter.currency || filter.date_from || filter.date_to;
  const updateFilter = (k, v) => { setFilter(p => ({ ...p, [k]: v })); setPage(1); };

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
      toast.success('Settlement proof uploaded');
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

  const pending = useMemo(() => data.deals.filter(d => d.status === 'pending'), [data.deals]);
  const done = useMemo(() => data.deals.filter(d => d.status !== 'pending'), [data.deals]);

  const openReview = useCallback((d) => { _setSel(d); setRemarks(''); }, []);

  return (
    <div data-testid="treasury-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Deal Queue</h1>
          <p className="text-sm text-slate-500 mt-1">Review and process FX deal tickets</p>
        </div>
        <Button variant={showFilters ? 'default' : 'outline'} size="sm" onClick={() => setShowFilters(!showFilters)} data-testid="toggle-filters-btn" className={showFilters ? 'bg-[#518dca]' : ''}>
          <Filter className="h-3.5 w-3.5 mr-1.5" /> Filters {hasFilters && <Badge className="ml-1.5 bg-[#ec474e] text-white text-[10px] px-1.5 py-0">Active</Badge>}
        </Button>
      </div>

      {showFilters && (
        <Card className="mb-6" data-testid="treasury-filters-panel">
          <CardContent className="py-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="space-y-1"><Label className="text-xs">Client</Label>
                <Input className="h-8 text-xs" placeholder="Search client..." value={filter.client} onChange={e => updateFilter('client', e.target.value)} data-testid="treas-filter-client" />
              </div>
              <div className="space-y-1"><Label className="text-xs">Currency</Label>
                <Input className="h-8 text-xs" placeholder="e.g. USD" value={filter.currency} onChange={e => updateFilter('currency', e.target.value.toUpperCase())} data-testid="treas-filter-currency" />
              </div>
              <div className="space-y-1"><Label className="text-xs">Date From</Label>
                <Input type="date" className="h-8 text-xs" value={filter.date_from} onChange={e => updateFilter('date_from', e.target.value)} data-testid="treas-filter-date-from" />
              </div>
              <div className="space-y-1"><Label className="text-xs">Date To</Label>
                <Input type="date" className="h-8 text-xs" value={filter.date_to} onChange={e => updateFilter('date_to', e.target.value)} data-testid="treas-filter-date-to" />
              </div>
            </div>
            {hasFilters && <Button variant="ghost" size="sm" className="mt-3 text-xs text-slate-500" onClick={clearFilters} data-testid="treas-clear-filters"><X className="h-3 w-3 mr-1" /> Clear Filters</Button>}
          </CardContent>
        </Card>
      )}

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList data-testid="treasury-tabs">
          <TabsTrigger value="pending" data-testid="pending-tab">Pending ({pending.length})</TabsTrigger>
          <TabsTrigger value="processed" data-testid="processed-tab">Processed ({done.length})</TabsTrigger>
        </TabsList>
        <TabsContent value="pending" className="mt-4">
          <Card><CardContent className="p-0">
            {loading && pending.length === 0 ? <div className="flex items-center justify-center h-32"><div className="animate-spin h-6 w-6 border-4 border-[#518dca] border-t-transparent rounded-full" /></div>
            : pending.length === 0 ? <p className="text-center py-16 text-slate-400">No deals</p> :
            <div className={loading ? 'opacity-60 pointer-events-none transition-opacity' : 'transition-opacity'}>
            <Table>
              <TableHeader><TableRow className="bg-slate-50">
                <TableHead>Reference</TableHead><TableHead>Client</TableHead><TableHead>Trader</TableHead>
                <TableHead>Type</TableHead><TableHead>Pair</TableHead><TableHead className="text-right">Amount</TableHead>
                <TableHead className="text-right">Rate</TableHead><TableHead>Deal Date</TableHead>
                <TableHead>Action</TableHead>
              </TableRow></TableHeader>
              <TableBody>{pending.map(d => (
                <TreasuryRow key={d.id} deal={d} showActions onReview={openReview} />
              ))}</TableBody>
            </Table>
            </div>}
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="processed" className="mt-4">
          <Card><CardContent className="p-0">
            {done.length === 0 ? <p className="text-center py-16 text-slate-400">No deals</p> :
            <div className={loading ? 'opacity-60 pointer-events-none transition-opacity' : 'transition-opacity'}>
            <Table>
              <TableHeader><TableRow className="bg-slate-50">
                <TableHead>Reference</TableHead><TableHead>Client</TableHead><TableHead>Trader</TableHead>
                <TableHead>Type</TableHead><TableHead>Pair</TableHead><TableHead className="text-right">Amount</TableHead>
                <TableHead className="text-right">Rate</TableHead><TableHead>Deal Date</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Action</TableHead>
              </TableRow></TableHeader>
              <TableBody>{done.map(d => (
                <TreasuryRow key={d.id} deal={d} showActions={false} onReview={openReview} />
              ))}</TableBody>
            </Table>
            </div>}
          </CardContent></Card>
        </TabsContent>
      </Tabs>

      {data.pages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-xs text-slate-400">Page {data.page} of {data.pages} ({data.total} deals)</p>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" disabled={page <= 1} onClick={() => setPage(p => p - 1)} data-testid="treasury-prev-page">
              <ChevronLeft className="h-3.5 w-3.5 mr-1" /> Previous
            </Button>
            <Button size="sm" variant="outline" disabled={page >= data.pages} onClick={() => setPage(p => p + 1)} data-testid="treasury-next-page">
              Next <ChevronRight className="h-3.5 w-3.5 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Review Deal Dialog */}
      {(!!_sel || !!sel) && !confirmAction && (
      <Dialog open={!!_sel && !confirmAction} onOpenChange={o => !o && _setSel(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="process-deal-dialog">
          <DialogHeader><DialogTitle style={{ fontFamily: 'Chivo' }} className="text-[#08263e]">Review Deal - {sel?.reference_number}</DialogTitle></DialogHeader>
          {sel && (
            <div className="space-y-4">
              <Badge className={SB[sel.status] + ' text-xs'}>{sel.status}</Badge>
              <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
                <Info label="Client" val={sel.client_name} />
                <Info label="Transaction Type" val={sel.transaction_type} />
                <Info label="Transfer Type" val={sel.transfer_type} />
                <Info label="Buy Currency" val={sel.buy_currency} />
                <Info label="Sell Currency" val={sel.sell_currency} />
                <Info label={`Currency Amount (${sel.buy_currency})`} val={Number(sel.currency_amount).toLocaleString()} mono />
                <Info label="Amount" val={Number(sel.amount).toLocaleString()} mono />
                <Info label="Rate" val={sel.rate} mono />
                <Info label="Deal Date" val={format(new Date(sel.deal_date + 'T00:00:00'), 'dd MMM yyyy')} />
                <Info label="Value Date" val={format(new Date(sel.value_date + 'T00:00:00'), 'dd MMM yyyy')} />
                <AcctInfo deal={sel} prefix="from" label="From" />
                <AcctInfo deal={sel} prefix="to" label="To" />
                <Info label="Trader" val={sel.created_by_name} />
              </div>
              <OursInfo deal={sel} />
              {sel.remarks && (<div className="bg-slate-50 p-3 rounded-md"><p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Trader Remarks</p><p className="text-sm">{sel.remarks}</p></div>)}
              {sel.cancellation_reason && (<div className="bg-red-50 border border-red-200 p-3 rounded-md"><p className="text-[10px] text-red-400 uppercase tracking-wider mb-1">Cancellation Reason</p><p className="text-sm text-red-700">{sel.cancellation_reason}</p></div>)}

              <Separator />
              <div>
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs font-medium text-slate-600 uppercase tracking-wider">Settlement Proofs</p>
                  <div>
                    <input type="file" ref={fileRef} className="hidden" accept="image/*" multiple onChange={uploadProof} />
                    <Button size="sm" variant="outline" onClick={() => fileRef.current?.click()} disabled={uploading} data-testid="upload-proof-btn">
                      <Upload className="h-3 w-3 mr-1.5" /> {uploading ? 'Uploading...' : 'Upload Image'}
                    </Button>
                  </div>
                </div>
                {sel.settlement_proofs?.length > 0 ? (
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {sel.settlement_proofs.map(p => (
                      <div key={p.id} className="relative group border rounded-lg overflow-hidden">
                        <img src={`${BACKEND_URL}/api/files/${p.path}`} alt={p.filename} className="w-full h-28 object-cover" loading="lazy" decoding="async" />
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                          <a href={`${BACKEND_URL}/api/files/${p.path}`} target="_blank" rel="noopener noreferrer" className="text-white"><Eye className="h-4 w-4" /></a>
                          <button onClick={() => deleteProof(p.id)} className="text-white hover:text-red-300"><Trash2 className="h-4 w-4" /></button>
                        </div>
                        <p className="text-[10px] text-slate-500 p-1.5 truncate">{p.filename}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6 border border-dashed rounded-lg">
                    <ImageIcon className="h-8 w-8 text-slate-300 mx-auto mb-2" />
                    <p className="text-xs text-slate-400">No settlement proofs uploaded yet</p>
                  </div>
                )}
              </div>

              {sel.status === 'pending' && (
                <>
                  <Separator />
                  <div className="space-y-1.5">
                    <Label className="text-xs">Treasury Remarks <span className="text-red-500">*</span></Label>
                    <Textarea value={remarks} onChange={e => setRemarks(e.target.value)} placeholder="Add your remarks (required)..." rows={3} data-testid="treasury-remarks-input" />
                  </div>
                </>
              )}
            </div>
          )}
          {sel?.status === 'pending' && (
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => _setSel(null)} data-testid="cancel-review-btn">Cancel</Button>
              <Button className="bg-[#ec474e] hover:bg-[#ec474e]/90 text-white" onClick={() => tryProcess('returned')} disabled={processing} data-testid="return-deal-btn"><XCircle className="h-4 w-4 mr-2" /> Return</Button>
              <Button className="bg-[#10b981] hover:bg-[#10b981]/90 text-white" onClick={() => tryProcess('confirmed')} disabled={processing} data-testid="confirm-deal-btn"><CheckCircle className="h-4 w-4 mr-2" /> Confirm</Button>
            </DialogFooter>
          )}
          {sel?.status !== 'pending' && (
            <DialogFooter><Button variant="outline" onClick={() => _setSel(null)}>Close</Button></DialogFooter>
          )}
        </DialogContent>
      </Dialog>
      )}

      {/* Confirmation Prompt */}
      {!!confirmAction && (
      <Dialog open={!!confirmAction} onOpenChange={o => { if (!o) setConfirmAction(null); }}>
        <DialogContent className="max-w-sm" data-testid="confirm-process-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Chivo' }}>
              <AlertTriangle className="h-5 w-5 text-[#f59e0b]" />
              {confirmAction === 'confirmed' ? 'Confirm Deal' : 'Return Deal'}
            </DialogTitle>
          </DialogHeader>
          <p className="text-sm text-slate-500">
            Are you sure you want to <strong>{confirmAction === 'confirmed' ? 'confirm' : 'return'}</strong> deal <span className="font-mono font-medium">{sel?.reference_number}</span>?
          </p>
          <div className="bg-slate-50 p-3 rounded-md">
            <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Your Remarks</p>
            <p className="text-sm">{remarks}</p>
          </div>
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setConfirmAction(null)} data-testid="confirm-process-back-btn">Go Back</Button>
            <Button
              className={confirmAction === 'confirmed' ? 'bg-[#10b981] hover:bg-[#10b981]/90 text-white' : 'bg-[#ec474e] hover:bg-[#ec474e]/90 text-white'}
              onClick={process} disabled={processing}
              data-testid="confirm-process-submit-btn"
            >
              {processing ? 'Processing...' : confirmAction === 'confirmed' ? 'Yes, Confirm' : 'Yes, Return'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      )}
    </div>
  );
}

function Info({ label, val, mono }) {
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

const TreasuryRow = memo(function TreasuryRow({ deal, showActions, onReview }) {
  return (
    <TableRow data-testid={`${showActions ? 'pending' : 'processed'}-deal-${deal.id}`}>
      <TableCell className="font-mono text-xs font-medium">{deal.reference_number}</TableCell>
      <TableCell className="text-sm">{deal.client_name || '-'}</TableCell>
      <TableCell className="text-sm">{deal.created_by_name}</TableCell>
      <TableCell className="text-sm">{deal.transaction_type}</TableCell>
      <TableCell className="font-mono text-xs">{deal.buy_currency}/{deal.sell_currency}</TableCell>
      <TableCell className="text-right font-mono text-xs">{Number(deal.amount).toLocaleString()}</TableCell>
      <TableCell className="text-right font-mono text-xs">{deal.rate}</TableCell>
      <TableCell className="text-xs">{format(new Date(deal.deal_date + 'T00:00:00'), 'dd MMM yyyy')}</TableCell>
      {!showActions && <TableCell><Badge className={SB[deal.status]}>{deal.status}</Badge></TableCell>}
      <TableCell>
        <Button size="sm" variant="outline" onClick={() => onReview(deal)} data-testid={`review-deal-${deal.id}`}>
          <Eye className="h-3 w-3 mr-1" /> {showActions ? 'Review' : 'View'}
        </Button>
      </TableCell>
    </TableRow>
  );
});