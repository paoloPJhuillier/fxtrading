import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import api from './api';
import { useAuth } from './auth';

const RefDataContext = createContext(null);

export function RefDataProvider({ children }) {
  const { user } = useAuth();
  const [data, setData] = useState(null);

  const load = useCallback(async (signal) => {
    try {
      const opts = signal ? { signal } : {};
      const [c, b, tx, tf, cur] = await Promise.all([
        api.get('/reference/companies', opts),
        api.get('/reference/banks', opts),
        api.get('/reference/transaction-types', opts),
        api.get('/reference/transfer-types', opts),
        api.get('/reference/currencies', opts),
      ]);
      setData({
        companies: c.data.filter(i => i.is_active),
        banks: b.data.filter(i => i.is_active),
        txTypes: tx.data.filter(i => i.is_active),
        tfTypes: tf.data.filter(i => i.is_active),
        currencies: cur.data.filter(i => i.is_active),
        _all: {
          companies: c.data, banks: b.data, txTypes: tx.data, tfTypes: tf.data, currencies: cur.data,
        }
      });
    } catch (e) { if (!signal?.aborted) console.error(e); }
  }, []);

  useEffect(() => {
    if (!user) return;
    const c = new AbortController();
    load(c.signal);
    return () => c.abort();
  }, [user, load]);

  return (
    <RefDataContext.Provider value={{ data, reload: load }}>
      {children}
    </RefDataContext.Provider>
  );
}

export const useRefData = () => useContext(RefDataContext);
