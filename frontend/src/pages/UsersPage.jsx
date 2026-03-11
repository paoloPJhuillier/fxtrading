import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Pencil, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

const ROLE_BADGE = {
  admin: 'bg-purple-100 text-purple-800',
  trader: 'bg-blue-100 text-blue-800',
  treasury: 'bg-teal-100 text-teal-800',
};

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [edit, setEdit] = useState(null);
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'trader' });

  const load = useCallback(async () => {
    try { const r = await api.get('/users'); setUsers(r.data); }
    catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openNew = () => { setEdit(null); setForm({ name: '', email: '', password: '', role: 'trader' }); setOpen(true); };
  const openEdit = (u) => { setEdit(u); setForm({ name: u.name, email: u.email, password: '', role: u.role }); setOpen(true); };

  const save = async () => {
    try {
      if (edit) {
        const payload = { name: form.name, email: form.email, role: form.role };
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

  const del = async (id) => {
    if (!window.confirm('Delete this user?')) return;
    try { await api.delete(`/users/${id}`); toast.success('User deleted'); load(); }
    catch (e) { toast.error('Delete failed'); }
  };

  return (
    <div data-testid="users-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo' }}>User Management</h1>
          <p className="text-sm text-slate-500 mt-1">{users.length} user{users.length !== 1 ? 's' : ''}</p>
        </div>
        <Button className="bg-[#08263e] hover:bg-[#08263e]/90" onClick={openNew} data-testid="add-user-btn">
          <Plus className="h-4 w-4 mr-2" /> Add User
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-32"><div className="animate-spin h-6 w-6 border-4 border-[#518dca] border-t-transparent rounded-full" /></div>
          ) : (
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
                {users.map(u => (
                  <TableRow key={u.id} data-testid={`user-row-${u.id}`}>
                    <TableCell className="font-medium text-sm">{u.name}</TableCell>
                    <TableCell className="text-sm text-slate-500">{u.email}</TableCell>
                    <TableCell>
                      <Badge className={ROLE_BADGE[u.role]}>{u.role === 'treasury' ? 'Treasury Ops' : u.role}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={u.is_active !== false ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                        {u.is_active !== false ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => openEdit(u)} data-testid={`edit-user-${u.id}`}><Pencil className="h-3 w-3" /></Button>
                        <Button size="icon" variant="ghost" className="h-8 w-8 text-red-500 hover:text-red-700" onClick={() => del(u.id)} data-testid={`delete-user-${u.id}`}><Trash2 className="h-3 w-3" /></Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent data-testid="user-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Chivo' }}>{edit ? 'Edit' : 'Add'} User</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label className="text-xs">Name</Label>
              <Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} data-testid="user-name-input" />
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
    </div>
  );
}
