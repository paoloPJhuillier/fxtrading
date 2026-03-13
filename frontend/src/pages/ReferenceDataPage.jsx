import { useState, useEffect, useCallback, useRef, memo } from 'react';
import api from '@/lib/api';
import { useRefData } from '@/lib/refdata';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

const TABS = [
  { value: 'companies', label: 'Companies' },
  { value: 'banks', label: 'Banks' },
  { value: 'transaction-types', label: 'Transaction Types' },
  { value: 'transfer-types', label: 'Transfer Types' },
  { value: 'currencies', label: 'Currencies' },
];

export default function ReferenceDataPage() {
  const [tab, setTab] = useState('companies');
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [edit, setEdit] = useState(null);
  const [form, setForm] = useState({ name: '', code: '', swift_code: '', type: 'fiat', symbol: '' });

  const hasLoaded = useRef(false);
  const load = useCallback(async (signal) => {
    if (!hasLoaded.current) setLoading(true);
    try {
      const r = await api.get(`/reference/${tab}`, { signal });
      setItems(r.data);
      hasLoaded.current = true;
    } catch (e) { if (!signal?.aborted) console.error(e); }
    finally { if (!signal?.aborted) setLoading(false); }
  }, [tab]);

  useEffect(() => {
    const c = new AbortController();
    load(c.signal);
    return () => c.abort();
  }, [load]);

  const openNew = () => { setEdit(null); setForm({ name: '', code: '', swift_code: '', type: 'fiat', symbol: '' }); setOpen(true); };
  const openEdit = useCallback((item) => {
    setEdit(item);
    setForm({ name: item.name, code: item.code, swift_code: item.swift_code || '', type: item.type || 'fiat', symbol: item.symbol || '' });
    setOpen(true);
  }, []);

  const { reload: reloadRefData } = useRefData();

  const save = async () => {
    try {
      if (edit) {
        await api.put(`/reference/${tab}/${edit.id}`, form);
        toast.success('Updated');
      } else {
        await api.post(`/reference/${tab}`, form);
        toast.success('Created');
      }
      setOpen(false); load(); reloadRefData();
    } catch (e) { toast.error(e.response?.data?.detail || 'Save failed'); }
  };

  const del = useCallback(async (id) => {
    if (!window.confirm('Delete this item?')) return;
    try { await api.delete(`/reference/${tab}/${id}`); toast.success('Deleted'); load(); reloadRefData(); }
    catch (e) { toast.error('Delete failed'); }
  }, [tab, load, reloadRefData]);

  const isBank = tab === 'banks';
  const isCurr = tab === 'currencies';

  return (
    <div data-testid="reference-data-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Reference Data</h1>
          <p className="text-sm text-slate-500 mt-1">Manage system reference data</p>
        </div>
        <Button className="bg-[#08263e] hover:bg-[#08263e]/90" onClick={openNew} data-testid="add-item-btn">
          <Plus className="h-4 w-4 mr-2" /> Add New
        </Button>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="mb-4 flex-wrap" data-testid="ref-data-tabs">
          {TABS.map(t => <TabsTrigger key={t.value} value={t.value} data-testid={`tab-${t.value}`}>{t.label}</TabsTrigger>)}
        </TabsList>

        {TABS.map(t => (
          <TabsContent key={t.value} value={t.value}>
            <Card>
              <CardContent className="p-0">
                {loading && items.length === 0 ? (
                  <div className="flex items-center justify-center h-32"><div className="animate-spin h-6 w-6 border-4 border-[#518dca] border-t-transparent rounded-full" /></div>
                ) : items.length === 0 ? (
                  <p className="text-center py-16 text-slate-400">No items. Click "Add New" to create one.</p>
                ) : (
                  <div className={loading ? 'opacity-60 pointer-events-none transition-opacity' : 'transition-opacity'}>
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-slate-50">
                        <TableHead>Name</TableHead>
                        <TableHead>Code</TableHead>
                        {isBank && <TableHead>SWIFT Code</TableHead>}
                        {isCurr && <><TableHead>Type</TableHead><TableHead>Symbol</TableHead></>}
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {items.map(item => (
                        <RefRow key={item.id} item={item} isBank={isBank} isCurr={isCurr} onEdit={openEdit} onDelete={del} />
                      ))}
                    </TableBody>
                  </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>

      {open && (
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent data-testid="ref-item-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Chivo' }}>{edit ? 'Edit' : 'Add'} {TABS.find(t => t.value === tab)?.label?.replace(/s$/, '')}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-xs">Name</Label>
              <Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} data-testid="ref-name-input" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Code</Label>
              <Input value={form.code} onChange={e => setForm({ ...form, code: e.target.value })} data-testid="ref-code-input" />
            </div>
            {isBank && (
              <div className="space-y-1.5">
                <Label className="text-xs">SWIFT Code</Label>
                <Input value={form.swift_code} onChange={e => setForm({ ...form, swift_code: e.target.value })} data-testid="ref-swift-input" />
              </div>
            )}
            {isCurr && (
              <>
                <div className="space-y-1.5">
                  <Label className="text-xs">Type</Label>
                  <Select value={form.type} onValueChange={v => setForm({ ...form, type: v })}>
                    <SelectTrigger data-testid="ref-type-select"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="fiat">Fiat</SelectItem>
                      <SelectItem value="stablecoin">Stablecoin</SelectItem>
                      <SelectItem value="crypto">Crypto</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1.5">
                  <Label className="text-xs">Symbol</Label>
                  <Input value={form.symbol} onChange={e => setForm({ ...form, symbol: e.target.value })} data-testid="ref-symbol-input" />
                </div>
              </>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)} data-testid="ref-cancel-btn">Cancel</Button>
            <Button className="bg-[#08263e] hover:bg-[#08263e]/90" onClick={save} data-testid="ref-save-btn">Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      )}
    </div>
  );
}

const RefRow = memo(function RefRow({ item, isBank, isCurr, onEdit, onDelete }) {
  return (
    <TableRow data-testid={`ref-item-${item.id}`}>
      <TableCell className="font-medium text-sm">{item.name}</TableCell>
      <TableCell className="font-mono text-xs">{item.code}</TableCell>
      {isBank && <TableCell className="font-mono text-xs">{item.swift_code || '-'}</TableCell>}
      {isCurr && (
        <>
          <TableCell><Badge variant={item.type === 'crypto' ? 'secondary' : 'outline'} className={`text-xs ${item.type === 'stablecoin' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : ''}`}>{item.type}</Badge></TableCell>
          <TableCell className="text-sm">{item.symbol}</TableCell>
        </>
      )}
      <TableCell><Badge className={item.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>{item.is_active ? 'Active' : 'Inactive'}</Badge></TableCell>
      <TableCell className="text-right">
        <div className="flex justify-end gap-1">
          <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => onEdit(item)} data-testid={`edit-${item.id}`}><Pencil className="h-3 w-3" /></Button>
          <Button size="icon" variant="ghost" className="h-8 w-8 text-red-500 hover:text-red-700" onClick={() => onDelete(item.id)} data-testid={`delete-${item.id}`}><Trash2 className="h-3 w-3" /></Button>
        </div>
      </TableCell>
    </TableRow>
  );
});
