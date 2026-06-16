import { useState, useEffect } from "react";
import { FileText, Trash2, ExternalLink, RefreshCw, AlertCircle, FileDigit, Loader2 } from "lucide-react";
import { authenticatedFetch } from "../../config";
import { Card, CardContent } from "../ui/Card";

export default function DocumentList() {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  const fetchDocs = async () => {
    setLoading(true);
    try {
      // FIX: Changed endpoint from /system/documents to /documents
      const data = await authenticatedFetch("/documents?page_size=50");
      setDocs(data.documents);
      setError("");
    } catch (err) {
      console.error(err);
      setError("Failed to load documents.");
    } finally {
      setLoading(false);
    }
  };

// --- Single Delete ---
  const handleDelete = async (docId) => {
    if (!confirm("Are you sure you want to delete this document?")) return;
    setDocs(prev => prev.filter(d => d.id !== docId));
    try {
      await authenticatedFetch(`/documents/by-source?source_url=${encodeURIComponent(docId)}`, { method: "DELETE" });
    } catch (err) {
      alert("Failed to delete item.");
      fetchDocs();
    }
  };

// --- DELETE ALL LOGIC ---
  const handleDeleteAll = async () => {
    if (docs.length === 0) return;
    const confirmMsg = `⚠️ DANGER ZONE ⚠️\n\nAre you sure you want to delete ALL ${docs.length} documents?\nThis action cannot be undone.`;
    if (!confirm(confirmMsg)) return;

    setDeleting(true);
    setError("");

    try {
      await authenticatedFetch("/documents/all?confirm=true", { method: "DELETE" });
      setDocs([]); // Clear UI immediately
      alert("All documents have been deleted.");
    } catch (err) {
      setError("An error occurred while deleting documents.");
      fetchDocs();
    } finally {
      setDeleting(false);
    }
  };

  useEffect(() => { fetchDocs(); }, []);

return (
    <Card className="h-full flex flex-col border-gray-200 dark:border-slate-800 shadow-sm">
      <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-800 flex items-center justify-between bg-white dark:bg-slate-900 rounded-t-xl transition-colors">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-50 dark:bg-blue-900/20 text-brand-600 dark:text-brand-400 rounded-lg">
            <FileText size={18} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">Knowledge Base</h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">{docs.length} documents indexed</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* DELETE ALL BUTTON */}
          {docs.length > 0 && (
            <button
              onClick={handleDeleteAll}
              disabled={deleting}
              className="px-3 py-1.5 text-xs font-medium text-red-600 hover:text-white border border-red-200 hover:bg-red-600 dark:border-red-900/50 dark:text-red-400 dark:hover:bg-red-900 rounded-lg transition-all flex items-center gap-2"
            >
              {deleting ? <Loader2 size={12} className="animate-spin" /> : <Trash2 size={12} />}
              Delete All
            </button>
          )}

          <button 
            onClick={fetchDocs} 
            className="p-1.5 hover:bg-gray-100 dark:hover:bg-slate-800 rounded-full text-gray-400 hover:text-brand-600 dark:hover:text-brand-400 transition-colors"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      <CardContent className="p-0 flex-1 overflow-hidden flex flex-col bg-white dark:bg-slate-950">
        {error && (
          <div className="m-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-xs rounded-lg flex items-center gap-2 border border-red-100 dark:border-red-900/50">
            <AlertCircle size={14} /> {error}
          </div>
        )}

        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {docs.length === 0 && !loading ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-400 dark:text-gray-600">
              <FileDigit size={40} className="mb-3 opacity-10" />
              <p className="text-sm">No documents found</p>
            </div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead className="bg-gray-50/50 dark:bg-slate-900/50 text-gray-500 dark:text-gray-400 sticky top-0 z-10 backdrop-blur-sm">
                <tr>
                  <th className="px-6 py-3 text-xs font-semibold uppercase tracking-wider">Source</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider">Chunks</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider">Size</th>
                  <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider">Date Fed</th>
                  <th className="px-6 py-3 text-center text-xs font-semibold uppercase tracking-wider"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50 dark:divide-slate-800">
                {docs.map((doc) => (
                    <tr key={doc.id} className="hover:bg-blue-50/30 dark:hover:bg-blue-900/10 group transition-colors">
                      <td className="px-6 py-3 max-w-[200px]">
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-200 truncate" title={doc.title}>
                          {doc.title || "Untitled"}
                        </div>
                        <a 
                          href={doc.url} 
                          target="_blank" 
                          rel="noreferrer"
                          className="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1 hover:text-brand-600 dark:hover:text-brand-400 truncate mt-0.5"
                        >
                          <ExternalLink size={10} /> {doc.url}
                        </a>
                      </td>
                      <td className="px-6 py-3 text-right text-xs text-gray-500 dark:text-gray-400 font-mono">
                        {doc.chunk_count}
                      </td>
                      <td className="px-6 py-3 text-right text-xs text-gray-500 dark:text-gray-400 font-mono">
                        {(doc.total_characters / 1000).toFixed(1)}k
                      </td>
                      <td className="px-6 py-3 text-right text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap">
                        {doc.created_at
                          ? new Date(doc.created_at).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
                          : doc.ingested_at
                          ? new Date(doc.ingested_at).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
                          : '—'
                        }
                      </td>
                      <td className="px-6 py-3 text-center">
                        <button
                          onClick={() => handleDelete(doc.id)}
                          className="p-1.5 text-gray-300 dark:text-gray-600 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-all opacity-0 group-hover:opacity-100"
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </CardContent>
    </Card>
  );
}