import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { CheckCircle, XCircle, Eye } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';

const SB = { pending: 'bg-yellow-100 text-yellow-800', confirmed: 'bg-green-100 text-green-800', returned: 'bg-red-100 text-red-800' };

export default function TreasuryPage() {
  const [deals, setDeals] = useState([]);
  const [sel, setSel] = useState(null);
  const [remarks, setRemarks] = useState('');
  const [processing, setProcessing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('pending');

  const load = useCallback(async () => {
    try { const r = await api.get('/deals'); setDeals(r.data); }
    catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

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

  const pending = deals.filter(d => d.status === 'pending');
  const done = deals.filter(d => d.status !== 'pending');

  return (
    <div data-testid="treasury-page">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Deal Queue</h1>
        <p className="text-sm text-slate-500 mt-1">Review and process FX deal tickets</p>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList data-testid="treasury-tabs">
          <TabsTrigger value="pending" data-testid="pending-tab">Pending ({pending.length})</TabsTrigger>
          <TabsTrigger value="processed" data-testid="processed-tab">Processed ({done.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="mt-4">
          <Card>
            <CardContent className="p-0">
              {loading ? (
                <div className="flex items-center justify-center h-32"><div className="animate-spin h-6 w-6 border-4 border-[#518dca] border-t-transparent rounded-full" /></div>
              ) : pending.length === 0 ? (
                <p className="text-center py-16 text-slate-400">No pending deals to process</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50">
                      <TableHead>Reference</TableHead>
                      <TableHead>Trader</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Pair</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead className="text-right">Rate</TableHead>
                      <TableHead>Deal Date</TableHead>
                      <TableHead>Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pending.map(d => (
                      <TableRow key={d.id} data-testid={`pending-deal-${d.id}`}>
                        <TableCell className="font-mono text-xs font-medium">{d.reference_number}</TableCell>
                        <TableCell className="text-sm">{d.created_by_name}</TableCell>
                        <TableCell className="text-sm">{d.transaction_type}</TableCell>
                        <TableCell className="font-mono text-xs">{d.buy_currency}/{d.sell_currency}</TableCell>
                        <TableCell className="text-right font-mono text-xs">{Number(d.amount).toLocaleString()}</TableCell>
                        <TableCell className="text-right font-mono text-xs">{d.rate}</TableCell>
                        <TableCell className="text-xs">{format(new Date(d.deal_date + 'T00:00:00'), 'dd MMM yyyy')}</TableCell>
                        <TableCell>
                          <Button size="sm" variant="outline" onClick={() => { setSel(d); setRemarks(''); }} data-testid={`review-deal-${d.id}`}>
                            <Eye className="h-3 w-3 mr-1" /> Review
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="processed" className="mt-4">
          <Card>
            <CardContent className="p-0">
              {done.length === 0 ? (
                <p className="text-center py-16 text-slate-400">No processed deals yet</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50">
                      <TableHead>Reference</TableHead>
                      <TableHead>Trader</TableHead>
                      <TableHead>Pair</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Processed By</TableHead>
                      <TableHead>Processed At</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {done.map(d => (
                      <TableRow key={d.id}>
                        <TableCell className="font-mono text-xs">{d.reference_number}</TableCell>
                        <TableCell className="text-sm">{d.created_by_name}</TableCell>
                        <TableCell className="font-mono text-xs">{d.buy_currency}/{d.sell_currency}</TableCell>
                        <TableCell className="text-right font-mono text-xs">{Number(d.amount).toLocaleString()}</TableCell>
                        <TableCell><Badge className={SB[d.status]}>{d.status}</Badge></TableCell>
                        <TableCell className="text-sm">{d.processed_by_name}</TableCell>
                        <TableCell className="text-xs">{d.processed_at ? format(new Date(d.processed_at), 'dd MMM yyyy HH:mm') : '-'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={!!sel} onOpenChange={o => !o && setSel(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="process-deal-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Chivo' }} className="text-[#08263e]">Review Deal - {sel?.reference_number}</DialogTitle>
          </DialogHeader>
          {sel && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
                <Info label="Transaction Type" val={sel.transaction_type} />
                <Info label="Transfer Type" val={sel.transfer_type} />
                <Info label="Buy Currency" val={sel.buy_currency} />
                <Info label="Sell Currency" val={sel.sell_currency} />
                <Info label="Currency Amount" val={Number(sel.currency_amount).toLocaleString()} mono />
                <Info label="Amount" val={Number(sel.amount).toLocaleString()} mono />
                <Info label="Rate" val={sel.rate} mono />
                <Info label="Deal Date" val={format(new Date(sel.deal_date + 'T00:00:00'), 'dd MMM yyyy')} />
                <Info label="Value Date" val={format(new Date(sel.value_date + 'T00:00:00'), 'dd MMM yyyy')} />
                <Info label="From" val={`${sel.from_company} / ${sel.from_bank}`} />
                <Info label="To" val={`${sel.to_company} / ${sel.to_bank}`} />
                <Info label="Trader" val={sel.created_by_name} />
              </div>
              {sel.remarks && (
                <div className="bg-slate-50 p-3 rounded-md">
                  <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Trader Remarks</p>
                  <p className="text-sm">{sel.remarks}</p>
                </div>
              )}
              <Separator />
              <div className="space-y-1.5">
                <Label className="text-xs">Treasury Remarks</Label>
                <Textarea value={remarks} onChange={e => setRemarks(e.target.value)} placeholder="Add your remarks..." rows={3} data-testid="treasury-remarks-input" />
              </div>
            </div>
          )}
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setSel(null)} data-testid="cancel-review-btn">Cancel</Button>
            <Button className="bg-[#ec474e] hover:bg-[#ec474e]/90 text-white" onClick={() => process('returned')} disabled={processing} data-testid="return-deal-btn">
              <XCircle className="h-4 w-4 mr-2" /> Return
            </Button>
            <Button className="bg-[#10b981] hover:bg-[#10b981]/90 text-white" onClick={() => process('confirmed')} disabled={processing} data-testid="confirm-deal-btn">
              <CheckCircle className="h-4 w-4 mr-2" /> Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Info({ label, val, mono }) {
  return (
    <div>
      <p className="text-[10px] text-slate-400 uppercase tracking-wider">{label}</p>
      <p className={`text-sm font-medium ${mono ? 'font-mono' : ''}`}>{val}</p>
    </div>
  );
}
