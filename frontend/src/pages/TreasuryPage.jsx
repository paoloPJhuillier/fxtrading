import { useState, useEffect, useCallback, useRef, memo, useMemo } from 'react';
import api from '@/lib/api';
import { useRefData } from '@/lib/refdata';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CheckCircle, XCircle, Eye, Filter, X, Image as ImageIcon, AlertTriangle, Upload, Trash2, ChevronLeft, ChevronRight, Settings2, Clock } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const SB = {
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-green-100 text-green-800',
  returned: 'bg-red-100 text-red-800',
  cancelled: 'bg-slate-200 text-slate-600',
};
const PAGE_SIZE = 20;

const DEFAULT_COLS = { reference: true, client: true, type: true, pair: true, amount: true, rate: true, from_bank: true, to_bank: true, deal_date: true, status: true, last_action: true };

export default function TreasuryPage() {
  const { data: ref } = useRefData();
  const banks = ref?.banks || [];
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
  const [showColConfig, setShowColConfig] = useState(false);
  const [cols, setCols] = useState(DEFAULT_COLS);
  const [filter, setFilter] = useState({ client: '', currency: '', date_from: '', date_to: '', from_bank: '', to_bank: '' });
  const [debouncedFilter, setDebouncedFilter] = useState(filter);
  const [confirmAction, setConfirmAction] = useState(null);
  const [uploading, setUploading] = useState(false);
  const clientFileRef = useRef(null);
  const processorFileRef = useRef(null);
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

  const clearFilters = () => { setFilter({ client: '', currency: '', date_from: '', date_to: '', from_bank: '', to_bank: '' }); setPage(1); };
  const hasFilters = filter.client || filter.currency || filter.date_from || filter.date_to || filter.from_bank || filter.to_bank;
  const updateFilter = (k, v) => { setFilter(p => ({ ...p, [k]: v })); setPage(1); };

  const uploadProof = async (e, proofType) => {
    if (!sel || !e.target.files?.length) return;
    setUploading(true);
    try {
      for (const file of e.target.files) {
        const fd = new FormData();
        fd.append('file', file);
        await api.post(`/deals/${sel.id}/upload?proof_type=${proofType}`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      }
      const res = await api.get(`/deals/${sel.id}`);
      _setSel(res.data);
      toast.success(`${proofType === 'client' ? "Client" : "Processor"} settlement proof uploaded`);
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

  // Filter deals by tab AND from_bank/to_bank
  const filterByBank = useCallback((deals) => {
    let result = deals;
    if (debouncedFilter.from_bank) result = result.filter(d => d.from_bank === debouncedFilter.from_bank);
    if (debouncedFilter.to_bank) result = result.filter(d => d.to_bank === debouncedFilter.to_bank);
    return result;
  }, [debouncedFilter.from_bank, debouncedFilter.to_bank]);

  const pending = useMemo(() => filterByBank(data.deals.filter(d => d.status === 'pending')), [data.deals, filterByBank]);
  const returned = useMemo(() => filterByBank(data.deals.filter(d => d.status === 'returned')), [data.deals, filterByBank]);
  const done = useMemo(() => filterByBank(data.deals.filter(d => d.status === 'confirmed' || d.status === 'cancelled')), [data.deals, filterByBank]);

  const openReview = useCallback(async (d) => {
    _setSel(d); setRemarks('');
    try { const r = await api.get(`/deals/${d.id}`); _setSel(r.data); } catch (e) { console.error(e); }
  }, []);
  const toggleCol = useCallback((key) => { setCols(p => ({ ...p, [key]: !p[key] })); }, []);

  const clientProofs = sel?.settlement_proofs?.filter(p => p.proof_type !== 'processor') || [];
  const processorProofs = sel?.settlement_proofs?.filter(p => p.proof_type === 'processor') || [];

  return (
    <div data-testid="treasury-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Deal Queue</h1>
          <p className="text-sm text-slate-500 mt-1">Review and process FX deal tickets</p>
        </div>
        <div className="flex gap-2">
          <Button variant={showColConfig ? 'default' : 'outline'} size="sm" onClick={() => setShowColConfig(!showColConfig)} className={showColConfig ? 'bg-[#08263e]' : ''} data-testid="col-config-btn">
            <Settings2 className="h-3.5 w-3.5 mr-1.5" /> Columns
          </Button>
          <Button variant={showFilters ? 'default' : 'outline'} size="sm" onClick={() => setShowFilters(!showFilters)} data-testid="toggle-filters-btn" className={showFilters ? 'bg-[#518dca]' : ''}>
            <Filter className="h-3.5 w-3.5 mr-1.5" /> Filters {hasFilters && <Badge className="ml-1.5 bg-[#ec474e] text-white text-[10px] px-1.5 py-0">Active</Badge>}
          </Button>
        </div>
      </div>

      {showColConfig && (
        <Card className="mb-4" data-testid="col-config-panel">
          <CardContent className="py-3">
            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-3">Visible Columns</p>
            <div className="flex flex-wrap gap-4">
              {[
                ['reference', 'Reference'], ['client', 'Client'], ['type', 'Type'], ['pair', 'Pair'],
                ['amount', 'Amount'], ['rate', 'Rate'], ['from_bank', 'From Bank'], ['to_bank', 'To Bank'],
                ['deal_date', 'Deal Date'], ['status', 'Status'], ['last_action', 'Last Action'],
              ].map(([key, label]) => (
                <div key={key} className="flex items-center gap-2">
                  <Switch checked={cols[key]} onCheckedChange={() => toggleCol(key)} id={`col-${key}`} data-testid={`col-toggle-${key}`} />
                  <Label htmlFor={`col-${key}`} className="text-xs cursor-pointer">{label}</Label>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {showFilters && (
        <Card className="mb-6" data-testid="treasury-filters-panel">
          <CardContent className="py-4">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <div className="space-y-1"><Label className="text-xs">Client</Label>
                <Input className="h-8 text-xs" placeholder="Search client..." value={filter.client} onChange={e => updateFilter('client', e.target.value)} data-testid="treas-filter-client" />
              </div>
              <div className="space-y-1"><Label className="text-xs">Currency</Label>
                <Input className="h-8 text-xs" placeholder="e.g. USD" value={filter.currency} onChange={e => updateFilter('currency', e.target.value.toUpperCase())} data-testid="treas-filter-currency" />
              </div>
              <div className="space-y-1"><Label className="text-xs">From Bank</Label>
                <Select value={filter.from_bank || '_all'} onValueChange={v => updateFilter('from_bank', v === '_all' ? '' : v)}>
                  <SelectTrigger className="h-8 text-xs" data-testid="treas-filter-from-bank"><SelectValue placeholder="All" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="_all">All Banks</SelectItem>
                    {banks.map(b => <SelectItem key={b.id} value={b.name}>{b.name}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1"><Label className="text-xs">To Bank</Label>
                <Select value={filter.to_bank || '_all'} onValueChange={v => updateFilter('to_bank', v === '_all' ? '' : v)}>
                  <SelectTrigger className="h-8 text-xs" data-testid="treas-filter-to-bank"><SelectValue placeholder="All" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="_all">All Banks</SelectItem>
                    {banks.map(b => <SelectItem key={b.id} value={b.name}>{b.name}</SelectItem>)}
                  </SelectContent>
                </Select>
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
          <TabsTrigger value="returned" data-testid="returned-tab">Returned ({returned.length})</TabsTrigger>
          <TabsTrigger value="processed" data-testid="processed-tab">Processed ({done.length})</TabsTrigger>
        </TabsList>

        {['pending', 'returned', 'processed'].map(tabKey => {
          const list = tabKey === 'pending' ? pending : tabKey === 'returned' ? returned : done;
          const showReviewActions = tabKey === 'pending';
          return (
            <TabsContent key={tabKey} value={tabKey} className="mt-4">
              <Card><CardContent className="p-0">
                {loading && list.length === 0 ? <div className="flex items-center justify-center h-32"><div className="animate-spin h-6 w-6 border-4 border-[#518dca] border-t-transparent rounded-full" /></div>
                : list.length === 0 ? <p className="text-center py-16 text-slate-400">No deals</p> :
                <div className={loading ? 'opacity-60 pointer-events-none transition-opacity' : 'transition-opacity'}>
                <Table>
                  <TableHeader><TableRow className="bg-slate-50">
                    {cols.reference && <TableHead>Reference</TableHead>}
                    {cols.client && <TableHead>Client</TableHead>}
                    {cols.type && <TableHead>Type</TableHead>}
                    {cols.pair && <TableHead>Pair</TableHead>}
                    {cols.amount && <TableHead className="text-right">Amount</TableHead>}
                    {cols.rate && <TableHead className="text-right">Rate</TableHead>}
                    {cols.from_bank && <TableHead>From Bank</TableHead>}
                    {cols.to_bank && <TableHead>To Bank</TableHead>}
                    {cols.deal_date && <TableHead>Deal Date</TableHead>}
                    {cols.status && tabKey !== 'pending' && <TableHead>Status</TableHead>}
                    {cols.last_action && <TableHead>Last Action</TableHead>}
                    <TableHead>Action</TableHead>
                  </TableRow></TableHeader>
                  <TableBody>{list.map(d => (
                    <TreasuryRow key={d.id} deal={d} cols={cols} showStatus={tabKey !== 'pending'} onReview={openReview} />
                  ))}</TableBody>
                </Table>
                </div>}
              </CardContent></Card>
            </TabsContent>
          );
        })}
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
              {sel.treasury_remarks && (<div className="bg-blue-50 p-3 rounded-md"><p className="text-[10px] text-blue-400 uppercase tracking-wider mb-1">Treasury Remarks</p><p className="text-sm">{sel.treasury_remarks}</p></div>)}

              <Separator />
              {/* Client's Settlement Proofs - View only for Treasury (Item 1: Trader-only upload) */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs font-medium text-slate-600 uppercase tracking-wider">Client's Settlement</p>
                </div>
                {clientProofs.length > 0 ? (
                  <ProofGrid proofs={clientProofs} onDelete={deleteProof} />
                ) : (
                  <div className="text-center py-4 border border-dashed rounded-lg">
                    <ImageIcon className="h-6 w-6 text-slate-300 mx-auto mb-1" />
                    <p className="text-[10px] text-slate-400">No client settlement proofs</p>
                  </div>
                )}
              </div>

              {/* Processor's Settlement Proofs */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs font-medium text-slate-600 uppercase tracking-wider">Processor's Settlement</p>
                  <div>
                    <input type="file" ref={processorFileRef} className="hidden" accept="image/*,.pdf" multiple onChange={e => uploadProof(e, 'processor')} />
                    <Button size="sm" variant="outline" onClick={() => processorFileRef.current?.click()} disabled={uploading} data-testid="upload-processor-proof-btn">
                      <Upload className="h-3 w-3 mr-1.5" /> {uploading ? 'Uploading...' : 'Upload'}
                    </Button>
                  </div>
                </div>
                {processorProofs.length > 0 ? (
                  <ProofGrid proofs={processorProofs} onDelete={deleteProof} />
                ) : (
                  <div className="text-center py-4 border border-dashed rounded-lg">
                    <ImageIcon className="h-6 w-6 text-slate-300 mx-auto mb-1" />
                    <p className="text-[10px] text-slate-400">No processor settlement proofs</p>
                  </div>
                )}
              </div>

              {/* Deal History */}
              {sel.history?.length > 0 && (
                <>
                  <Separator />
                  <DealHistory history={sel.history} />
                </>
              )}

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
              {(clientProofs.length + processorProofs.length) === 0 && (
                <p className="text-[10px] text-amber-600 mr-auto self-center">Settlement proofs required to confirm</p>
              )}
              <Button variant="outline" onClick={() => _setSel(null)} data-testid="cancel-review-btn">Cancel</Button>
              <Button className="bg-[#ec474e] hover:bg-[#ec474e]/90 text-white" onClick={() => tryProcess('returned')} disabled={processing} data-testid="return-deal-btn"><XCircle className="h-4 w-4 mr-2" /> Return</Button>
              <Button className="bg-[#10b981] hover:bg-[#10b981]/90 text-white" onClick={() => tryProcess('confirmed')} disabled={processing || (clientProofs.length + processorProofs.length) === 0} data-testid="confirm-deal-btn"><CheckCircle className="h-4 w-4 mr-2" /> Confirm</Button>
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

function ProofGrid({ proofs, onDelete }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
      {proofs.map(p => (
        <div key={p.id} className="relative group border rounded-lg overflow-hidden">
          <img src={`${BACKEND_URL}/api/files/${p.path}`} alt={p.filename} className="w-full h-28 object-cover" loading="lazy" decoding="async" />
          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
            <a href={`${BACKEND_URL}/api/files/${p.path}`} target="_blank" rel="noopener noreferrer" className="text-white"><Eye className="h-4 w-4" /></a>
            <button onClick={() => onDelete(p.id)} className="text-white hover:text-red-300"><Trash2 className="h-4 w-4" /></button>
          </div>
          <p className="text-[10px] text-slate-500 p-1.5 truncate">{p.filename}</p>
        </div>
      ))}
    </div>
  );
}

function DealHistory({ history }) {
  return (
    <div data-testid="deal-history">
      <p className="text-xs font-medium text-slate-600 uppercase tracking-wider mb-3">Deal History</p>
      <div className="space-y-3">
        {[...history].reverse().map(h => (
          <div key={h.id} className="flex gap-3 items-start">
            <div className="flex-shrink-0 mt-0.5">
              <Clock className="h-3.5 w-3.5 text-slate-400" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge className={`${HISTORY_COLORS[h.action] || 'bg-slate-100 text-slate-600'} text-[10px] px-1.5 py-0`}>{h.action.replace(/_/g, ' ')}</Badge>
                <span className="text-[11px] text-slate-500">{h.user_name} ({h.user_role})</span>
                <span className="text-[10px] text-slate-400">{format(new Date(h.timestamp), 'dd MMM yyyy HH:mm')}</span>
              </div>
              {h.remarks && <p className="text-xs text-slate-600 mt-1">{h.remarks}</p>}
              {h.changes?.length > 0 && (
                <div className="mt-1 space-y-0.5">
                  {h.changes.map((c, i) => (
                    <p key={i} className="text-[11px] text-slate-500">
                      <span className="font-medium">{c.field}:</span> <span className="line-through text-red-400">{c.old_value || '(empty)'}</span> <span className="text-green-600">{c.new_value}</span>
                    </p>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const HISTORY_COLORS = {
  created: 'bg-blue-100 text-blue-700',
  deal_confirmed: 'bg-green-100 text-green-700',
  deal_returned: 'bg-red-100 text-red-700',
  deal_cancelled: 'bg-slate-200 text-slate-600',
  deal_resubmitted: 'bg-purple-100 text-purple-700',
  deal_edited: 'bg-amber-100 text-amber-700',
  proof_uploaded: 'bg-cyan-100 text-cyan-700',
};

const TreasuryRow = memo(function TreasuryRow({ deal, cols, showStatus, onReview }) {
  const lastAction = deal.history?.length > 0 ? deal.history[deal.history.length - 1] : null;
  return (
    <TableRow data-testid={`deal-row-${deal.id}`}>
      {cols.reference && <TableCell className="font-mono text-xs font-medium">{deal.reference_number}</TableCell>}
      {cols.client && <TableCell className="text-sm">{deal.client_name || '-'}</TableCell>}
      {cols.type && <TableCell className="text-sm">{deal.transaction_type}</TableCell>}
      {cols.pair && <TableCell className="font-mono text-xs">{deal.buy_currency}/{deal.sell_currency}</TableCell>}
      {cols.amount && <TableCell className="text-right font-mono text-xs">{Number(deal.currency_amount).toLocaleString()} <span className="text-slate-400">{deal.buy_currency}</span></TableCell>}
      {cols.rate && <TableCell className="text-right font-mono text-xs">{deal.rate}</TableCell>}
      {cols.from_bank && <TableCell className="text-xs">{deal.from_bank || '-'}</TableCell>}
      {cols.to_bank && <TableCell className="text-xs">{deal.to_bank || '-'}</TableCell>}
      {cols.deal_date && <TableCell className="text-xs">{format(new Date(deal.deal_date + 'T00:00:00'), 'dd MMM yyyy')}</TableCell>}
      {cols.status && showStatus && <TableCell><Badge className={SB[deal.status]}>{deal.status}</Badge></TableCell>}
      {cols.last_action && <TableCell className="text-[10px] text-slate-500 max-w-[120px]">
        {lastAction ? (
          <span title={lastAction.remarks || lastAction.action.replace(/_/g, ' ')}>
            <Badge className={`${HISTORY_COLORS[lastAction.action] || 'bg-slate-100 text-slate-600'} text-[9px] px-1 py-0`}>
              {lastAction.action.replace(/^deal_/, '').replace(/_/g, ' ')}
            </Badge>
          </span>
        ) : '-'}
      </TableCell>}
      <TableCell>
        <Button size="sm" variant="outline" onClick={() => onReview(deal)} data-testid={`review-deal-${deal.id}`}>
          <Eye className="h-3 w-3 mr-1" /> {deal.status === 'pending' ? 'Review' : 'View'}
        </Button>
      </TableCell>
    </TableRow>
  );
});
