import { useState, useCallback, useMemo, memo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '@/lib/api';
import { useRefData } from '@/lib/refdata';
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
import { CalendarIcon, ArrowLeft, ChevronsUpDown, Check, AlertTriangle, Upload, X as XIcon, ImageIcon } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';

export default function NewDealPage() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [errors, setErrors] = useState({});
  const [proofFiles, setProofFiles] = useState([]);
  const proofRef = useRef(null);
  const { data: ref } = useRefData();
  const safeRef = ref || { companies: [], banks: [], txTypes: [], tfTypes: [], currencies: [] };
  const [f, setF] = useState({
    transaction_type: '', transfer_type: '', client_name: '',
    deal_date: new Date(), value_date: new Date(),
    from_type: 'bank', from_company: '', from_bank: '', from_account_num: '', from_wallet_address: '',
    to_type: 'bank', to_company: '', to_bank: '', to_account_num: '', to_wallet_address: '',
    ours_type: 'bank', ours_bank: '', ours_account_num: '', ours_wallet_address: '',
    buy_currency: '', sell_currency: '',
    currency_amount: '', amount: '', rate: '', remarks: ''
  });

  // Stable handler — uses only functional updaters, no external deps
  const up = useCallback((k, v) => {
    setF(p => {
      const next = { ...p, [k]: v };
      if (k === 'currency_amount' || k === 'rate') {
        const ca = parseFloat(k === 'currency_amount' ? v : next.currency_amount) || 0;
        const r = parseFloat(k === 'rate' ? v : next.rate) || 0;
        next.amount = (ca > 0 && r > 0) ? (ca * r).toFixed(2) : '';
      }
      if (k === 'from_type') { next.from_bank = ''; next.from_account_num = ''; next.from_wallet_address = ''; }
      if (k === 'to_type') { next.to_bank = ''; next.to_account_num = ''; next.to_wallet_address = ''; }
      if (k === 'ours_type') { next.ours_bank = ''; next.ours_account_num = ''; next.ours_wallet_address = ''; }
      return next;
    });
    setErrors(p => p[k] ? { ...p, [k]: null } : p);
  }, []);

  // Single stable callback for all native inputs (uses e.target.name)
  const onInput = useCallback(e => up(e.target.name, e.target.value), [up]);

  // Memoized derived arrays — stable refs unless currencies change
  const fiat = useMemo(() => safeRef.currencies.filter(c => c.type === 'fiat'), [safeRef.currencies]);
  const stablecoin = useMemo(() => safeRef.currencies.filter(c => c.type === 'stablecoin'), [safeRef.currencies]);
  const crypto = useMemo(() => safeRef.currencies.filter(c => c.type === 'crypto'), [safeRef.currencies]);

  const validate = () => {
    const errs = {};
    const base = ['transaction_type', 'transfer_type', 'client_name', 'from_company', 'to_company', 'buy_currency', 'sell_currency', 'currency_amount', 'rate'];
    base.forEach(k => { if (!f[k]) errs[k] = 'Required'; });
    if (!f.deal_date) errs.deal_date = 'Required';
    if (!f.value_date) errs.value_date = 'Required';
    if (f.from_type === 'bank') {
      if (!f.from_bank) errs.from_bank = 'Required';
      if (!f.from_account_num) errs.from_account_num = 'Required';
    } else { if (!f.from_wallet_address) errs.from_wallet_address = 'Required'; }
    if (f.to_type === 'bank') {
      if (!f.to_bank) errs.to_bank = 'Required';
      if (!f.to_account_num) errs.to_account_num = 'Required';
    } else { if (!f.to_wallet_address) errs.to_wallet_address = 'Required'; }
    if (f.ours_type === 'bank') {
      if (!f.ours_bank) errs.ours_bank = 'Required';
      if (!f.ours_account_num) errs.ours_account_num = 'Required';
    } else { if (!f.ours_wallet_address) errs.ours_wallet_address = 'Required'; }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handlePreSubmit = (e) => {
    e.preventDefault();
    if (!validate()) { toast.error('Please fill in all required fields'); return; }
    setConfirmOpen(true);
  };

  const addProofFiles = useCallback((e) => {
    const files = Array.from(e.target.files || []);
    setProofFiles(p => [...p, ...files]);
    if (proofRef.current) proofRef.current.value = '';
  }, []);

  const removeProofFile = useCallback((idx) => {
    setProofFiles(p => p.filter((_, i) => i !== idx));
  }, []);

  const submit = async () => {
    setSubmitting(true);
    try {
      const res = await api.post('/deals', {
        ...f,
        deal_date: format(f.deal_date, 'yyyy-MM-dd'),
        value_date: format(f.value_date, 'yyyy-MM-dd'),
        currency_amount: parseFloat(f.currency_amount) || 0,
        amount: parseFloat(f.amount) || 0,
        rate: parseFloat(f.rate) || 0,
      });
      const dealId = res.data.id;
      if (proofFiles.length > 0) {
        for (const file of proofFiles) {
          const fd = new FormData();
          fd.append('file', file);
          await api.post(`/deals/${dealId}/upload`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
        }
        toast.success(`Deal created with ${proofFiles.length} proof(s) uploaded`);
      } else {
        toast.success('Deal ticket created successfully');
      }
      navigate('/deals');
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed to create deal'); }
    finally { setSubmitting(false); setConfirmOpen(false); }
  };

  return (
    <div data-testid="new-deal-page">
      <div className="flex items-center gap-4 mb-8">
        <Button variant="ghost" size="icon" onClick={() => navigate('/deals')} data-testid="back-btn"><ArrowLeft className="h-5 w-5" /></Button>
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
              <VField label="Client Name" error={errors.client_name}>
                <Input name="client_name" value={f.client_name} onChange={onInput} placeholder="Enter client name" data-testid="client-name-input" className={errors.client_name ? 'border-red-400' : ''} />
              </VField>
              <div className="grid grid-cols-2 gap-4">
                <VField label="Transaction Type" error={errors.transaction_type}>
                  <Select value={f.transaction_type} onValueChange={v => up('transaction_type', v)}>
                    <SelectTrigger data-testid="transaction-type-select" className={errors.transaction_type ? 'border-red-400' : ''}><SelectValue placeholder="Select..." /></SelectTrigger>
                    <SelectContent>{safeRef.txTypes.map(t => <SelectItem key={t.id} value={t.name}>{t.name}</SelectItem>)}</SelectContent>
                  </Select>
                </VField>
                <VField label="Transfer Type" error={errors.transfer_type}>
                  <Select value={f.transfer_type} onValueChange={v => up('transfer_type', v)}>
                    <SelectTrigger data-testid="transfer-type-select" className={errors.transfer_type ? 'border-red-400' : ''}><SelectValue placeholder="Select..." /></SelectTrigger>
                    <SelectContent>{safeRef.tfTypes.map(t => <SelectItem key={t.id} value={t.name}>{t.name}</SelectItem>)}</SelectContent>
                  </Select>
                </VField>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <DatePick label="Deal Date" value={f.deal_date} name="deal_date" onChange={up} tid="deal-date" error={errors.deal_date} />
                <DatePick label="Value Date" value={f.value_date} name="value_date" onChange={up} tid="value-date" error={errors.value_date} />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Amounts & Currency</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <CurrSel label="Buy Currency" value={f.buy_currency} name="buy_currency" onChange={up} fiat={fiat} stablecoin={stablecoin} crypto={crypto} tid="buy-currency" error={errors.buy_currency} />
                <CurrSel label="Sell Currency" value={f.sell_currency} name="sell_currency" onChange={up} fiat={fiat} stablecoin={stablecoin} crypto={crypto} tid="sell-currency" error={errors.sell_currency} />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <VField label={`Currency Amount${f.buy_currency ? ` (${f.buy_currency})` : ''}`} error={errors.currency_amount}>
                  <Input name="currency_amount" type="number" step="0.01" value={f.currency_amount} onChange={onInput} placeholder="0.00" data-testid="currency-amount-input" className={errors.currency_amount ? 'border-red-400' : ''} />
                </VField>
                <VField label="Exchange Rate" error={errors.rate}>
                  <Input name="rate" type="number" step="0.000001" value={f.rate} onChange={onInput} placeholder="0.000000" data-testid="rate-input" className={errors.rate ? 'border-red-400' : ''} />
                </VField>
                <VField label={`Converted Amount${f.sell_currency ? ` (${f.sell_currency})` : ''}`}>
                  <Input type="number" step="0.01" value={f.amount} readOnly className="bg-slate-50 font-medium" placeholder="0.00" data-testid="amount-input" />
                </VField>
              </div>
              {f.buy_currency && f.sell_currency && f.currency_amount && f.rate && (
                <p className="text-xs text-slate-400 font-mono" data-testid="rate-summary">
                  {Number(f.currency_amount).toLocaleString()} {f.buy_currency} x {f.rate} = {Number(f.amount).toLocaleString()} {f.sell_currency}
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Source (From)</CardTitle>
                <TypeToggle value={f.from_type} name="from_type" onChange={up} testId="from-type" />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <SearchSelect label="Company" value={f.from_company} name="from_company" onChange={up} items={safeRef.companies} displayKey="name" tid="from-company" placeholder="Search company..." error={errors.from_company} />
              {f.from_type === 'bank' ? (
                <>
                  <SearchSelect label="Bank" value={f.from_bank} name="from_bank" onChange={up} items={safeRef.banks} displayKey="name" tid="from-bank" placeholder="Search bank..." error={errors.from_bank} />
                  <VField label="Account Number" error={errors.from_account_num}>
                    <Input name="from_account_num" value={f.from_account_num} onChange={onInput} placeholder="Enter account number" data-testid="from-account-input" className={errors.from_account_num ? 'border-red-400' : ''} />
                  </VField>
                </>
              ) : (
                <VField label="Wallet Address" error={errors.from_wallet_address}>
                  <Input name="from_wallet_address" value={f.from_wallet_address} onChange={onInput} placeholder="Enter crypto wallet address" data-testid="from-wallet-input" className={errors.from_wallet_address ? 'border-red-400' : ''} />
                </VField>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Destination (To)</CardTitle>
                <TypeToggle value={f.to_type} name="to_type" onChange={up} testId="to-type" />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <SearchSelect label="Company" value={f.to_company} name="to_company" onChange={up} items={safeRef.companies} displayKey="name" tid="to-company" placeholder="Search company..." error={errors.to_company} />
              {f.to_type === 'bank' ? (
                <>
                  <SearchSelect label="Bank" value={f.to_bank} name="to_bank" onChange={up} items={safeRef.banks} displayKey="name" tid="to-bank" placeholder="Search bank..." error={errors.to_bank} />
                  <VField label="Account Number" error={errors.to_account_num}>
                    <Input name="to_account_num" value={f.to_account_num} onChange={onInput} placeholder="Enter account number" data-testid="to-account-input" className={errors.to_account_num ? 'border-red-400' : ''} />
                  </VField>
                </>
              ) : (
                <VField label="Wallet Address" error={errors.to_wallet_address}>
                  <Input name="to_wallet_address" value={f.to_wallet_address} onChange={onInput} placeholder="Enter crypto wallet address" data-testid="to-wallet-input" className={errors.to_wallet_address ? 'border-red-400' : ''} />
                </VField>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="mt-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Ours (Receiving Account)</CardTitle>
                <p className="text-xs text-slate-400 mt-1">Account where the client credits us</p>
              </div>
              <TypeToggle value={f.ours_type} name="ours_type" onChange={up} testId="ours-type" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {f.ours_type === 'bank' ? (
                <>
                  <SearchSelect label="Bank" value={f.ours_bank} name="ours_bank" onChange={up} items={safeRef.banks} displayKey="name" tid="ours-bank" placeholder="Search bank..." error={errors.ours_bank} />
                  <VField label="Account Number" error={errors.ours_account_num}>
                    <Input name="ours_account_num" value={f.ours_account_num} onChange={onInput} placeholder="Enter account number" data-testid="ours-account-input" className={errors.ours_account_num ? 'border-red-400' : ''} />
                  </VField>
                </>
              ) : (
                <VField label="Wallet Address" error={errors.ours_wallet_address}>
                  <Input name="ours_wallet_address" value={f.ours_wallet_address} onChange={onInput} placeholder="Enter crypto wallet address" data-testid="ours-wallet-input" className={errors.ours_wallet_address ? 'border-red-400' : ''} />
                </VField>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardContent className="pt-6">
            <VField label="Remarks (optional)">
              <Textarea name="remarks" value={f.remarks} onChange={onInput} placeholder="Additional notes..." rows={3} data-testid="remarks-input" />
            </VField>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Proof of Payment (optional)</CardTitle>
            <p className="text-xs text-slate-400 mt-1">Upload settlement proof documents or screenshots</p>
          </CardHeader>
          <CardContent>
            <input type="file" ref={proofRef} className="hidden" accept="image/*,.pdf,.doc,.docx" multiple onChange={addProofFiles} data-testid="proof-file-input" />
            <Button type="button" variant="outline" className="w-full h-20 border-dashed border-2 hover:border-[#518dca] hover:bg-slate-50" onClick={() => proofRef.current?.click()} data-testid="proof-upload-btn">
              <div className="flex flex-col items-center gap-1 text-slate-400">
                <Upload className="h-5 w-5" />
                <span className="text-xs">Click to select files</span>
              </div>
            </Button>
            {proofFiles.length > 0 && (
              <div className="mt-3 space-y-2" data-testid="proof-file-list">
                {proofFiles.map((file, i) => (
                  <div key={i} className="flex items-center gap-3 p-2 rounded-md bg-slate-50 border" data-testid={`proof-file-${i}`}>
                    <ImageIcon className="h-4 w-4 text-slate-400 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate">{file.name}</p>
                      <p className="text-[10px] text-slate-400">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                    <Button type="button" variant="ghost" size="icon" className="h-6 w-6 flex-shrink-0" onClick={() => removeProofFile(i)} data-testid={`remove-proof-${i}`}>
                      <XIcon className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex justify-end gap-3 mt-6 mb-16">
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
            <CR label="Client" val={f.client_name} />
            <CR label="Transaction Type" val={f.transaction_type} />
            <CR label="Transfer Type" val={f.transfer_type} />
            <CR label="Deal Date" val={f.deal_date ? format(f.deal_date, 'dd MMM yyyy') : ''} />
            <CR label="Value Date" val={f.value_date ? format(f.value_date, 'dd MMM yyyy') : ''} />
            <CR label="Buy Currency" val={f.buy_currency} />
            <CR label="Sell Currency" val={f.sell_currency} />
            <CR label={`Currency Amount (${f.buy_currency || '-'})`} val={f.currency_amount ? Number(f.currency_amount).toLocaleString() : '-'} mono />
            <CR label="Exchange Rate" val={f.rate || '-'} mono />
            <CR label={`Converted Amount (${f.sell_currency || '-'})`} val={f.amount ? Number(f.amount).toLocaleString() : '-'} mono />
          </div>
          <Separator />
          <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <div className="col-span-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Source (From) — {f.from_type === 'bank' ? 'Bank' : 'Crypto'}</div>
            <CR label="Company" val={f.from_company} />
            {f.from_type === 'bank' ? (<><CR label="Bank" val={f.from_bank} /><CR label="Account Number" val={f.from_account_num} mono /></>) : (<CR label="Wallet Address" val={f.from_wallet_address} mono />)}
          </div>
          <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <div className="col-span-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Destination (To) — {f.to_type === 'bank' ? 'Bank' : 'Crypto'}</div>
            <CR label="Company" val={f.to_company} />
            {f.to_type === 'bank' ? (<><CR label="Bank" val={f.to_bank} /><CR label="Account Number" val={f.to_account_num} mono /></>) : (<CR label="Wallet Address" val={f.to_wallet_address} mono />)}
          </div>
          <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <div className="col-span-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider bg-yellow-50 p-1.5 rounded">Ours (Receiving) — {f.ours_type === 'bank' ? 'Bank' : 'Crypto'}</div>
            {f.ours_type === 'bank' ? (<><CR label="Bank" val={f.ours_bank} /><CR label="Account Number" val={f.ours_account_num} mono /></>) : (<CR label="Wallet Address" val={f.ours_wallet_address} mono />)}
          </div>
          {f.remarks && (<><Separator /><div><p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Remarks</p><p className="text-sm">{f.remarks}</p></div></>)}
          {proofFiles.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 p-3 rounded-md">
              <p className="text-xs font-medium text-blue-700">{proofFiles.length} proof file(s) will be uploaded</p>
              <div className="mt-1 space-y-0.5">{proofFiles.map((f, i) => <p key={i} className="text-[10px] text-blue-500 truncate">{f.name}</p>)}</div>
            </div>
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

function VField({ label, error, children }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs">{label} {error && <span className="text-red-500 text-[10px] ml-1">*{error}</span>}</Label>
      {children}
    </div>
  );
}

function CR({ label, val, mono }) {
  return (<div><p className="text-[10px] text-slate-400 uppercase tracking-wider">{label}</p><p className={`text-sm font-medium ${mono ? 'font-mono' : ''}`}>{val || '-'}</p></div>);
}

// Memo'd — stable onChange(name, value) + name prop prevents re-renders
const TypeToggle = memo(function TypeToggle({ value, name, onChange, testId }) {
  return (
    <div className="flex gap-1 p-0.5 bg-slate-100 rounded-md w-fit">
      <button type="button" onClick={() => onChange(name, 'bank')} data-testid={`${testId}-bank`}
        className={`px-3 py-1 text-xs font-medium rounded transition-colors ${value === 'bank' ? 'bg-[#08263e] text-white shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>
        Bank
      </button>
      <button type="button" onClick={() => onChange(name, 'crypto')} data-testid={`${testId}-crypto`}
        className={`px-3 py-1 text-xs font-medium rounded transition-colors ${value === 'crypto' ? 'bg-[#08263e] text-white shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>
        Crypto
      </button>
    </div>
  );
});

const DatePick = memo(function DatePick({ label, value, name, onChange, tid, error }) {
  const [open, setOpen] = useState(false);
  const handleSelect = useCallback(d => {
    if (d) { onChange(name, d); setOpen(false); }
  }, [onChange, name]);
  return (
    <VField label={label} error={error}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" className={`w-full justify-start text-left font-normal h-9 text-sm ${error ? 'border-red-400' : ''}`} data-testid={`${tid}-picker`}>
            <CalendarIcon className="mr-2 h-3.5 w-3.5 text-slate-400" />
            {value ? format(value, 'dd MMM yyyy') : 'Pick date'}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar mode="single" selected={value} onSelect={handleSelect} />
        </PopoverContent>
      </Popover>
    </VField>
  );
});

const SearchSelect = memo(function SearchSelect({ label, value, name, onChange, items, displayKey, tid, placeholder, error }) {
  const [open, setOpen] = useState(false);
  const selected = items.find(i => i[displayKey] === value);
  const handleSelect = useCallback(val => {
    onChange(name, val);
    setOpen(false);
  }, [onChange, name]);
  return (
    <VField label={label} error={error}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" role="combobox" aria-expanded={open} className={`w-full justify-between text-left font-normal h-9 text-sm ${error ? 'border-red-400' : ''}`} data-testid={`${tid}-select`}>
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
                  <CommandItem key={item.id} value={item[displayKey]} onSelect={() => handleSelect(item[displayKey])}>
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
    </VField>
  );
});

const CurrItem = memo(function CurrItem({ c, value, onSelect }) {
  return (
    <CommandItem value={`${c.code} ${c.name}`} onSelect={() => onSelect(c.code)}>
      <Check className={cn("mr-2 h-3 w-3", value === c.code ? "opacity-100" : "opacity-0")} />
      <span className="font-mono text-xs mr-2">{c.code}</span>
      <span className="text-xs text-slate-500 truncate">{c.name}</span>
    </CommandItem>
  );
});

const CurrSel = memo(function CurrSel({ label, value, name, onChange, fiat, stablecoin, crypto, tid, error }) {
  const [open, setOpen] = useState(false);
  const all = useMemo(() => [...fiat, ...stablecoin, ...crypto], [fiat, stablecoin, crypto]);
  const selected = all.find(c => c.code === value);
  const handleSelect = useCallback(code => {
    onChange(name, code);
    setOpen(false);
  }, [onChange, name]);
  return (
    <VField label={label} error={error}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="outline" role="combobox" aria-expanded={open} className={`w-full justify-between text-left font-normal h-9 text-sm ${error ? 'border-red-400' : ''}`} data-testid={`${tid}-select`}>
            <span className="truncate">{selected ? `${selected.code} - ${selected.name}` : 'Search currency...'}</span>
            <ChevronsUpDown className="ml-1 h-3.5 w-3.5 shrink-0 text-slate-400" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[280px] p-0" align="start">
          <Command>
            <CommandInput placeholder="Type to search..." data-testid={`${tid}-search`} />
            <CommandList>
              <CommandEmpty>No currency found.</CommandEmpty>
              {fiat.length > 0 && <CommandGroup heading="Fiat Currencies">{fiat.map(c => <CurrItem key={c.id} c={c} value={value} onSelect={handleSelect} />)}</CommandGroup>}
              {stablecoin.length > 0 && <CommandGroup heading="Stablecoins">{stablecoin.map(c => <CurrItem key={c.id} c={c} value={value} onSelect={handleSelect} />)}</CommandGroup>}
              {crypto.length > 0 && <CommandGroup heading="Cryptocurrencies">{crypto.map(c => <CurrItem key={c.id} c={c} value={value} onSelect={handleSelect} />)}</CommandGroup>}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </VField>
  );
});
