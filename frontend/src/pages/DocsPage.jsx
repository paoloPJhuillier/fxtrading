import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Download, FileText, FileSpreadsheet, Archive } from 'lucide-react';
import { toast } from 'sonner';

const TYPE_ICON = { pdf: FileText, docx: FileText, xlsx: FileSpreadsheet, md: FileText };
const TYPE_COLOR = { pdf: 'bg-red-100 text-red-700', docx: 'bg-blue-100 text-blue-700', xlsx: 'bg-emerald-100 text-emerald-700', md: 'bg-slate-100 text-slate-600' };

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

// Group files by document name (without extension)
function groupFiles(files) {
  const groups = {};
  for (const f of files) {
    const base = f.name.replace(/\.(pdf|docx|xlsx|md)$/, '');
    if (!groups[base]) groups[base] = { name: base, files: [] };
    groups[base].files.push(f);
  }
  return Object.values(groups);
}

export default function DocsPage() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(null);

  useEffect(() => {
    api.get('/documentation/list')
      .then(r => setFiles(r.data))
      .catch(() => toast.error('Failed to load documentation'))
      .finally(() => setLoading(false));
  }, []);

  const downloadFile = async (filename) => {
    setDownloading(filename);
    try {
      const r = await api.get(`/documentation/download/${filename}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a'); a.href = url; a.download = filename;
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(url);
    } catch { toast.error('Download failed'); }
    finally { setDownloading(null); }
  };

  const downloadAll = async () => {
    setDownloading('__all__');
    try {
      const r = await api.get('/documentation/download-all', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a'); a.href = url; a.download = 'FX_Trading_Tracker_Documentation.zip';
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(url);
    } catch { toast.error('Download failed'); }
    finally { setDownloading(null); }
  };

  const groups = groupFiles(files);

  return (
    <div data-testid="docs-page">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-[#08263e]" style={{ fontFamily: 'Chivo' }}>Documentation</h1>
          <p className="text-sm text-slate-500 mt-1">Download project documentation — BRD, SRS, User Manual, and more</p>
        </div>
        <Button onClick={downloadAll} disabled={downloading === '__all__' || files.length === 0} className="bg-[#08263e] hover:bg-[#08263e]/90" data-testid="download-all-btn">
          <Archive className="h-4 w-4 mr-2" />
          {downloading === '__all__' ? 'Preparing ZIP...' : 'Download All (ZIP)'}
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40"><div className="animate-spin h-6 w-6 border-4 border-[#518dca] border-t-transparent rounded-full" /></div>
      ) : groups.length === 0 ? (
        <p className="text-center py-12 text-slate-400">No documentation files found.</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {groups.map(g => (
            <Card key={g.name} className="hover:shadow-md transition-shadow" data-testid={`doc-group-${g.name}`}>
              <CardContent className="p-5">
                <h3 className="font-semibold text-sm text-[#08263e] mb-3 leading-tight" style={{ fontFamily: 'Chivo' }}>
                  {g.name.replace(/_/g, ' ')}
                </h3>
                <div className="space-y-2">
                  {g.files.map(f => {
                    const Icon = TYPE_ICON[f.type] || FileText;
                    return (
                      <div key={f.name} className="flex items-center justify-between gap-2 group">
                        <div className="flex items-center gap-2 min-w-0">
                          <Badge className={`${TYPE_COLOR[f.type] || 'bg-slate-100 text-slate-600'} text-[10px] px-1.5 py-0 uppercase font-mono`}>{f.type}</Badge>
                          <span className="text-xs text-slate-500">{formatSize(f.size)}</span>
                        </div>
                        <Button size="sm" variant="ghost" className="h-7 px-2 text-[#518dca] hover:text-[#08263e] opacity-70 group-hover:opacity-100"
                          onClick={() => downloadFile(f.name)} disabled={downloading === f.name} data-testid={`download-${f.name}`}>
                          <Download className="h-3.5 w-3.5 mr-1" />
                          {downloading === f.name ? '...' : 'Download'}
                        </Button>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
