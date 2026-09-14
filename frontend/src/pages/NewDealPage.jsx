import { useState, useCallback, useMemo, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '@/lib/api';
import { useRefData } from '@/lib/refdata';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { ArrowLeft, AlertTriangle } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';
import { VField, TypeToggle, DatePick, SearchSelect, CurrSel, BankAccountSelect, ProofUploadSection, NetworkSelect } from '@/components/DealFormFields';

export default function NewDealPage() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [errors, setErrors] = useState({});
  const [clientProofFiles, setClientProofFiles] = useState([]);
  const [processorProofFiles, setProcessorProofFiles] = useState([]);
  const clientProofRef = useRef(null);
  const processorProofRef = useRef(null);
  const { data: ref } = useRefData();
  const safeRef = ref || { companies: [], banks: [], txTypes: [], tfTypes: [], currencies: [], counterparties: [] };

  const [heavyReady, setHeavyReady] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setHeavyReady(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const [f, setF] = useState({
    transaction_type: '', transfer_type: '', client_name: '', counterparty: '',
    deal_date: new Date(), value_date: new Date(),
    from_type: 'bank', from_company: '', from_bank: '', from_account_num: '', from_wallet_address: '', from_network: '',
    to_type: 'bank', to_company: '', to_bank: '', to_account_num: '', to_wallet_address: '', to_network: '',
    ours_type: 'bank', ours_bank: '', ours_account_num: '', ours_wallet_address: '', ours_network: '',
    buying_ours_type: 'bank', buying_ours_bank: '', buying_ours_account_num: '', buying_ours_wallet_address: '', buying_ours_network: '',
    buy_currency: '', sell_currency: '',
    currency_amount: '', amount: '', rate: '', remarks: ''
  });

  const isFxBankDeal = f.transfer_type === 'FX Bank Deal';
  const isFxLocal = f.transfer_type === 'FX Local' || f.transfer_type === 'FX - Corporate Settlement';
  const isFxInterco = f.transfer_type === 'FX-Intercompany';
  const showCounterparty = isFxLocal || isFxInterco;
  const showDestination = !isFxBankDeal;
  const showBuyingOurs = isFxInterco;

  // Dynamic Ours label
  const oursLabel = isFxInterco ? 'Selling Counterparty Ours (Receiving Account)' : 'Ours (Receiving Account)';

  const up = useCallback((k, v) => {
    setF(p => {
      const next = { ...p, [k]: v };
      // When transfer type changes, reset conditional fields
      if (k === 'transfer_type') {
        next.counterparty = '';
        if (v === 'FX Bank Deal') {
          next.to_type = 'bank'; next.to_company = ''; next.to_bank = '';
          next.to_account_num = ''; next.to_wallet_address = '';
        }
        if (v !== 'FX-Intercompany') {
          next.buying_ours_type = 'bank'; next.buying_ours_bank = '';
          next.buying_ours_account_num = ''; next.buying_ours_wallet_address = '';
        }
      }
      // Auto-compute: Amount = Currency Amount × Rate (always multiply)
      if (k === 'currency_amount' || k === 'rate') {
        const ca = parseFloat(k === 'currency_amount' ? v : next.currency_amount) || 0;
        const r = parseFloat(k === 'rate' ? v : next.rate) || 0;
        next.amount = (ca > 0 && r > 0) ? (ca * r).toFixed(2) : '';
      }
      if (k === 'from_type') { next.from_bank = ''; next.from_account_num = ''; next.from_wallet_address = ''; next.from_network = ''; }
      if (k === 'to_type') { next.to_bank = ''; next.to_account_num = ''; next.to_wallet_address = ''; next.to_network = ''; }
      if (k === 'ours_type') { next.ours_bank = ''; next.ours_account_num = ''; next.ours_wallet_address = ''; next.ours_network = ''; }
      if (k === 'buying_ours_type') { next.buying_ours_bank = ''; next.buying_ours_account_num = ''; next.buying_ours_wallet_address = ''; next.buying_ours_network = ''; }
      if (k === 'from_bank') { next.from_account_num = ''; }
      if (k === 'to_bank') { next.to_account_num = ''; }
      if (k === 'ours_bank') { next.ours_account_num = ''; }
      if (k === 'buying_ours_bank') { next.buying_ours_account_num = ''; }
      // Auto-sync: counterparty selection also sets from_company and to_company
      if (k === 'counterparty') {
        next.from_company = v;
        next.to_company = v;
      }
      return next;
    });
    setErrors(p => p[k] ? { ...p, [k]: null } : p);
  }, []);

  const onInput = useCallback(e => up(e.target.name, e.target.value), [up]);

  const fiat = useMemo(() => safeRef.currencies.filter(c => c.type === 'fiat'), [safeRef.currencies]);
  const stablecoin = useMemo(() => safeRef.currencies.filter(c => c.type === 'stablecoin'), [safeRef.currencies]);
  const crypto = useMemo(() => safeRef.currencies.filter(c => c.type === 'crypto'), [safeRef.currencies]);

  const validate = () => {
    const errs = {};
    const base = ['transaction_type', 'transfer_type', 'client_name', 'buy_currency', 'currency_amount', 'rate'];
    if (showCounterparty) base.push('counterparty');
    if (!showCounterparty) base.push('from_company');
    if (showDestination && !showCounterparty) base.push('to_company');
    base.forEach(k => { if (!f[k]) errs[k] = 'Required'; });
    if (!f.deal_date) errs.deal_date = 'Required';
    if (!f.value_date) errs.value_date = 'Required';
    if (f.from_type === 'bank') {
      if (!f.from_bank) errs.from_bank = 'Required';
      if (!f.from_account_num) errs.from_account_num = 'Required';
    } else { if (!f.from_wallet_address) errs.from_wallet_address = 'Required'; if (!f.from_network) errs.from_network = 'Required'; }
    if (showDestination) {
      if (f.to_type === 'bank') {
        if (!f.to_bank) errs.to_bank = 'Required';
        if (!f.to_account_num) errs.to_account_num = 'Required';
      } else { if (!f.to_wallet_address) errs.to_wallet_address = 'Required'; if (!f.to_network) errs.to_network = 'Required'; }
    }
    if (f.ours_type === 'bank') {
      if (!f.ours_bank) errs.ours_bank = 'Required';
      if (!f.ours_account_num) errs.ours_account_num = 'Required';
    } else { if (!f.ours_wallet_address) errs.ours_wallet_address = 'Required'; if (!f.ours_network) errs.ours_network = 'Required'; }
    if (showBuyingOurs) {
      if (f.buying_ours_type === 'bank') {
        if (!f.buying_ours_bank) errs.buying_ours_bank = 'Required';
        if (!f.buying_ours_account_num) errs.buying_ours_account_num = 'Required';
      } else { if (!f.buying_ours_wallet_address) errs.buying_ours_wallet_address = 'Required'; if (!f.buying_ours_network) errs.buying_ours_network = 'Required'; }
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handlePreSubmit = (e) => {
    e.preventDefault();
    if (!validate()) { toast.error('Please fill in all required fields'); return; }
    setConfirmOpen(true);
  };

  const addClientProofs = useCallback((e) => {
    const files = Array.from(e.target.files || []);
    setClientProofFiles(p => [...p, ...files]);
    if (clientProofRef.current) clientProofRef.current.value = '';
  }, []);
  const addProcessorProofs = useCallback((e) => {
    const files = Array.from(e.target.files || []);
    setProcessorProofFiles(p => [...p, ...files]);
    if (processorProofRef.current) processorProofRef.current.value = '';
  }, []);
  const removeClientProof = useCallback((idx) => {
    setClientProofFiles(p => p.filter((_, i) => i !== idx));
  }, []);
  const removeProcessorProof = useCallback((idx) => {
    setProcessorProofFiles(p => p.filter((_, i) => i !== idx));
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
      const totalProofs = clientProofFiles.length + processorProofFiles.length;
      if (totalProofs > 0) {
        for (const file of clientProofFiles) {
          const fd = new FormData();
          fd.append('file', file);
          await api.post(`/deals/${dealId}/upload?proof_type=client`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
        }
        for (const file of processorProofFiles) {
          const fd = new FormData();
          fd.append('file', file);
          await api.post(`/deals/${dealId}/upload?proof_type=processor`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
        }
        toast.success(`Deal created with ${totalProofs} proof(s) uploaded`);
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
              <CurrSel label="Currency" value={f.buy_currency} name="buy_currency" onChange={up} fiat={fiat} stablecoin={stablecoin} crypto={crypto} tid="buy-currency" error={errors.buy_currency} />
              <div className="grid grid-cols-3 gap-4">
                <VField label="Currency Amount" error={errors.currency_amount}>
                  <Input name="currency_amount" type="text" inputMode="decimal" value={f.currency_amount} onChange={e => { const v = e.target.value.replace(/[^0-9.]/g, ''); up('currency_amount', v); }} placeholder="0.00" data-testid="currency-amount-input" className={errors.currency_amount ? 'border-red-400' : ''} />
                  {f.currency_amount && <p className="text-[10px] text-slate-400 mt-0.5 font-mono">{Number(f.currency_amount).toLocaleString()}</p>}
                </VField>
                <VField label="Exchange Rate" error={errors.rate}>
                  <Input name="rate" type="text" inputMode="decimal" value={f.rate} onChange={e => { const v = e.target.value.replace(/[^0-9.]/g, ''); up('rate', v); }} placeholder="0.000000" data-testid="rate-input" className={errors.rate ? 'border-red-400' : ''} />
                </VField>
                <VField label="Converted Amount">
                  <Input type="text" value={f.amount ? Number(f.amount).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) : ''} readOnly className="bg-slate-50 font-medium" placeholder="0.00" data-testid="amount-input" />
                </VField>
              </div>
              {f.buy_currency && f.currency_amount && f.rate && (
                <p className="text-xs text-slate-400 font-mono" data-testid="rate-summary">
                  {Number(f.currency_amount).toLocaleString()} {f.buy_currency} x {f.rate} = {Number(f.amount).toLocaleString()} Converted
                </p>
              )}
            </CardContent>
          </Card>

          {heavyReady && (<>
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Source (From)</CardTitle>
                <TypeToggle value={f.from_type} name="from_type" onChange={up} testId="from-type" />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {showCounterparty ? (
                <SearchSelect label="Counterparty" value={f.counterparty} name="counterparty" onChange={up} items={safeRef.counterparties} displayKey="name" tid="counterparty" placeholder="Search counterparty..." error={errors.counterparty} />
              ) : (
                <SearchSelect label="Company" value={f.from_company} name="from_company" onChange={up} items={safeRef.companies} displayKey="name" tid="from-company" placeholder="Search company..." error={errors.from_company} />
              )}
              {f.from_type === 'bank' ? (
                <>
                  <SearchSelect label="Bank" value={f.from_bank} name="from_bank" onChange={up} items={safeRef.banks} displayKey="name" tid="from-bank" placeholder="Search bank..." error={errors.from_bank} />
                  <BankAccountSelect bankName={f.from_bank} value={f.from_account_num} name="from_account_num" onChange={up} banks={safeRef.banks} tid="from-account" error={errors.from_account_num} />
                </>
              ) : (
                <>
                  <VField label="Wallet Address" error={errors.from_wallet_address}>
                    <Input name="from_wallet_address" value={f.from_wallet_address} onChange={onInput} placeholder="Enter crypto wallet address" data-testid="from-wallet-input" className={errors.from_wallet_address ? 'border-red-400' : ''} />
                  </VField>
                  <NetworkSelect value={f.from_network} name="from_network" onChange={up} tid="from-network" error={errors.from_network} />
                </>
              )}
            </CardContent>
          </Card>

          {showDestination && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Destination (To)</CardTitle>
                <TypeToggle value={f.to_type} name="to_type" onChange={up} testId="to-type" />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {(isFxInterco) ? (
                <SearchSelect label="Counterparty" value={f.counterparty || ''} name="counterparty" onChange={up} items={safeRef.counterparties} displayKey="name" tid="to-counterparty" placeholder="Search counterparty..." />
              ) : (
                <SearchSelect label="Company" value={f.to_company} name="to_company" onChange={up} items={safeRef.companies} displayKey="name" tid="to-company" placeholder="Search company..." error={errors.to_company} />
              )}
              {f.to_type === 'bank' ? (
                <>
                  <SearchSelect label="Bank" value={f.to_bank} name="to_bank" onChange={up} items={safeRef.banks} displayKey="name" tid="to-bank" placeholder="Search bank..." error={errors.to_bank} />
                  <BankAccountSelect bankName={f.to_bank} value={f.to_account_num} name="to_account_num" onChange={up} banks={safeRef.banks} tid="to-account" error={errors.to_account_num} />
                </>
              ) : (
                <>
                  <VField label="Wallet Address" error={errors.to_wallet_address}>
                    <Input name="to_wallet_address" value={f.to_wallet_address} onChange={onInput} placeholder="Enter crypto wallet address" data-testid="to-wallet-input" className={errors.to_wallet_address ? 'border-red-400' : ''} />
                  </VField>
                  <NetworkSelect value={f.to_network} name="to_network" onChange={up} tid="to-network" error={errors.to_network} />
                </>
              )}
            </CardContent>
          </Card>
          )}

          {!showDestination && (
            <Card className="border-dashed border-slate-300 bg-slate-50/50">
              <CardContent className="py-8 text-center">
                <p className="text-xs text-slate-400">Destination (To) is not applicable for FX Bank Deal</p>
              </CardContent>
            </Card>
          )}
          </>)}
        </div>

        {heavyReady && (<>
        <Card className="mt-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>{oursLabel}</CardTitle>
                <p className="text-xs text-slate-400 mt-1">Account where the client credits us</p>
                {showCounterparty && f.counterparty && (
                  <p className="text-xs text-[#518dca] font-medium mt-1" data-testid="ours-counterparty-display">Counterparty: {f.counterparty}</p>
                )}
              </div>
              <TypeToggle value={f.ours_type} name="ours_type" onChange={up} testId="ours-type" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {f.ours_type === 'bank' ? (
                <>
                  <SearchSelect label="Bank" value={f.ours_bank} name="ours_bank" onChange={up} items={safeRef.banks} displayKey="name" tid="ours-bank" placeholder="Search bank..." error={errors.ours_bank} />
                  <BankAccountSelect bankName={f.ours_bank} value={f.ours_account_num} name="ours_account_num" onChange={up} banks={safeRef.banks} tid="ours-account" error={errors.ours_account_num} />
                </>
              ) : (
                <>
                  <VField label="Wallet Address" error={errors.ours_wallet_address}>
                    <Input name="ours_wallet_address" value={f.ours_wallet_address} onChange={onInput} placeholder="Enter crypto wallet address" data-testid="ours-wallet-input" className={errors.ours_wallet_address ? 'border-red-400' : ''} />
                  </VField>
                  <NetworkSelect value={f.ours_network} name="ours_network" onChange={up} tid="ours-network" error={errors.ours_network} />
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {showBuyingOurs && (
        <Card className="mt-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Buying Counterparty Ours (Receiving Account)</CardTitle>
                <p className="text-xs text-slate-400 mt-1">Buying counterparty's receiving account</p>
              </div>
              <TypeToggle value={f.buying_ours_type} name="buying_ours_type" onChange={up} testId="buying-ours-type" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {f.buying_ours_type === 'bank' ? (
                <>
                  <SearchSelect label="Bank" value={f.buying_ours_bank} name="buying_ours_bank" onChange={up} items={safeRef.banks} displayKey="name" tid="buying-ours-bank" placeholder="Search bank..." error={errors.buying_ours_bank} />
                  <BankAccountSelect bankName={f.buying_ours_bank} value={f.buying_ours_account_num} name="buying_ours_account_num" onChange={up} banks={safeRef.banks} tid="buying-ours-account" error={errors.buying_ours_account_num} />
                </>
              ) : (
                <>
                  <VField label="Wallet Address" error={errors.buying_ours_wallet_address}>
                    <Input name="buying_ours_wallet_address" value={f.buying_ours_wallet_address} onChange={onInput} placeholder="Enter crypto wallet address" data-testid="buying-ours-wallet-input" className={errors.buying_ours_wallet_address ? 'border-red-400' : ''} />
                  </VField>
                  <NetworkSelect value={f.buying_ours_network} name="buying_ours_network" onChange={up} tid="buying-ours-network" error={errors.buying_ours_network} />
                </>
              )}
            </div>
          </CardContent>
        </Card>
        )}

        <Card className="mt-6">
          <CardContent className="pt-6">
            <VField label="Remarks (optional)">
              <Textarea name="remarks" value={f.remarks} onChange={onInput} placeholder="Additional notes..." rows={3} data-testid="remarks-input" />
            </VField>
          </CardContent>
        </Card>

        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Settlement Proofs (optional)</CardTitle>
            <p className="text-xs text-slate-400 mt-1">Upload separate proofs for client and processor settlements</p>
          </CardHeader>
          <CardContent className="space-y-6">
            {!isFxBankDeal && (
              <ProofUploadSection label="Client's Settlement" files={clientProofFiles} fileRef={clientProofRef} onAdd={addClientProofs} onRemove={removeClientProof} testIdPrefix="client-proof" />
            )}
            {isFxBankDeal && (
              <div className="text-center py-4 border border-dashed rounded-lg bg-slate-50/50">
                <p className="text-[10px] text-slate-400">Client's Settlement is not applicable for FX Bank Deal</p>
              </div>
            )}
            <ProofUploadSection label="Processor's Settlement" files={processorProofFiles} fileRef={processorProofRef} onAdd={addProcessorProofs} onRemove={removeProcessorProof} testIdPrefix="processor-proof" />
          </CardContent>
        </Card>

        <div className="flex justify-end gap-3 mt-6 mb-16">
          <Button type="button" variant="outline" onClick={() => navigate('/deals')} data-testid="cancel-btn">Cancel</Button>
          <Button type="submit" className="bg-[#08263e] hover:bg-[#08263e]/90" disabled={submitting} data-testid="submit-deal-btn">
            {submitting ? 'Creating...' : 'Submit Deal Ticket'}
          </Button>
        </div>
        </>)}
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
            {!showDestination ? (
              <div className="col-span-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Destination (To) — N/A (FX Bank Deal)</div>
            ) : (
              <>
                <div className="col-span-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Destination (To) — {f.to_type === 'bank' ? 'Bank' : 'Crypto'}</div>
                {isFxInterco ? <CR label="Counterparty" val={f.counterparty} /> : <CR label="Company" val={f.to_company} />}
                {f.to_type === 'bank' ? (<><CR label="Bank" val={f.to_bank} /><CR label="Account Number" val={f.to_account_num} mono /></>) : (<CR label="Wallet Address" val={f.to_wallet_address} mono />)}
              </>
            )}
          </div>
          <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-sm">
            <div className="col-span-2 text-[10px] font-semibold text-slate-500 uppercase tracking-wider bg-yellow-50 p-1.5 rounded">Ours (Receiving) — {f.ours_type === 'bank' ? 'Bank' : 'Crypto'}</div>
            {f.ours_type === 'bank' ? (<><CR label="Bank" val={f.ours_bank} /><CR label="Account Number" val={f.ours_account_num} mono /></>) : (<CR label="Wallet Address" val={f.ours_wallet_address} mono />)}
          </div>
          {f.remarks && (<><Separator /><div><p className="text-[10px] text-slate-400 uppercase tracking-wider mb-1">Remarks</p><p className="text-sm">{f.remarks}</p></div></>)}
          {(clientProofFiles.length > 0 || processorProofFiles.length > 0) && (
            <div className="bg-blue-50 border border-blue-200 p-3 rounded-md">
              <p className="text-xs font-medium text-blue-700">{clientProofFiles.length + processorProofFiles.length} proof file(s) will be uploaded</p>
              {clientProofFiles.length > 0 && <><p className="text-[10px] text-blue-600 font-medium mt-1">Client's Settlement:</p>{clientProofFiles.map((pf, i) => <p key={`c${i}`} className="text-[10px] text-blue-500 truncate">{pf.name}</p>)}</>}
              {processorProofFiles.length > 0 && <><p className="text-[10px] text-blue-600 font-medium mt-1">Processor's Settlement:</p>{processorProofFiles.map((pf, i) => <p key={`p${i}`} className="text-[10px] text-blue-500 truncate">{pf.name}</p>)}</>}
            </div>
          )}
          {f.buy_currency && f.currency_amount && f.rate && (
            <div className="bg-slate-50 p-3 rounded-md text-center font-mono text-sm font-medium text-[#08263e]">
              {Number(f.currency_amount).toLocaleString()} {f.buy_currency} x {f.rate} = {Number(f.amount).toLocaleString()} Converted
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

function CR({ label, val, mono }) {
  return (<div><p className="text-[10px] text-slate-400 uppercase tracking-wider">{label}</p><p className={`text-sm font-medium ${mono ? 'font-mono' : ''}`}>{val || '-'}</p></div>);
}
