import { useState, useEffect } from 'react';
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
import { Eye, FileText, Filter, X, Image as ImageIcon } from 'lucide-react';
import { format } from 'date-fns';

const SB = { pending: 'bg-yellow-100 text-yellow-800', confirmed: 'bg-green-100 text-green-800', returned: 'bg-red-100 text-red-800' };

export default function TransactionHistoryPage() {
  const [deals, setDeals] = useState([]);
  const [filter, setFilter] = useState({ status: 'all', client: '', currency: '', date_from: '', date_to: '' });
  const [showFilters, setShowFilters] = useState(false);
  const [loading, setLoading] = useState(true);
  const [sel, setSel] = useState(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (filter.status !== 'all') params.append('status', filter.status);
        if (filter.client) params.append('client', filter.client);
        if (filter.currency) params.append('currency', filter.currency);
        if (filter.date_from) params.append('date_from', filter.date_from);
        if (filter.date_to) params.append('date_to', filter.date_to);
        const q = params.toString();
        const res = await api.get(`/deals${q ? '?' + q : ''}`);
        setDeals(res.data);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    })();
  }, [filter]);

  const clearFilters = () => setFilter({ status: 'all', client: '', currency: '', date_from: '', date_to: '' });
  const hasFilters = filter.status !== 'all' || filter.client || filter.currency || filter.date_from || filter.date_to;

  return (
    <div data-testid="transactions-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Transaction History</h1>
          <p className="text-sm text-slate-500 mt-1">All FX deal transactions</p>
        </div>
        <Button variant={showFilters ? 'default' : 'outline'} size="sm" onClick={() => setShowFilters(!showFilters)} className={showFilters ? 'bg-[#518dca]' : ''} data-testid="tx-toggle-filters">
          <Filter className="h-3.5 w-3.5 mr-1.5" /> Filters {hasFilters && <Badge className="ml-1.5 bg-[#ec474e] text-white text-[10px] px-1.5 py-0">Active</Badge>}
        </Button>
      </div>

      {showFilters && (
        <Card className="mb-6">
          <CardContent className="py-4">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              <div className="space-y-1"><Label className="text-xs">Status</Label>
                <Select value={filter.status} onValueChange={v => setFilter(p => ({ ...p, status: v }))}>
                  <SelectTrigger className="h-8 text-xs" data-testid="tx-filter-status"><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="all">All</SelectItem><SelectItem value="pending">Pending</SelectItem><SelectItem value="confirmed">Confirmed</SelectItem><SelectItem value="returned">Returned</SelectItem></SelectContent>
                </Select>
              </div>
              <div className="space-y-1"><Label className="text-xs">Client</Label><Input className="h-8 text-xs" placeholder="Search client..." value={filter.client} onChange={e => setFilter(p => ({ ...p, client: e.target.value }))} /></div>
              <div className="space-y-1"><Label className="text-xs">Currency</Label><Input className="h-8 text-xs" placeholder="e.g. USD" value={filter.currency} onChange={e => setFilter(p => ({ ...p, currency: e.target.value.toUpperCase() }))} /></div>
              <div className="space-y-1"><Label className="text-xs">Date From</Label><Input type="date" className="h-8 text-xs" value={filter.date_from} onChange={e => setFilter(p => ({ ...p, date_from: e.target.value }))} /></div>
              <div className="space-y-1"><Label className="text-xs">Date To</Label><Input type="date" className="h-8 text-xs" value={filter.date_to} onChange={e => setFilter(p => ({ ...p, date_to: e.target.value }))} /></div>
            </div>
            {hasFilters && <Button variant="ghost" size="sm" className="mt-3 text-xs text-slate-500" onClick={clearFilters}><X className="h-3 w-3 mr-1" /> Clear Filters</Button>}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          {loading ? <div className="flex items-center justify-center h-32"><div className="animate-spin h-6 w-6 border-4 border-[#518dca] border-t-transparent rounded-full" /></div>
          : deals.length === 0 ? <div className="text-center py-16"><FileText className="h-12 w-12 text-slate-300 mx-auto mb-3" /><p className="text-slate-500">No transactions found</p></div>
          : <Table>
              <TableHeader><TableRow className="bg-slate-50">
                <TableHead>Reference</TableHead><TableHead>Client</TableHead><TableHead>Trader</TableHead><TableHead>Type</TableHead><TableHead>Pair</TableHead><TableHead className="text-right">Amount</TableHead><TableHead className="text-right">Rate</TableHead><TableHead>Status</TableHead><TableHead>Created</TableHead><TableHead>Action</TableHead>
              </TableRow></TableHeader>
              <TableBody>{deals.map(d => (
                <TableRow key={d.id} data-testid={`tx-row-${d.id}`}>
                  <TableCell className="font-mono text-xs font-medium text-[#08263e]">{d.reference_number}</TableCell>
                  <TableCell className="text-sm">{d.client_name || '-'}</TableCell>
                  <TableCell className="text-sm">{d.created_by_name}</TableCell>
                  <TableCell className="text-sm">{d.transaction_type}</TableCell>
                  <TableCell className="font-mono text-xs">{d.buy_currency}/{d.sell_currency}</TableCell>
                  <TableCell className="text-right font-mono text-xs">{Number(d.amount).toLocaleString()}</TableCell>
                  <TableCell className="text-right font-mono text-xs">{d.rate}</TableCell>
                  <TableCell><Badge className={SB[d.status]}>{d.status}</Badge></TableCell>
                  <TableCell className="text-xs text-slate-500">{format(new Date(d.created_at), 'dd MMM yyyy')}</TableCell>
                  <TableCell><Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => setSel(d)} data-testid={`view-tx-${d.id}`}><Eye className="h-3.5 w-3.5" /></Button></TableCell>
                </TableRow>
              ))}</TableBody>
            </Table>}
        </CardContent>
      </Card>

      <Dialog open={!!sel} onOpenChange={o => !o && setSel(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="tx-detail-dialog">
          <DialogHeader><DialogTitle style={{ fontFamily: 'Chivo' }} className="text-[#08263e]">Deal Details - {sel?.reference_number}</DialogTitle></DialogHeader>
          {sel && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
                <Info label="Client" val={sel.client_name} />
                <Info label="Transaction Type" val={sel.transaction_type} />
                <Info label="Transfer Type" val={sel.transfer_type} />
                <Info label="Deal Date" val={format(new Date(sel.deal_date + 'T00:00:00'), 'dd MMM yyyy')} />
                <Info label="Value Date" val={format(new Date(sel.value_date + 'T00:00:00'), 'dd MMM yyyy')} />
                <Info label="Buy Currency" val={sel.buy_currency} />
                <Info label="Sell Currency" val={sel.sell_currency} />
                <Info label={`Currency Amount (${sel.buy_currency})`} val={Number(sel.currency_amount).toLocaleString()} mono />
                <Info label="Amount" val={Number(sel.amount).toLocaleString()} mono />
                <Info label="Rate" val={sel.rate} mono />
                <Info label="From" val={`${sel.from_company} / ${sel.from_bank} (${sel.from_account_num})`} />
                <Info label="To" val={`${sel.to_company} / ${sel.to_bank} (${sel.to_account_num})`} />
                <Info label="Created By" val={sel.created_by_name} />
                <Info label="Status" val={sel.status} />
                {sel.processed_by_name && <Info label="Processed By" val={sel.processed_by_name} />}
                {sel.processed_at && <Info label="Processed At" val={format(new Date(sel.processed_at), 'dd MMM yyyy HH:mm')} />}
              </div>
              {sel.remarks && (<><Separator /><div className="bg-slate-50 p-3 rounded-md"><p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Trader Remarks</p><p className="text-sm">{sel.remarks}</p></div></>)}
              {sel.treasury_remarks && (<div className="bg-blue-50 p-3 rounded-md"><p className="text-[10px] text-blue-400 uppercase tracking-wider mb-1">Treasury Remarks</p><p className="text-sm">{sel.treasury_remarks}</p></div>)}
              {sel.settlement_proofs?.length > 0 && (
                <><Separator /><div><p className="text-xs font-medium text-slate-600 uppercase tracking-wider mb-2">Settlement Proofs</p><div className="grid grid-cols-3 gap-2">{sel.settlement_proofs.map(p => (
                  <a key={p.id} href={`${process.env.REACT_APP_BACKEND_URL}/api/files/${p.path}`} target="_blank" rel="noopener noreferrer" className="block border rounded overflow-hidden hover:ring-2 ring-[#518dca]">
                    <img src={`${process.env.REACT_APP_BACKEND_URL}/api/files/${p.path}`} alt={p.filename} className="w-full h-20 object-cover" />
                    <p className="text-[10px] text-slate-500 p-1 truncate">{p.filename}</p>
                  </a>
                ))}</div></div></>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Info({ label, val, mono }) {
  return (<div><p className="text-[10px] text-slate-400 uppercase tracking-wider">{label}</p><p className={`text-sm font-medium ${mono ? 'font-mono' : ''}`}>{val || '-'}</p></div>);
}
