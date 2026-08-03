import { useState, useCallback, useMemo, memo, useEffect } from 'react';
import api from '@/lib/api';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Command, CommandInput, CommandList, CommandEmpty, CommandGroup, CommandItem } from '@/components/ui/command';
import { Calendar } from '@/components/ui/calendar';
import { CalendarIcon, ChevronsUpDown, Check, Plus, Upload, X as XIcon, ImageIcon } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';

export function VField({ label, error, children }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-xs">{label} {error && <span className="text-red-500 text-[10px] ml-1">*{error}</span>}</Label>
      {children}
    </div>
  );
}

export function ProofUploadSection({ label, files, fileRef, onAdd, onRemove, testIdPrefix }) {
  return (
    <div>
      <p className="text-xs font-medium text-slate-600 uppercase tracking-wider mb-2">{label}</p>
      <input type="file" ref={fileRef} className="hidden" accept="image/*,.pdf,.doc,.docx" multiple onChange={onAdd} data-testid={`${testIdPrefix}-file-input`} />
      <Button type="button" variant="outline" className="w-full h-16 border-dashed border-2 hover:border-[#518dca] hover:bg-slate-50" onClick={() => fileRef.current?.click()} data-testid={`${testIdPrefix}-upload-btn`}>
        <div className="flex flex-col items-center gap-1 text-slate-400">
          <Upload className="h-4 w-4" />
          <span className="text-[11px]">Click to select files</span>
        </div>
      </Button>
      {files.length > 0 && (
        <div className="mt-2 space-y-1.5" data-testid={`${testIdPrefix}-file-list`}>
          {files.map((file, i) => (
            <div key={i} className="flex items-center gap-3 p-2 rounded-md bg-slate-50 border" data-testid={`${testIdPrefix}-file-${i}`}>
              <ImageIcon className="h-4 w-4 text-slate-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate">{file.name}</p>
                <p className="text-[10px] text-slate-400">{(file.size / 1024).toFixed(1)} KB</p>
              </div>
              <Button type="button" variant="ghost" size="icon" className="h-6 w-6 flex-shrink-0" onClick={() => onRemove(i)} data-testid={`${testIdPrefix}-remove-${i}`}>
                <XIcon className="h-3 w-3" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export const TypeToggle = memo(function TypeToggle({ value, name, onChange, testId }) {
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

const CRYPTO_NETWORKS = ['SOLANA', 'ETHEREUM', 'TRON'];

export const NetworkSelect = memo(function NetworkSelect({ value, name, onChange, tid, error }) {
  return (
    <VField label="Network" error={error}>
      <select
        value={value || ''}
        onChange={e => onChange(name, e.target.value)}
        data-testid={`${tid}-select`}
        className={`w-full h-9 rounded-md border px-3 text-sm ${error ? 'border-red-400' : 'border-input'} bg-background`}
      >
        <option value="">Select network...</option>
        {CRYPTO_NETWORKS.map(n => <option key={n} value={n}>{n}</option>)}
      </select>
    </VField>
  );
});

export const DatePick = memo(function DatePick({ label, value, name, onChange, tid, error }) {
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

export const SearchSelect = memo(function SearchSelect({ label, value, name, onChange, items, displayKey, tid, placeholder, error }) {
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

export const CurrSel = memo(function CurrSel({ label, value, name, onChange, fiat, stablecoin, crypto, tid, error }) {
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

export const BankAccountSelect = memo(function BankAccountSelect({ bankName, value, name, onChange, banks, tid, error }) {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [newMode, setNewMode] = useState(false);
  const [newAcct, setNewAcct] = useState('');
  const [newAcctName, setNewAcctName] = useState('');
  const [adding, setAdding] = useState(false);

  const bankId = useMemo(() => banks.find(b => b.name === bankName)?.id, [bankName, banks]);

  useEffect(() => {
    if (!bankId) { setAccounts([]); return; }
    let cancelled = false;
    setLoading(true);
    api.get(`/reference/banks/${bankId}/accounts`)
      .then(r => { if (!cancelled) setAccounts(r.data.filter(a => a.is_active !== false)); })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [bankId]);

  const selectedAcct = useMemo(() => accounts.find(a => a.account_number === value), [accounts, value]);
  const displayText = selectedAcct ? `${selectedAcct.account_name || ''} - ${selectedAcct.account_number}`.trim() : (value || '');

  const addAccount = async () => {
    if (!newAcct.trim() || !newAcctName.trim() || !bankId) return;
    setAdding(true);
    try {
      const r = await api.post(`/reference/banks/${bankId}/accounts`, { account_number: newAcct.trim(), account_name: newAcctName.trim() });
      setAccounts(p => [...p, r.data]);
      onChange(name, newAcct.trim());
      setNewAcct(''); setNewAcctName(''); setNewMode(false); setOpen(false);
      toast.success('Account added');
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to add account'); }
    finally { setAdding(false); }
  };

  if (!bankName) {
    return (
      <VField label="Account" error={error}>
        <Input disabled placeholder="Select a bank first" className="bg-slate-50" data-testid={`${tid}-input`} />
      </VField>
    );
  }

  return (
    <VField label="Account" error={error}>
      <Popover open={open} onOpenChange={o => { setOpen(o); if (!o) { setNewMode(false); setNewAcct(''); setNewAcctName(''); } }}>
        <PopoverTrigger asChild>
          <Button variant="outline" role="combobox" className={`w-full justify-between text-left font-normal h-9 text-sm ${error ? 'border-red-400' : ''}`} data-testid={`${tid}-select`}>
            <span className="truncate">{displayText || 'Search account...'}</span>
            <ChevronsUpDown className="ml-1 h-3.5 w-3.5 shrink-0 text-slate-400" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[320px] p-0" align="start">
          {newMode ? (
            <div className="p-3 space-y-2">
              <p className="text-xs font-medium text-slate-600">Add New Account</p>
              <Input value={newAcctName} onChange={e => setNewAcctName(e.target.value)} placeholder="Account name (required)" className="h-8 text-xs" data-testid={`${tid}-new-name-input`} autoFocus />
              <Input value={newAcct} onChange={e => setNewAcct(e.target.value)} placeholder="Account number (required)" className="h-8 text-xs font-mono" data-testid={`${tid}-new-input`} />
              <div className="flex gap-2 justify-end">
                <Button type="button" size="sm" variant="ghost" className="h-7 text-xs" onClick={() => { setNewMode(false); setNewAcct(''); setNewAcctName(''); }}>Cancel</Button>
                <Button type="button" size="sm" className="h-7 text-xs bg-[#08263e] hover:bg-[#08263e]/90" onClick={addAccount} disabled={adding || !newAcct.trim() || !newAcctName.trim()} data-testid={`${tid}-add-btn`}>
                  {adding ? 'Adding...' : 'Add'}
                </Button>
              </div>
            </div>
          ) : (
            <Command>
              <CommandInput placeholder="Search by name or number..." data-testid={`${tid}-search`} />
              <CommandList>
                {loading ? (
                  <div className="py-6 text-center text-xs text-slate-400">Loading accounts...</div>
                ) : accounts.length === 0 ? (
                  <CommandEmpty>No accounts found for this bank.</CommandEmpty>
                ) : (
                  <CommandGroup>
                    {accounts.map(a => (
                      <CommandItem key={a.id} value={`${a.account_name || ''} ${a.account_number}`} onSelect={() => { onChange(name, a.account_number); setOpen(false); }}>
                        <Check className={cn("mr-2 h-3 w-3", value === a.account_number ? "opacity-100" : "opacity-0")} />
                        <div className="flex flex-col">
                          <span className="text-xs font-medium">{a.account_name || 'Unnamed'}</span>
                          <span className="font-mono text-[10px] text-slate-400">{a.account_number}</span>
                        </div>
                      </CommandItem>
                    ))}
                  </CommandGroup>
                )}
                <div className="border-t p-1">
                  <button type="button" className="w-full text-left px-2 py-1.5 text-xs text-[#518dca] hover:bg-slate-50 rounded flex items-center gap-1.5" onClick={() => setNewMode(true)} data-testid={`${tid}-add-new-btn`}>
                    <Plus className="h-3 w-3" /> Add New Account
                  </button>
                </div>
              </CommandList>
            </Command>
          )}
        </PopoverContent>
      </Popover>
    </VField>
  );
});
