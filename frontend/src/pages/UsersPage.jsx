import { useState, useEffect, useCallback, useRef, memo } from 'react';
import api from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Pencil, Trash2, ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { toast } from 'sonner';

const ROLE_BADGE = {
  admin: 'bg-purple-100 text-purple-800',
  trader: 'bg-blue-100 text-blue-800',
  treasury: 'bg-teal-100 text-teal-800',
};
const PAGE_SIZE = 20;

export default function UsersPage() {
  const [data, setData] = useState({ users: [], total: 0, page: 1, pages: 1 });
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [edit, setEdit] = useState(null);
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', role: 'trader' });

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search), 250);
    return () => clearTimeout(t);
  }, [search]);

  const hasLoaded = useRef(false);
  const load = useCallback(async (signal) => {
    if (!hasLoaded.current) setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', page);
      params.append('limit', PAGE_SIZE);
      if (debouncedSearch) params.append('search', debouncedSearch);
      const r = await api.get(`/users?${params.toString()}`, { signal });
      setData(r.data);
      hasLoaded.current = true;
    } catch (e) { if (!signal?.aborted) console.error(e); }
    finally { if (!signal?.aborted) setLoading(false); }
  }, [page, debouncedSearch]);

  useEffect(() => {
    const c = new AbortController();
    load(c.signal);
    return () => c.abort();
  }, [load]);

  const openNew = () => { setEdit(null); setForm({ first_name: '', last_name: '', email: '', password: '', role: 'trader' }); setOpen(true); };
  const openEdit = useCallback((u) => { setEdit(u); setForm({ first_name: u.first_name || '', last_name: u.last_name || '', email: u.email, password: '', role: u.role }); setOpen(true); }, []);

  const save = async () => {
    try {
      if (edit) {
        const payload = { first_name: form.first_name, last_name: form.last_name, email: form.email, role: form.role };
        if (form.password) payload.password = form.password;
        await api.put(`/users/${edit.id}`, payload);
        toast.success('User updated');
      } else {
        if (!form.password) { toast.error('Password required'); return; }
        await api.post('/users', form);
        toast.success('User created');
      }
      setOpen(false); load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Save failed'); }
  };

  const del = useCallback(async (id) => {
    if (!window.confirm('Delete this user?')) return;
    try { await api.delete(`/users/${id}`); toast.success('User deleted'); load(); }
    catch (e) { toast.error('Delete failed'); }
  }, [load]);

  return (
    <div data-testid="users-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo' }}>User Management</h1>
          <p className="text-sm text-slate-500 mt-1">{data.total} user{data.total !== 1 ? 's' : ''}</p>
        </div>
        <div className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <Input className="h-9 pl-8 w-48 text-xs" placeholder="Search users..." value={search} onChange={e => { setSearch(e.target.value); setPage(1); }} data-testid="search-users-input" />
          </div>
          <Button className="bg-[#08263e] hover:bg-[#08263e]/90" onClick={openNew} data-testid="add-user-btn">
            <Plus className="h-4 w-4 mr-2" /> Add User
          </Button>
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading && data.users.length === 0 ? (
            <div className="flex items-center justify-center h-32"><div className="animate-spin h-6 w-6 border-4 border-[#518dca] border-t-transparent rounded-full" /></div>
          ) : (
            <div className={loading ? 'opacity-60 pointer-events-none transition-opacity' : 'transition-opacity'}>
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.users.map(u => (
                  <UserRow key={u.id} user={u} onEdit={openEdit} onDelete={del} />
                ))}
              </TableBody>
            </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {data.pages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-xs text-slate-400">Page {data.page} of {data.pages} ({data.total} users)</p>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" disabled={page <= 1} onClick={() => setPage(p => p - 1)} data-testid="users-prev-page">
              <ChevronLeft className="h-3.5 w-3.5 mr-1" /> Previous
            </Button>
            <Button size="sm" variant="outline" disabled={page >= data.pages} onClick={() => setPage(p => p + 1)} data-testid="users-next-page">
              Next <ChevronRight className="h-3.5 w-3.5 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {open && (
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent data-testid="user-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Chivo' }}>{edit ? 'Edit' : 'Add'} User</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs">First Name</Label>
                <Input value={form.first_name} onChange={e => setForm({ ...form, first_name: e.target.value })} data-testid="user-first-name-input" />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs">Last Name</Label>
                <Input value={form.last_name} onChange={e => setForm({ ...form, last_name: e.target.value })} data-testid="user-last-name-input" />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Email</Label>
              <Input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} data-testid="user-email-input" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">{edit ? 'New Password (leave blank to keep)' : 'Password'}</Label>
              <Input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} data-testid="user-password-input" />
            </div>
            <div className="space-y-1.5">
              <Label className="text-xs">Role</Label>
              <Select value={form.role} onValueChange={v => setForm({ ...form, role: v })}>
                <SelectTrigger data-testid="user-role-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="trader">Trader</SelectItem>
                  <SelectItem value="treasury">Treasury Operations</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)} data-testid="user-cancel-btn">Cancel</Button>
            <Button className="bg-[#08263e] hover:bg-[#08263e]/90" onClick={save} data-testid="user-save-btn">Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      )}
    </div>
  );
}

const UserRow = memo(function UserRow({ user, onEdit, onDelete }) {
  return (
    <TableRow data-testid={`user-row-${user.id}`}>
      <TableCell className="font-medium text-sm">{`${user.first_name || ''} ${user.last_name || ''}`.trim() || user.name}</TableCell>
      <TableCell className="text-sm text-slate-500">{user.email}</TableCell>
      <TableCell>
        <Badge className={ROLE_BADGE[user.role]}>{user.role === 'treasury' ? 'Treasury Ops' : user.role}</Badge>
      </TableCell>
      <TableCell>
        <Badge className={user.is_active !== false ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
          {user.is_active !== false ? 'Active' : 'Inactive'}
        </Badge>
      </TableCell>
      <TableCell className="text-right">
        <div className="flex justify-end gap-1">
          <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => onEdit(user)} data-testid={`edit-user-${user.id}`}><Pencil className="h-3 w-3" /></Button>
          <Button size="icon" variant="ghost" className="h-8 w-8 text-red-500 hover:text-red-700" onClick={() => onDelete(user.id)} data-testid={`delete-user-${user.id}`}><Trash2 className="h-3 w-3" /></Button>
        </div>
      </TableCell>
    </TableRow>
  );
});
