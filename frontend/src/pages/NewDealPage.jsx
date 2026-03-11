import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '@/lib/api';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Command, CommandInput, CommandList, CommandEmpty, CommandGroup, CommandItem } from '@/components/ui/command';
import { Calendar } from '@/components/ui/calendar';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { CalendarIcon, ArrowLeft, ChevronsUpDown, Check, AlertTriangle } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';

export default function NewDealPage() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [ref, setRef] = useState({ companies: [], banks: [], txTypes: [], tfTypes: [], currencies: [] });
  const [f, setF] = useState({
    transaction_type: '', transfer_type: '',
    deal_date: new Date(), value_date: new Date(),
    from_company: '', from_bank: '', from_account_num: '',
    to_company: '', to_bank: '', to_account_num: '',
    buy_currency: '', sell_currency: '',
    currency_amount: '', amount: '', rate: '', remarks: ''
  });

  useEffect(() => {
    Promise.all([
      api.get('/reference/companies'), api.get('/reference/banks'),
      api.get('/reference/transaction-types'), api.get('/reference/transfer-types'),
      api.get('/reference/currencies'),
    ]).then(([c, b, tx, tf, cur]) => {
      setRef({
        companies: c.data.filter(i => i.is_active),
        banks: b.data.filter(i => i.is_active),
        txTypes: tx.data.filter(i => i.is_active),
        tfTypes: tf.data.filter(i => i.is_active),
        currencies: cur.data.filter(i => i.is_active),
      });
    }).catch(console.error);
  }, []);

  const up = (k, v) => {
    setF(p => {
      const next = { ...p, [k]: v };
      if (k === 'currency_amount' || k === 'rate') {
        const ca = parseFloat(k === 'currency_amount' ? v : next.currency_amount) || 0;
        const r = parseFloat(k === 'rate' ? v : next.rate) || 0;
        next.amount = (ca > 0 && r > 0) ? (ca * r).toFixed(2) : '';
      }
      return next;
    });
  };

  const handlePreSubmit = (e) => {
    e.preventDefault();
    if (!f.transaction_type || !f.transfer_type || !f.buy_currency || !f.sell_currency || !f.from_company || !f.to_company) {
      toast.error('Please fill in all required fields');
      return;
    }
    setConfirmOpen(true);
  };

  const submit = async () => {
    setSubmitting(true);
    try {
      await api.post('/deals', {
        ...f,
        deal_date: format(f.deal_date, 'yyyy-MM-dd'),
        value_date: format(f.value_date, 'yyyy-MM-dd'),
        currency_amount: parseFloat(f.currency_amount) || 0,
        amount: parseFloat(f.amount) || 0,
        rate: parseFloat(f.rate) || 0,
      });
      toast.success('Deal ticket created successfully');
      navigate('/deals');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create deal');
    } finally { setSubmitting(false); setConfirmOpen(false); }
  };

  const fiat = ref.currencies.filter(c => c.type === 'fiat');
  const stablecoin = ref.currencies.filter(c => c.type === 'stablecoin');
  const crypto = ref.currencies.filter(c => c.type === 'crypto');

  return (
    <div data-testid="new-deal-page">
      <div className="flex items-center gap-4 mb-8">
        <Button variant="ghost" size="icon" onClick={() => navigate('/deals')} data-testid="back-btn">
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo' }}>New Deal Ticket</h1>
          <p className="text-sm text-slate-500 mt-1">Create a new FX trade deal</p>
        </div>
      </div>

      <form onSubmit={handlePreSubmit}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader><CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Deal Information</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Field label="Transaction Type">
                  <Select value={f.transaction_type} onValueChange={v => up('transaction_type', v)}>
                    <SelectTrigger data-testid="transaction-type-select"><SelectValue placeholder="Select..." /></SelectTrigger>
                    <SelectContent>{ref.txTypes.map(t => <SelectItem key={t.id} value={t.name}>{t.name}</SelectItem>)}</SelectContent>
                  </Select>
                </Field>
                <Field label="Transfer Type">
                  <Select value={f.transfer_type} onValueChange={v => up('transfer_type', v)}>
                    <SelectTrigger data-testid="transfer-type-select"><SelectValue placeholder="Select..." /></SelectTrigger>
                    <SelectContent>{ref.tfTypes.map(t => <SelectItem key={t.id} value={t.name}>{t.name}</SelectItem>)}</SelectContent>
                  </Select>
                </Field>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <DatePick label="Deal Date" value={f.deal_date} onChange={v => up('deal_date', v)} tid="deal-date" />
                <DatePick label="Value Date" value={f.value_date} onChange={v => up('value_date', v)} tid="value-date" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Amounts & Currency</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <CurrSel label="Buy Currency" value={f.buy_currency} onChange={v => up('buy_currency', v)} fiat={fiat} stablecoin={stablecoin} crypto={crypto} tid="buy-currency" />
                <CurrSel label="Sell Currency" value={f.sell_currency} onChange={v => up('sell_currency', v)} fiat={fiat} stablecoin={stablecoin} crypto={crypto} tid="sell-currency" />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <Field label={`Currency Amount${f.buy_currency ? ` (${f.buy_currency})` : ''}`}>
                  <Input type="number" step="0.01" value={f.currency_amount} onChange={e => up('currency_amount', e.target.value)} placeholder="0.00" data-testid="currency-amount-input" />
                </Field>
                <Field label="Exchange Rate">
                  <Input type="number" step="0.000001" value={f.rate} onChange={e => up('rate', e.target.value)} placeholder="0.000000" data-testid="rate-input" />
                </Field>
                <Field label={`Converted Amount${f.sell_currency ? ` (${f.sell_currency})` : ''}`}>
                  <Input type="number" step="0.01" value={f.amount} readOnly className="bg-slate-50 font-medium" placeholder="0.00" data-testid="amount-input" />
                </Field>
              </div>
              {f.buy_currency && f.sell_currency && f.currency_amount && f.rate && (
                <p className="text-xs text-slate-400 font-mono" data-testid="rate-summary">
                  {Number(f.currency_amount).toLocaleString()} {f.buy_currency} × {f.rate} = {Number(f.amount).toLocaleString()} {f.sell_currency}
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Source (From)</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <SearchSelect label="Company" value={f.from_company} onChange={v => up('from_company', v)} items={ref.companies} displayKey="name" tid="from-company" placeholder="Search company..." />
              <SearchSelect label="Bank" value={f.from_bank} onChange={v => up('from_bank', v)} items={ref.banks} displayKey="name" tid="from-bank" placeholder="Search bank..." />
              <Field label="Account Number">
                <Input value={f.from_account_num} onChange={e => up('from_account_num', e.target.value)} placeholder="Enter account number" data-testid="from-account-input" />
              </Field>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Destination (To)</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <SearchSelect label="Company" value={f.to_company} onChange={v => up('to_company', v)} items={ref.companies} displayKey="name" tid="to-company" placeholder="Search company..." />
              <SearchSelect label="Bank" value={f.to_bank} onChange={v => up('to_bank', v)} items={ref.banks} displayKey="name" tid="to-bank" placeholder="Search bank..." />
              <Field label="Account Number">
                <Input value={f.to_account_num} onChange={e => up('to_account_num', e.target.value)} placeholder="Enter account number" data-testid="to-account-input" />
              </Field>
            </CardContent>
          </Card>
        </div>

        <Card className="mt-6">
          <CardContent className="pt-6">
            <Field label="Remarks">
              <Textarea value={f.remarks} onChange={e => up('remarks', e.target.value)} placeholder="Additional notes..." rows={3} data-testid="remarks-input" />
            </Field>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-3 mt-6">
          <Button type="button" variant="outline" onClick={() => navigate('/deals')} data-testid="cancel-btn">Cancel</Button>
          <Button type="submit" className="bg-[#08263e] hover:bg-[#08263e]/90" disabled={submitting} data-testid="submit-deal-btn">
            {submitting ? 'Creating...' : 'Submit Deal Ticket'}
          </Button>
        </div>
      </form>

      <Dialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <DialogContent className="max-w-xl max-h-[90vh] overflow-y-auto" data-testid="confirm-deal-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-[#08263e]" style={{ fontFamily: 'Chivo' }}>
              <AlertTriangle className="h-5 w-5 text-[#f59e0b]" /> Confirm Deal Submission
            </DialogTitle>
          </DialogHeader>
          <p className="text-sm text-slate-500">Please review the deal details below before submitting.</p>
          <Separator />
          <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <ConfirmRow label="Transaction Type" val={f.transaction_type} />
            <ConfirmRow label="Transfer Type" val={f.transfer_type} />
            <ConfirmRow label="Deal Date" val={f.deal_date ? format(f.deal_date, 'dd MMM yyyy') : ''} />
            <ConfirmRow label="Value Date" val={f.value_date ? format(f.value_date, 'dd MMM yyyy') : ''} />
            <ConfirmRow label="Buy Currency" val={f.buy_currency} />
            <ConfirmRow label="Sell Currency" val={f.sell_currency} />
            <ConfirmRow label={`Currency Amount (${f.buy_currency || '-'})`} val={f.currency_amount ? Number(f.currency_amount).toLocaleString() : '-'} mono />
            <ConfirmRow label="Exchange Rate" val={f.rate || '-'} mono />
            <ConfirmRow label={`Converted Amount (${f.sell_currency || '-'})`} val={f.amount ? Number(f.amount).toLocaleString() : '-'} mono />
            <ConfirmRow label="From Company" val={f.from_company} />
            <ConfirmRow label="From Bank" val={f.from_bank} />
            <ConfirmRow label="From Account" val={f.from_account_num || '-'} mono />
            <ConfirmRow label="To Company" val={f.to_company} />
            <ConfirmRow label="To Bank" val={f.to_bank} />
            <ConfirmRow label="To Account" val={f.to_account_num || '-'} mono />
          </div>
          {f.remarks && (
            <>
              <Separator />
              <div>
                <p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Remarks</p>
                <p className="text-sm">{f.remarks}</p>
              </div>
            </>
          )}
          {f.buy_currency && f.sell_currency && f.currency_amount && f.rate && (
            <div className="bg-slate-50 p-3 rounded-md text-center font-mono text-sm font-medium text-[#08263e]">
              {Number(f.currency_amount).toLocaleString()} {f.buy_currency} x {f.rate} = {Number(f.amount).toLocaleString()} {f.sell_currency}
            </div>
          )}
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setConfirmOpen(false)} data-testid="confirm-cancel-btn">Go Back & Edit</Button>
            <Button className="bg-[#08263e] hover:bg-[#08263e]/90" onClick={submit} disabled={submitting} data-testid="confirm-submit-btn">
              {submitting ? 'Submitting...' : 'Confirm & Submit'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Field({ label, children }) {
  return <div className="space-y-1.5"><Label className="text-xs">{label}</Label>{children}</div>;
}

function DatePick({ label, value, onChange, tid }) {
  const [open, setOpen] = useState(false);
  return (
    <Field label={label}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" className="w-full justify-start text-left font-normal h-9 text-sm" data-testid={`${tid}-picker`}>
            <CalendarIcon className="mr-2 h-3.5 w-3.5 text-slate-400" />
            {value ? format(value, 'dd MMM yyyy') : 'Pick date'}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar mode="single" selected={value} onSelect={d => { if (d) { onChange(d); setOpen(false); } }} />
        </PopoverContent>
      </Popover>
    </Field>
  );
}

function CurrSel({ label, value, onChange, fiat, stablecoin, crypto, tid }) {
  const [open, setOpen] = useState(false);
  const all = [...fiat, ...stablecoin, ...crypto];
  const selected = all.find(c => c.code === value);

  return (
    <Field label={label}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" role="combobox" aria-expanded={open}
            className="w-full justify-between text-left font-normal h-9 text-sm"
            data-testid={`${tid}-select`}>
            <span className="truncate">{selected ? `${selected.code} - ${selected.name}` : 'Search currency...'}</span>
            <ChevronsUpDown className="ml-1 h-3.5 w-3.5 shrink-0 text-slate-400" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[280px] p-0" align="start">
          <Command>
            <CommandInput placeholder="Type to search..." data-testid={`${tid}-search`} />
            <CommandList>
              <CommandEmpty>No currency found.</CommandEmpty>
              {fiat.length > 0 && (
                <CommandGroup heading="Fiat Currencies">
                  {fiat.map(c => (
                    <CommandItem key={c.id} value={`${c.code} ${c.name}`} onSelect={() => { onChange(c.code); setOpen(false); }}>
                      <Check className={cn("mr-2 h-3 w-3", value === c.code ? "opacity-100" : "opacity-0")} />
                      <span className="font-mono text-xs mr-2">{c.code}</span>
                      <span className="text-xs text-slate-500 truncate">{c.name}</span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}
              {stablecoin.length > 0 && (
                <CommandGroup heading="Stablecoins">
                  {stablecoin.map(c => (
                    <CommandItem key={c.id} value={`${c.code} ${c.name}`} onSelect={() => { onChange(c.code); setOpen(false); }}>
                      <Check className={cn("mr-2 h-3 w-3", value === c.code ? "opacity-100" : "opacity-0")} />
                      <span className="font-mono text-xs mr-2">{c.code}</span>
                      <span className="text-xs text-slate-500 truncate">{c.name}</span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}
              {crypto.length > 0 && (
                <CommandGroup heading="Cryptocurrencies">
                  {crypto.map(c => (
                    <CommandItem key={c.id} value={`${c.code} ${c.name}`} onSelect={() => { onChange(c.code); setOpen(false); }}>
                      <Check className={cn("mr-2 h-3 w-3", value === c.code ? "opacity-100" : "opacity-0")} />
                      <span className="font-mono text-xs mr-2">{c.code}</span>
                      <span className="text-xs text-slate-500 truncate">{c.name}</span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </Field>
  );
}

function SearchSelect({ label, value, onChange, items, displayKey, tid, placeholder }) {
  const [open, setOpen] = useState(false);
  const selected = items.find(i => i[displayKey] === value);
  return (
    <Field label={label}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" role="combobox" aria-expanded={open}
            className="w-full justify-between text-left font-normal h-9 text-sm"
            data-testid={`${tid}-select`}>
            <span className="truncate">{selected ? selected[displayKey] : placeholder}</span>
            <ChevronsUpDown className="ml-1 h-3.5 w-3.5 shrink-0 text-slate-400" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[280px] p-0" align="start">
          <Command>
            <CommandInput placeholder={placeholder} data-testid={`${tid}-search`} />
            <CommandList>
              <CommandEmpty>No results found.</CommandEmpty>
              <CommandGroup>
                {items.map(item => (
                  <CommandItem key={item.id} value={item[displayKey]} onSelect={() => { onChange(item[displayKey]); setOpen(false); }}>
                    <Check className={cn("mr-2 h-3 w-3", value === item[displayKey] ? "opacity-100" : "opacity-0")} />
                    <span className="text-sm">{item[displayKey]}</span>
                    {item.code && <span className="ml-auto text-xs text-slate-400 font-mono">{item.code}</span>}
                  </CommandItem>
                ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </Field>
  );
}

function ConfirmRow({ label, val, mono }) {
  return (
    <div>
      <p className="text-[10px] text-slate-400 uppercase tracking-wider">{label}</p>
      <p className={`text-sm font-medium ${mono ? 'font-mono' : ''}`}>{val || '-'}</p>
    </div>
  );
}
