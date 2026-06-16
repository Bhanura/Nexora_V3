import { useState } from "react";
import { MoreVertical, Shield, ShieldOff, Trash2, Search, Mail, Download, CheckSquare, Square } from "lucide-react";
import { authenticatedFetch } from "../../config";
import { Card, CardContent } from "../ui/Card";
import { MessageSquare } from "lucide-react";
import UserDetailModal from "./UserDetailModal";

export default function UserTable({ users, onUpdate, onNotify }) {
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState("");
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [selectedUsers, setSelectedUsers] = useState(new Set());
  const [showBulkActions, setShowBulkActions] = useState(false);

  // Actions
  const handleBan = async (email, currentStatus) => {
    const action = currentStatus === 'banned' ? 'unban' : 'ban';
    if (!confirm(`Are you sure you want to ${action.toUpperCase()} this user?`)) return;

    setLoading(true);
    try {
      await authenticatedFetch(`/admin/${action}`, {
        method: "POST",
        body: JSON.stringify({ email })
      });
      onUpdate(); // Refresh list
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (email) => {
    const msg = "⚠️ DANGER: This will delete the user AND all their documents/bots.\nThis action is irreversible.\n\nType 'DELETE' to confirm.";
    const confirmation = prompt(msg);
    if (confirmation !== "DELETE") return;

    setLoading(true);
    try {
      // DELETE request with Query Parameter
      await authenticatedFetch(`/admin/client?email=${encodeURIComponent(email)}`, {
        method: "DELETE"
      });
      onUpdate();
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Bulk actions
  const toggleUserSelection = (userId) => {
    const newSelection = new Set(selectedUsers);
    if (newSelection.has(userId)) {
      newSelection.delete(userId);
    } else {
      newSelection.add(userId);
    }
    setSelectedUsers(newSelection);
    setShowBulkActions(newSelection.size > 0);
  };

  const selectAll = () => {
    setSelectedUsers(new Set(filteredUsers.map(u => u.id)));
    setShowBulkActions(true);
  };

  const clearSelection = () => {
    setSelectedUsers(new Set());
    setShowBulkActions(false);
  };

  const handleBulkBan = async () => {
    if (!confirm(`Ban ${selectedUsers.size} selected users?`)) return;
    setLoading(true);
    try {
      await authenticatedFetch("/admin/bulk/ban", {
        method: "POST",
        body: JSON.stringify({ user_ids: Array.from(selectedUsers), action: "ban" })
      });
      clearSelection();
      onUpdate();
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkDelete = async () => {
    if (!confirm(`PERMANENTLY DELETE ${selectedUsers.size} users and ALL their data? This cannot be undone!`)) return;
    setLoading(true);
    try {
      await authenticatedFetch("/admin/bulk/delete", {
        method: "POST",
        body: JSON.stringify({ user_ids: Array.from(selectedUsers) })
      });
      clearSelection();
      onUpdate();
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      const response = await fetch("/api/admin/export/users", {
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("token")}`
        }
      });
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "users_export.csv";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Export failed: " + err.message);
    }
  };

  // Filtering Logic
  const filteredUsers = users.filter(u => 
    u.email.toLowerCase().includes(filter.toLowerCase()) || 
    u.name.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <Card className="flex flex-col h-full border-gray-200 dark:border-slate-800 shadow-sm">
      {/* Header / Search */}
      <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white dark:bg-slate-900 rounded-t-xl">
        <div className="flex items-center gap-4">
          <h3 className="font-semibold text-gray-900 dark:text-gray-100">Client Directory</h3>
          {showBulkActions && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">{selectedUsers.size} selected</span>
              <button
                onClick={clearSelection}
                className="text-xs text-gray-500 hover:text-gray-700 underline"
              >
                Clear
              </button>
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {showBulkActions && (
            <>
              <button
                onClick={handleBulkBan}
                disabled={loading}
                className="flex items-center gap-2 px-3 py-2 bg-orange-600 text-white rounded-lg text-sm hover:bg-orange-700 transition disabled:opacity-50"
              >
                <ShieldOff size={14} /> Ban Selected
              </button>
              <button
                onClick={handleBulkDelete}
                disabled={loading}
                className="flex items-center gap-2 px-3 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 transition disabled:opacity-50"
              >
                <Trash2 size={14} /> Delete Selected
              </button>
            </>
          )}
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-2 px-3 py-2 bg-gray-600 text-white rounded-lg text-sm hover:bg-gray-700 transition"
          >
            <Download size={14} /> Export CSV
          </button>
          <div className="relative">
            <Search className="absolute left-3 top-2.5 text-gray-400" size={16} />
            <input 
              type="text" placeholder="Search users..."
              value={filter} onChange={(e) => setFilter(e.target.value)}
              className="pl-9 pr-4 py-2 border border-gray-200 dark:border-slate-700 rounded-lg text-sm bg-gray-50 dark:bg-slate-800 focus:ring-2 focus:ring-brand-500 outline-none w-full sm:w-64"
            />
          </div>
        </div>
      </div>

      <CardContent className="p-0 flex-1 overflow-auto bg-white dark:bg-slate-950 custom-scrollbar">
        <table className="w-full text-left border-collapse">
          <thead className="bg-gray-50/50 dark:bg-slate-900/50 text-gray-500 dark:text-gray-400 sticky top-0 z-10 backdrop-blur-sm text-xs uppercase font-semibold">
            <tr>
              <th className="px-6 py-3 w-12">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    selectedUsers.size === filteredUsers.length ? clearSelection() : selectAll();
                  }}
                  className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                >
                  {selectedUsers.size === filteredUsers.length && filteredUsers.length > 0 ? (
                    <CheckSquare size={18} />
                  ) : (
                    <Square size={18} />
                  )}
                </button>
              </th>
              <th className="px-6 py-3">Client</th>
              <th className="px-6 py-3">Role</th>
              <th className="px-6 py-3">Usage</th>
              <th className="px-6 py-3">Storage</th>
              <th className="px-6 py-3">Last Activity</th>
              <th className="px-6 py-3 text-center">Status</th>
              <th className="px-6 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50 dark:divide-slate-800">
            {filteredUsers.map((u) => (
              <tr 
                key={u.id} 
                onClick={() => setSelectedUserId(u.id)}
                className="hover:bg-gray-50 dark:hover:bg-slate-900 transition-colors group cursor-pointer"
              >
                <td className="px-6 py-4" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => toggleUserSelection(u.id)}
                    className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                  >
                    {selectedUsers.has(u.id) ? (
                      <CheckSquare size={18} className="text-brand-600" />
                    ) : (
                      <Square size={18} />
                    )}
                  </button>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-500 to-purple-600 text-white flex items-center justify-center font-bold text-xs">
                      {u.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-200">{u.name}</p>
                      <p className="text-xs text-gray-500 flex items-center gap-1">
                        <Mail size={10} /> {u.email}
                      </p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400 capitalize">
                  <span className={`px-2 py-1 rounded text-xs border ${u.role === 'super_admin' ? 'bg-purple-50 text-purple-700 border-purple-100' : 'bg-gray-100 text-gray-700 border-gray-200'}`}>
                    {u.role.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm font-mono text-gray-600 dark:text-gray-400">
                   {u.doc_count} Docs
                </td>
                <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                  <div className="flex flex-col">
                    <span className="font-medium text-gray-900 dark:text-white">
                      {u.storage_mb ? u.storage_mb.toFixed(2) : '0.00'} MB
                    </span>
                    <span className="text-xs text-gray-400">
                      {u.doc_count} {u.doc_count === 1 ? 'doc' : 'docs'}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">
                  {u.last_login 
                    ? new Date(u.last_login).toLocaleDateString('en-US', { 
                        month: 'short', 
                        day: 'numeric', 
                        year: 'numeric' 
                      })
                    : <span className="text-gray-400 italic">Never</span>
                  }
                </td>
                <td className="px-6 py-4 text-center">
                  {u.status === 'banned' ? (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                      Banned
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Active
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 text-right flex justify-end gap-2 opacity-60 group-hover:opacity-100 transition-opacity" onClick={(e) => e.stopPropagation()}>
                   {u.role !== 'super_admin' && (
                     <>

                        <button
                            onClick={() => onNotify(u.email)} // Calls the prop function
                            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded"
                            title="Send Notification"
                        >
                        <MessageSquare size={16} />
                        </button>
                        <button
                          onClick={() => handleBan(u.email, u.status)}
                          disabled={loading}
                          className="p-1.5 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded"
                          title={u.status === 'banned' ? "Unban User" : "Ban User"}
                        >
                          {u.status === 'banned' ? <Shield size={16} /> : <ShieldOff size={16} />}
                        </button>
                        <button
                          onClick={() => handleDelete(u.email)}
                          disabled={loading}
                          className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded"
                          title="Delete Client & Data"
                        >
                          <Trash2 size={16} />
                        </button>
                     </>
                   )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>

      {/* User Detail Modal */}
      {selectedUserId && (
        <UserDetailModal 
          userId={selectedUserId} 
          onClose={() => setSelectedUserId(null)}
          onUpdate={onUpdate}
        />
      )}
    </Card>
  );
}