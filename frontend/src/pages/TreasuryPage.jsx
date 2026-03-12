import { useState, useEffect, useCallback } from 'react';
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
import { CheckCircle, XCircle, Eye, Filter, X, Image as ImageIcon } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';

const SB = {
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-green-100 text-green-800',
  returned: 'bg-red-100 text-red-800',
  cancelled: 'bg-slate-200 text-slate-600',
};

export default function TreasuryPage() {
  const [deals, setDeals] = useState([]);
  const [sel, setSel] = useState(null);
  const [remarks, setRemarks] = useState('');
  const [processing, setProcessing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('pending');
  const [showFilters, setShowFilters] = useState(false);
  const [filter, setFilter] = useState({ client: '', currency: '', date_from: '', date_to: '' });

  const load = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (filter.client) params.append('client', filter.client);
      if (filter.currency) params.append('currency', filter.currency);
      if (filter.date_from) params.append('date_from', filter.date_from);
      if (filter.date_to) params.append('date_to', filter.date_to);
      const q = params.toString();
      const r = await api.get(`/deals${q ? '?' + q : ''}`);
      setDeals(r.data);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const process = async (status) => {
    if (!sel) return;
    setProcessing(true);
    try {
      await api.put(`/deals/${sel.id}/process`, { status, treasury_remarks: remarks });
      toast.success(`Deal ${status === 'confirmed' ? 'confirmed' : 'returned'}`);
      setSel(null); setRemarks(''); load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed'); }
    finally { setProcessing(false); }
  };

  const clearFilters = () => setFilter({ client: '', currency: '', date_from: '', date_to: '' });
  const hasFilters = filter.client || filter.currency || filter.date_from || filter.date_to;
  const pending = deals.filter(d => d.status === 'pending');
  const done = deals.filter(d => d.status !== 'pending');

  const AccountInfo = ({ deal, prefix, label }) => {
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
  };

  const OursInfo = ({ deal }) => {
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
  };

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
                <Input className="h-8 text-xs" placeholder="Search client..." value={filter.client} onChange={e => setFilter(p => ({ ...p, client: e.target.value }))} data-testid="treas-filter-client" />
              </div>
              <div className="space-y-1"><Label className="text-xs">Currency</Label>
                <Input className="h-8 text-xs" placeholder="e.g. USD" value={filter.currency} onChange={e => setFilter(p => ({ ...p, currency: e.target.value.toUpperCase() }))} data-testid="treas-filter-currency" />
              </div>
              <div className="space-y-1"><Label className="text-xs">Date From</Label>
                <Input type="date" className="h-8 text-xs" value={filter.date_from} onChange={e => setFilter(p => ({ ...p, date_from: e.target.value }))} data-testid="treas-filter-date-from" />
              </div>
              <div className="space-y-1"><Label className="text-xs">Date To</Label>
                <Input type="date" className="h-8 text-xs" value={filter.date_to} onChange={e => setFilter(p => ({ ...p, date_to: e.target.value }))} data-testid="treas-filter-date-to" />
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
            {loading ? <div className="flex items-center justify-center h-32"><div className="animate-spin h-6 w-6 border-4 border-[#518dca] border-t-transparent rounded-full" /></div>
            : pending.length === 0 ? <p className="text-center py-16 text-slate-400">No pending deals</p>
            : <Table>
                <TableHeader><TableRow className="bg-slate-50">
                  <TableHead>Reference</TableHead><TableHead>Client</TableHead><TableHead>Trader</TableHead><TableHead>Type</TableHead><TableHead>Pair</TableHead><TableHead className="text-right">Amount</TableHead><TableHead className="text-right">Rate</TableHead><TableHead>Deal Date</TableHead><TableHead>Action</TableHead>
                </TableRow></TableHeader>
                <TableBody>{pending.map(d => (
                  <TableRow key={d.id} data-testid={`pending-deal-${d.id}`}>
                    <TableCell className="font-mono text-xs font-medium">{d.reference_number}</TableCell>
                    <TableCell className="text-sm">{d.client_name || '-'}</TableCell>
                    <TableCell className="text-sm">{d.created_by_name}</TableCell>
                    <TableCell className="text-sm">{d.transaction_type}</TableCell>
                    <TableCell className="font-mono text-xs">{d.buy_currency}/{d.sell_currency}</TableCell>
                    <TableCell className="text-right font-mono text-xs">{Number(d.amount).toLocaleString()}</TableCell>
                    <TableCell className="text-right font-mono text-xs">{d.rate}</TableCell>
                    <TableCell className="text-xs">{format(new Date(d.deal_date + 'T00:00:00'), 'dd MMM yyyy')}</TableCell>
                    <TableCell><Button size="sm" variant="outline" onClick={() => { setSel(d); setRemarks(''); }} data-testid={`review-deal-${d.id}`}><Eye className="h-3 w-3 mr-1" /> Review</Button></TableCell>
                  </TableRow>
                ))}</TableBody>
              </Table>}
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="processed" className="mt-4">
          <Card><CardContent className="p-0">
            {done.length === 0 ? <p className="text-center py-16 text-slate-400">No processed deals</p>
            : <Table>
                <TableHeader><TableRow className="bg-slate-50">
                  <TableHead>Reference</TableHead><TableHead>Client</TableHead><TableHead>Trader</TableHead><TableHead>Pair</TableHead><TableHead className="text-right">Amount</TableHead><TableHead>Status</TableHead><TableHead>Processed By</TableHead><TableHead>Processed At</TableHead>
                </TableRow></TableHeader>
                <TableBody>{done.map(d => (
                  <TableRow key={d.id}>
                    <TableCell className="font-mono text-xs">{d.reference_number}</TableCell>
                    <TableCell className="text-sm">{d.client_name || '-'}</TableCell>
                    <TableCell className="text-sm">{d.created_by_name}</TableCell>
                    <TableCell className="font-mono text-xs">{d.buy_currency}/{d.sell_currency}</TableCell>
                    <TableCell className="text-right font-mono text-xs">{Number(d.amount).toLocaleString()}</TableCell>
                    <TableCell><Badge className={SB[d.status]}>{d.status}</Badge></TableCell>
                    <TableCell className="text-sm">{d.processed_by_name || '-'}</TableCell>
                    <TableCell className="text-xs">{d.processed_at ? format(new Date(d.processed_at), 'dd MMM yyyy HH:mm') : '-'}</TableCell>
                  </TableRow>
                ))}</TableBody>
              </Table>}
          </CardContent></Card>
        </TabsContent>
      </Tabs>

      <Dialog open={!!sel} onOpenChange={o => !o && setSel(null)}>
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
                <AccountInfo deal={sel} prefix="from" label="From" />
                <AccountInfo deal={sel} prefix="to" label="To" />
                <Info label="Trader" val={sel.created_by_name} />
              </div>
              <OursInfo deal={sel} />
              {sel.remarks && (<div className="bg-slate-50 p-3 rounded-md"><p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Trader Remarks</p><p className="text-sm">{sel.remarks}</p></div>)}
              {sel.cancellation_reason && (<div className="bg-red-50 border border-red-200 p-3 rounded-md"><p className="text-[10px] text-red-400 uppercase tracking-wider mb-1">Cancellation Reason</p><p className="text-sm text-red-700">{sel.cancellation_reason}</p></div>)}

              {sel.settlement_proofs?.length > 0 && (
                <>
                  <Separator />
                  <div>
                    <p className="text-xs font-medium text-slate-600 uppercase tracking-wider mb-2">Settlement Proofs</p>
                    <div className="grid grid-cols-3 gap-2">
                      {sel.settlement_proofs.map(p => (
                        <a key={p.id} href={`${process.env.REACT_APP_BACKEND_URL}/api/files/${p.path}`} target="_blank" rel="noopener noreferrer" className="block border rounded overflow-hidden hover:ring-2 ring-[#518dca]">
                          <img src={`${process.env.REACT_APP_BACKEND_URL}/api/files/${p.path}`} alt={p.filename} className="w-full h-20 object-cover" />
                          <p className="text-[10px] text-slate-500 p-1 truncate">{p.filename}</p>
                        </a>
                      ))}
                    </div>
                  </div>
                </>
              )}

              {sel.status === 'pending' && (
                <>
                  <Separator />
                  <div className="space-y-1.5">
                    <Label className="text-xs">Treasury Remarks</Label>
                    <Textarea value={remarks} onChange={e => setRemarks(e.target.value)} placeholder="Add your remarks..." rows={3} data-testid="treasury-remarks-input" />
                  </div>
                </>
              )}
            </div>
          )}
          {sel?.status === 'pending' && (
            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={() => setSel(null)} data-testid="cancel-review-btn">Cancel</Button>
              <Button className="bg-[#ec474e] hover:bg-[#ec474e]/90 text-white" onClick={() => process('returned')} disabled={processing} data-testid="return-deal-btn"><XCircle className="h-4 w-4 mr-2" /> Return</Button>
              <Button className="bg-[#10b981] hover:bg-[#10b981]/90 text-white" onClick={() => process('confirmed')} disabled={processing} data-testid="confirm-deal-btn"><CheckCircle className="h-4 w-4 mr-2" /> Confirm</Button>
            </DialogFooter>
          )}
          {sel?.status !== 'pending' && (
            <DialogFooter>
              <Button variant="outline" onClick={() => setSel(null)}>Close</Button>
            </DialogFooter>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Info({ label, val, mono }) {
  return (<div><p className="text-[10px] text-slate-400 uppercase tracking-wider">{label}</p><p className={`text-sm font-medium ${mono ? 'font-mono' : ''}`}>{val || '-'}</p></div>);
}
