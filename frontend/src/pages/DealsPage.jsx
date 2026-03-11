import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
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
import { Plus, FileText, Eye, Filter, X, Upload, Trash2, Image as ImageIcon } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';

const SB = { pending: 'bg-yellow-100 text-yellow-800', confirmed: 'bg-green-100 text-green-800', returned: 'bg-red-100 text-red-800' };

export default function DealsPage() {
  const [deals, setDeals] = useState([]);
  const [filter, setFilter] = useState({ status: 'all', client: '', currency: '', date_from: '', date_to: '' });
  const [showFilters, setShowFilters] = useState(false);
  const [loading, setLoading] = useState(true);
  const [sel, setSel] = useState(null);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef(null);
  const navigate = useNavigate();

  const fetchDeals = useCallback(async () => {
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
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, [filter]);

  useEffect(() => { fetchDeals(); }, [fetchDeals]);

  const clearFilters = () => setFilter({ status: 'all', client: '', currency: '', date_from: '', date_to: '' });
  const hasFilters = filter.status !== 'all' || filter.client || filter.currency || filter.date_from || filter.date_to;

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
      setSel(res.data);
      toast.success('Settlement proof uploaded');
    } catch (err) { toast.error(err.response?.data?.detail || 'Upload failed'); }
    finally { setUploading(false); e.target.value = ''; }
  };

  const deleteProof = async (proofId) => {
    if (!sel) return;
    try {
      await api.delete(`/deals/${sel.id}/proofs/${proofId}`);
      const res = await api.get(`/deals/${sel.id}`);
      setSel(res.data);
      toast.success('Proof removed');
    } catch (err) { toast.error('Delete failed'); }
  };

  return (
    <div data-testid="deals-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo' }}>My Deals</h1>
          <p className="text-sm text-slate-500 mt-1">{deals.length} deal{deals.length !== 1 ? 's' : ''}</p>
        </div>
        <div className="flex gap-2">
          <Button variant={showFilters ? 'default' : 'outline'} size="sm" onClick={() => setShowFilters(!showFilters)} data-testid="toggle-filters-btn" className={showFilters ? 'bg-[#518dca]' : ''}>
            <Filter className="h-3.5 w-3.5 mr-1.5" /> Filters {hasFilters && <Badge className="ml-1.5 bg-[#ec474e] text-white text-[10px] px-1.5 py-0">Active</Badge>}
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
                <Select value={filter.status} onValueChange={v => setFilter(p => ({ ...p, status: v }))}>
                  <SelectTrigger className="h-8 text-xs" data-testid="filter-status"><SelectValue /></SelectTrigger>
                  <SelectContent><SelectItem value="all">All</SelectItem><SelectItem value="pending">Pending</SelectItem><SelectItem value="confirmed">Confirmed</SelectItem><SelectItem value="returned">Returned</SelectItem></SelectContent>
                </Select>
              </div>
              <div className="space-y-1"><Label className="text-xs">Client</Label>
                <Input className="h-8 text-xs" placeholder="Search client..." value={filter.client} onChange={e => setFilter(p => ({ ...p, client: e.target.value }))} data-testid="filter-client" />
              </div>
              <div className="space-y-1"><Label className="text-xs">Currency</Label>
                <Input className="h-8 text-xs" placeholder="e.g. USD" value={filter.currency} onChange={e => setFilter(p => ({ ...p, currency: e.target.value.toUpperCase() }))} data-testid="filter-currency" />
              </div>
              <div className="space-y-1"><Label className="text-xs">Date From</Label>
                <Input type="date" className="h-8 text-xs" value={filter.date_from} onChange={e => setFilter(p => ({ ...p, date_from: e.target.value }))} data-testid="filter-date-from" />
              </div>
              <div className="space-y-1"><Label className="text-xs">Date To</Label>
                <Input type="date" className="h-8 text-xs" value={filter.date_to} onChange={e => setFilter(p => ({ ...p, date_to: e.target.value }))} data-testid="filter-date-to" />
              </div>
            </div>
            {hasFilters && <Button variant="ghost" size="sm" className="mt-3 text-xs text-slate-500" onClick={clearFilters} data-testid="clear-filters-btn"><X className="h-3 w-3 mr-1" /> Clear Filters</Button>}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-32"><div className="animate-spin h-6 w-6 border-4 border-[#518dca] border-t-transparent rounded-full" /></div>
          ) : deals.length === 0 ? (
            <div className="text-center py-16">
              <FileText className="h-12 w-12 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500">No deals found</p>
              <Button className="mt-4 bg-[#08263e] hover:bg-[#08263e]/90" onClick={() => navigate('/deals/new')} data-testid="empty-new-deal-btn"><Plus className="h-4 w-4 mr-2" /> Create First Deal</Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Reference</TableHead>
                  <TableHead>Client</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Pair</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right">Rate</TableHead>
                  <TableHead>Deal Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {deals.map(deal => (
                  <TableRow key={deal.id} data-testid={`deal-row-${deal.id}`}>
                    <TableCell className="font-mono text-xs font-medium text-[#08263e]">{deal.reference_number}</TableCell>
                    <TableCell className="text-sm">{deal.client_name || '-'}</TableCell>
                    <TableCell className="text-sm">{deal.transaction_type}</TableCell>
                    <TableCell className="font-mono text-xs">{deal.buy_currency}/{deal.sell_currency}</TableCell>
                    <TableCell className="text-right font-mono text-xs">{Number(deal.amount).toLocaleString()}</TableCell>
                    <TableCell className="text-right font-mono text-xs">{deal.rate}</TableCell>
                    <TableCell className="text-xs">{format(new Date(deal.deal_date + 'T00:00:00'), 'dd MMM yyyy')}</TableCell>
                    <TableCell><Badge className={SB[deal.status]}>{deal.status}</Badge></TableCell>
                    <TableCell>
                      <Button size="icon" variant="ghost" className="h-8 w-8" onClick={async () => { const r = await api.get(`/deals/${deal.id}`); setSel(r.data); }} data-testid={`view-deal-${deal.id}`}>
                        <Eye className="h-3.5 w-3.5" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={!!sel} onOpenChange={o => { if (!o) setSel(null); }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="deal-detail-dialog">
          <DialogHeader><DialogTitle className="text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Deal Details - {sel?.reference_number}</DialogTitle></DialogHeader>
          {sel && (
            <div className="space-y-4">
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
                <DI label="From" val={`${sel.from_company} / ${sel.from_bank} (${sel.from_account_num})`} />
                <DI label="To" val={`${sel.to_company} / ${sel.to_bank} (${sel.to_account_num})`} />
                <DI label="Status" val={sel.status} />
                <DI label="Created By" val={sel.created_by_name} />
                {sel.processed_by_name && <DI label="Processed By" val={sel.processed_by_name} />}
                {sel.processed_at && <DI label="Processed At" val={format(new Date(sel.processed_at), 'dd MMM yyyy HH:mm')} />}
              </div>
              <div className="bg-slate-50 p-3 rounded-md text-center font-mono text-sm font-medium text-[#08263e]">
                {Number(sel.currency_amount).toLocaleString()} {sel.buy_currency} x {sel.rate} = {Number(sel.amount).toLocaleString()} {sel.sell_currency}
              </div>
              {sel.remarks && (<><Separator /><div className="bg-slate-50 p-3 rounded-md"><p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Remarks</p><p className="text-sm">{sel.remarks}</p></div></>)}
              {sel.treasury_remarks && (<div className="bg-blue-50 p-3 rounded-md"><p className="text-[10px] text-blue-400 uppercase tracking-wider mb-1">Treasury Remarks</p><p className="text-sm">{sel.treasury_remarks}</p></div>)}

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
                        <img src={`${process.env.REACT_APP_BACKEND_URL}/api/files/${p.path}`} alt={p.filename} className="w-full h-28 object-cover" />
                        <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                          <a href={`${process.env.REACT_APP_BACKEND_URL}/api/files/${p.path}`} target="_blank" rel="noopener noreferrer" className="text-white"><Eye className="h-4 w-4" /></a>
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
