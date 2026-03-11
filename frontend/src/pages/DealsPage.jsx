import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, FileText } from 'lucide-react';
import { format } from 'date-fns';

const STATUS_MAP = {
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-green-100 text-green-800',
  returned: 'bg-red-100 text-red-800',
};

export default function DealsPage() {
  const [deals, setDeals] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const params = filter !== 'all' ? `?status=${filter}` : '';
        const res = await api.get(`/deals${params}`);
        setDeals(res.data);
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    })();
  }, [filter]);

  return (
    <div data-testid="deals-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo' }}>My Deals</h1>
          <p className="text-sm text-slate-500 mt-1">{deals.length} deal{deals.length !== 1 ? 's' : ''}</p>
        </div>
        <div className="flex gap-3">
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-36" data-testid="status-filter">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="confirmed">Confirmed</SelectItem>
              <SelectItem value="returned">Returned</SelectItem>
            </SelectContent>
          </Select>
          <Button className="bg-[#08263e] hover:bg-[#08263e]/90" onClick={() => navigate('/deals/new')} data-testid="new-deal-btn">
            <Plus className="h-4 w-4 mr-2" /> New Deal
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin h-6 w-6 border-4 border-[#518dca] border-t-transparent rounded-full" />
            </div>
          ) : deals.length === 0 ? (
            <div className="text-center py-16">
              <FileText className="h-12 w-12 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-500">No deals found</p>
              <Button className="mt-4 bg-[#08263e] hover:bg-[#08263e]/90" onClick={() => navigate('/deals/new')} data-testid="empty-new-deal-btn">
                <Plus className="h-4 w-4 mr-2" /> Create First Deal
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Reference</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Pair</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right">Rate</TableHead>
                  <TableHead>Deal Date</TableHead>
                  <TableHead>Value Date</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {deals.map(deal => (
                  <TableRow key={deal.id} data-testid={`deal-row-${deal.id}`}>
                    <TableCell className="font-mono text-xs font-medium text-[#08263e]">{deal.reference_number}</TableCell>
                    <TableCell className="text-sm">{deal.transaction_type}</TableCell>
                    <TableCell className="font-mono text-xs">{deal.buy_currency}/{deal.sell_currency}</TableCell>
                    <TableCell className="text-right font-mono text-xs">{Number(deal.amount).toLocaleString()}</TableCell>
                    <TableCell className="text-right font-mono text-xs">{deal.rate}</TableCell>
                    <TableCell className="text-xs">{format(new Date(deal.deal_date + 'T00:00:00'), 'dd MMM yyyy')}</TableCell>
                    <TableCell className="text-xs">{format(new Date(deal.value_date + 'T00:00:00'), 'dd MMM yyyy')}</TableCell>
                    <TableCell><Badge className={STATUS_MAP[deal.status]}>{deal.status}</Badge></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
