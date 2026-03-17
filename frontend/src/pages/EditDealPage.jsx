import { useState, useCallback, useMemo, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '@/lib/api';
import { useRefData } from '@/lib/refdata';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, RotateCcw } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';
import { VField, TypeToggle, DatePick, SearchSelect, CurrSel, BankAccountSelect } from '@/components/DealFormFields';

export default function EditDealPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [deal, setDeal] = useState(null);
  const [saving, setSaving] = useState(false);
  const [resubmitting, setResubmitting] = useState(false);
  const [errors, setErrors] = useState({});
  const { data: ref } = useRefData();
  const safeRef = ref || { companies: [], banks: [], txTypes: [], tfTypes: [], currencies: [] };

  const [f, setF] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api.get(`/deals/${id}`)
      .then(res => {
        if (cancelled) return;
        const d = res.data;
        if (d.status !== 'returned') {
          toast.error('Only returned deals can be edited');
          navigate('/deals');
          return;
        }
        setDeal(d);
        setF({
          transaction_type: d.transaction_type || '',
          transfer_type: d.transfer_type || '',
          client_name: d.client_name || '',
          deal_date: d.deal_date ? new Date(d.deal_date + 'T00:00:00') : new Date(),
          value_date: d.value_date ? new Date(d.value_date + 'T00:00:00') : new Date(),
          from_type: d.from_type || 'bank',
          from_company: d.from_company || '',
          from_bank: d.from_bank || '',
          from_account_num: d.from_account_num || '',
          from_wallet_address: d.from_wallet_address || '',
          to_type: d.to_type || 'bank',
          to_company: d.to_company || '',
          to_bank: d.to_bank || '',
          to_account_num: d.to_account_num || '',
          to_wallet_address: d.to_wallet_address || '',
          ours_type: d.ours_type || 'bank',
          ours_bank: d.ours_bank || '',
          ours_account_num: d.ours_account_num || '',
          ours_wallet_address: d.ours_wallet_address || '',
          buy_currency: d.buy_currency || '',
          sell_currency: d.sell_currency || '',
          currency_amount: d.currency_amount?.toString() || '',
          amount: d.amount?.toString() || '',
          rate: d.rate?.toString() || '',
          remarks: d.remarks || '',
        });
        setLoading(false);
      })
      .catch(() => {
        if (!cancelled) { toast.error('Failed to load deal'); navigate('/deals'); }
      });
    return () => { cancelled = true; };
  }, [id, navigate]);

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
      if (k === 'from_bank') { next.from_account_num = ''; }
      if (k === 'to_bank') { next.to_account_num = ''; }
      if (k === 'ours_bank') { next.ours_account_num = ''; }
      return next;
    });
    setErrors(p => p[k] ? { ...p, [k]: null } : p);
  }, []);

  const onInput = useCallback(e => up(e.target.name, e.target.value), [up]);

  const fiat = useMemo(() => safeRef.currencies.filter(c => c.type === 'fiat'), [safeRef.currencies]);
  const stablecoin = useMemo(() => safeRef.currencies.filter(c => c.type === 'stablecoin'), [safeRef.currencies]);
  const crypto = useMemo(() => safeRef.currencies.filter(c => c.type === 'crypto'), [safeRef.currencies]);

  const buildPayload = () => {
    if (!deal || !f) return null;
    const payload = {};
    const strFields = ['transaction_type','transfer_type','client_name','from_type','from_company','from_bank','from_account_num','from_wallet_address','to_type','to_company','to_bank','to_account_num','to_wallet_address','ours_type','ours_bank','ours_account_num','ours_wallet_address','buy_currency','sell_currency','remarks'];
    strFields.forEach(k => { if (f[k] !== (deal[k] || '')) payload[k] = f[k]; });
    const dateFields = ['deal_date','value_date'];
    dateFields.forEach(k => {
      const fmtd = f[k] ? format(f[k], 'yyyy-MM-dd') : '';
      if (fmtd !== (deal[k] || '')) payload[k] = fmtd;
    });
    if (parseFloat(f.currency_amount) !== deal.currency_amount) payload.currency_amount = parseFloat(f.currency_amount) || 0;
    if (parseFloat(f.rate) !== deal.rate) payload.rate = parseFloat(f.rate) || 0;
    if (parseFloat(f.amount) !== deal.amount) payload.amount = parseFloat(f.amount) || 0;
    return payload;
  };

  const handleSave = async () => {
    const payload = buildPayload();
    if (!payload || Object.keys(payload).length === 0) { toast.info('No changes to save'); return; }
    setSaving(true);
    try {
      await api.put(`/deals/${id}/edit`, payload);
      toast.success('Deal updated successfully');
      navigate('/deals');
    } catch (err) { toast.error(err.response?.data?.detail || 'Save failed'); }
    finally { setSaving(false); }
  };

  const handleSaveAndResubmit = async () => {
    const payload = buildPayload();
    setSaving(true);
    setResubmitting(true);
    try {
      if (payload && Object.keys(payload).length > 0) {
        await api.put(`/deals/${id}/edit`, payload);
      }
      await api.put(`/deals/${id}/resubmit`);
      toast.success('Deal updated and resubmitted for review');
      navigate('/deals');
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setSaving(false); setResubmitting(false); }
  };

  if (loading || !f) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-4 border-[#518dca] border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div data-testid="edit-deal-page">
      <div className="flex items-center gap-4 mb-8">
        <Button variant="ghost" size="icon" onClick={() => navigate('/deals')} data-testid="back-btn"><ArrowLeft className="h-5 w-5" /></Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Edit Deal Ticket</h1>
          <p className="text-sm text-slate-500 mt-1">{deal?.reference_number}</p>
        </div>
        <Badge className="bg-red-100 text-red-800 text-xs">returned</Badge>
      </div>

      {deal?.treasury_remarks && (
        <div className="bg-red-50 border border-red-300 p-4 rounded-md mb-6" data-testid="returned-alert">
          <p className="text-xs font-semibold text-red-700 uppercase tracking-wider mb-1">Deal Returned by Treasury</p>
          <p className="text-sm text-red-800">{deal.treasury_remarks}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Deal Information</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <VField label="Client Name" error={errors.client_name}>
              <Input name="client_name" value={f.client_name} onChange={onInput} placeholder="Enter client name" data-testid="edit-client-name-input" className={errors.client_name ? 'border-red-400' : ''} />
            </VField>
            <div className="grid grid-cols-2 gap-4">
              <VField label="Transaction Type" error={errors.transaction_type}>
                <Select value={f.transaction_type} onValueChange={v => up('transaction_type', v)}>
                  <SelectTrigger data-testid="edit-transaction-type-select" className={errors.transaction_type ? 'border-red-400' : ''}><SelectValue placeholder="Select..." /></SelectTrigger>
                  <SelectContent>{safeRef.txTypes.map(t => <SelectItem key={t.id} value={t.name}>{t.name}</SelectItem>)}</SelectContent>
                </Select>
              </VField>
              <VField label="Transfer Type" error={errors.transfer_type}>
                <Select value={f.transfer_type} onValueChange={v => up('transfer_type', v)}>
                  <SelectTrigger data-testid="edit-transfer-type-select" className={errors.transfer_type ? 'border-red-400' : ''}><SelectValue placeholder="Select..." /></SelectTrigger>
                  <SelectContent>{safeRef.tfTypes.map(t => <SelectItem key={t.id} value={t.name}>{t.name}</SelectItem>)}</SelectContent>
                </Select>
              </VField>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <DatePick label="Deal Date" value={f.deal_date} name="deal_date" onChange={up} tid="edit-deal-date" error={errors.deal_date} />
              <DatePick label="Value Date" value={f.value_date} name="value_date" onChange={up} tid="edit-value-date" error={errors.value_date} />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Amounts & Currency</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <CurrSel label="Buy Currency" value={f.buy_currency} name="buy_currency" onChange={up} fiat={fiat} stablecoin={stablecoin} crypto={crypto} tid="edit-buy-currency" error={errors.buy_currency} />
              <CurrSel label="Sell Currency" value={f.sell_currency} name="sell_currency" onChange={up} fiat={fiat} stablecoin={stablecoin} crypto={crypto} tid="edit-sell-currency" error={errors.sell_currency} />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <VField label={`Currency Amount${f.buy_currency ? ` (${f.buy_currency})` : ''}`} error={errors.currency_amount}>
                <Input name="currency_amount" type="number" step="0.01" value={f.currency_amount} onChange={onInput} placeholder="0.00" data-testid="edit-currency-amount-input" className={errors.currency_amount ? 'border-red-400' : ''} />
              </VField>
              <VField label="Exchange Rate" error={errors.rate}>
                <Input name="rate" type="number" step="0.000001" value={f.rate} onChange={onInput} placeholder="0.000000" data-testid="edit-rate-input" className={errors.rate ? 'border-red-400' : ''} />
              </VField>
              <VField label={`Converted Amount${f.sell_currency ? ` (${f.sell_currency})` : ''}`}>
                <Input type="number" step="0.01" value={f.amount} readOnly className="bg-slate-50 font-medium" placeholder="0.00" data-testid="edit-amount-input" />
              </VField>
            </div>
            {f.buy_currency && f.sell_currency && f.currency_amount && f.rate && (
              <p className="text-xs text-slate-400 font-mono" data-testid="edit-rate-summary">
                {Number(f.currency_amount).toLocaleString()} {f.buy_currency} x {f.rate} = {Number(f.amount).toLocaleString()} {f.sell_currency}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Source (From)</CardTitle>
              <TypeToggle value={f.from_type} name="from_type" onChange={up} testId="edit-from-type" />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <SearchSelect label="Company" value={f.from_company} name="from_company" onChange={up} items={safeRef.companies} displayKey="name" tid="edit-from-company" placeholder="Search company..." error={errors.from_company} />
            {f.from_type === 'bank' ? (
              <>
                <SearchSelect label="Bank" value={f.from_bank} name="from_bank" onChange={up} items={safeRef.banks} displayKey="name" tid="edit-from-bank" placeholder="Search bank..." error={errors.from_bank} />
                <BankAccountSelect bankName={f.from_bank} value={f.from_account_num} name="from_account_num" onChange={up} banks={safeRef.banks} tid="edit-from-account" error={errors.from_account_num} />
              </>
            ) : (
              <VField label="Wallet Address" error={errors.from_wallet_address}>
                <Input name="from_wallet_address" value={f.from_wallet_address} onChange={onInput} placeholder="Enter crypto wallet address" data-testid="edit-from-wallet-input" className={errors.from_wallet_address ? 'border-red-400' : ''} />
              </VField>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Destination (To)</CardTitle>
              <TypeToggle value={f.to_type} name="to_type" onChange={up} testId="edit-to-type" />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <SearchSelect label="Company" value={f.to_company} name="to_company" onChange={up} items={safeRef.companies} displayKey="name" tid="edit-to-company" placeholder="Search company..." error={errors.to_company} />
            {f.to_type === 'bank' ? (
              <>
                <SearchSelect label="Bank" value={f.to_bank} name="to_bank" onChange={up} items={safeRef.banks} displayKey="name" tid="edit-to-bank" placeholder="Search bank..." error={errors.to_bank} />
                <BankAccountSelect bankName={f.to_bank} value={f.to_account_num} name="to_account_num" onChange={up} banks={safeRef.banks} tid="edit-to-account" error={errors.to_account_num} />
              </>
            ) : (
              <VField label="Wallet Address" error={errors.to_wallet_address}>
                <Input name="to_wallet_address" value={f.to_wallet_address} onChange={onInput} placeholder="Enter crypto wallet address" data-testid="edit-to-wallet-input" className={errors.to_wallet_address ? 'border-red-400' : ''} />
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
            <TypeToggle value={f.ours_type} name="ours_type" onChange={up} testId="edit-ours-type" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {f.ours_type === 'bank' ? (
              <>
                <SearchSelect label="Bank" value={f.ours_bank} name="ours_bank" onChange={up} items={safeRef.banks} displayKey="name" tid="edit-ours-bank" placeholder="Search bank..." error={errors.ours_bank} />
                <BankAccountSelect bankName={f.ours_bank} value={f.ours_account_num} name="ours_account_num" onChange={up} banks={safeRef.banks} tid="edit-ours-account" error={errors.ours_account_num} />
              </>
            ) : (
              <VField label="Wallet Address" error={errors.ours_wallet_address}>
                <Input name="ours_wallet_address" value={f.ours_wallet_address} onChange={onInput} placeholder="Enter crypto wallet address" data-testid="edit-ours-wallet-input" className={errors.ours_wallet_address ? 'border-red-400' : ''} />
              </VField>
            )}
          </div>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardContent className="pt-6">
          <VField label="Remarks (optional)">
            <Textarea name="remarks" value={f.remarks} onChange={onInput} placeholder="Additional notes..." rows={3} data-testid="edit-remarks-input" />
          </VField>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-3 mt-6 mb-16">
        <Button type="button" variant="outline" onClick={() => navigate('/deals')} data-testid="edit-cancel-btn">Cancel</Button>
        <Button type="button" variant="outline" onClick={handleSave} disabled={saving} data-testid="edit-save-btn">
          {saving && !resubmitting ? 'Saving...' : 'Save Changes'}
        </Button>
        <Button type="button" className="bg-[#518dca] hover:bg-[#518dca]/90 gap-1.5" onClick={handleSaveAndResubmit} disabled={saving} data-testid="edit-save-resubmit-btn">
          <RotateCcw className="h-3.5 w-3.5" /> {resubmitting ? 'Resubmitting...' : 'Save & Resubmit'}
        </Button>
      </div>
    </div>
  );
}
