import { useState, useEffect } from "react";
import { Key, Copy, RefreshCw, Check, Trash2, Plus, Edit2, Eye, EyeOff, AlertCircle } from "lucide-react";
import { authenticatedFetch } from "../../config";
import { Card, CardHeader, CardContent } from "../ui/Card";

export default function ApiKeyManagement() {
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState(null);
  const [visibleKeys, setVisibleKeys] = useState({});
  const [copiedKey, setCopiedKey] = useState(null);
  const [selectedEditKey, setSelectedEditKey] = useState(null);

  const fetchApiKeys = async () => {
    setLoading(true);
    try {
      const keys = await authenticatedFetch("/auth/api-keys");
      setApiKeys(keys);
    } catch (err) {
      console.error("Failed to fetch API keys:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const createApiKey = async () => {
    if (!newKeyName.trim()) {
      alert("Please enter a name for the API key");
      return;
    }

    try {
      const result = await authenticatedFetch("/auth/api-keys", {
        method: "POST",
        body: JSON.stringify({ name: newKeyName })
      });
      setCreatedKey(result);
      setNewKeyName("");
      setShowCreateModal(false);
      fetchApiKeys();
    } catch (err) {
      alert(err.message || "Failed to create API key");
    }
  };

  const deleteApiKey = async (keyId, keyName) => {
    if (!confirm(`Delete API key "${keyName}"? This action cannot be undone.`)) return;

    try {
      await authenticatedFetch(`/auth/api-keys/${keyId}`, { method: "DELETE" });
      fetchApiKeys();
    } catch (err) {
      alert(err.message || "Failed to delete API key");
    }
  };

  const regenerateApiKey = async (keyId, keyName) => {
    if (!confirm(`Regenerate API key "${keyName}"? The old key will stop working immediately.`)) return;

    try {
      const result = await authenticatedFetch(`/auth/api-keys/${keyId}/regenerate`, {
        method: "POST"
      });
      setCreatedKey(result);
      fetchApiKeys();
    } catch (err) {
      alert(err.message || "Failed to regenerate API key");
    }
  };

  const toggleKeyVisibility = async (keyId) => {
    if (visibleKeys[keyId]) {
      // Hide the key
      setVisibleKeys({ ...visibleKeys, [keyId]: null });
    } else {
      // Fetch and show the key
      try {
        const keyDetails = await authenticatedFetch(`/auth/api-keys/${keyId}`);
        setVisibleKeys({ ...visibleKeys, [keyId]: keyDetails.key });
      } catch (err) {
        alert("Failed to fetch key details");
      }
    }
  };

  const copyToClipboard = (text, keyId) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(keyId);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const getStatusBadge = (status) => {
    if (status === "active") {
      return (
        <span className="px-2 py-1 text-xs rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400">
          Active
        </span>
      );
    } else if (status === "revoked") {
      return (
        <span className="px-2 py-1 text-xs rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400">
          Revoked
        </span>
      );
    }
    return null;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "Never";
    return new Date(dateStr).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  return (
    <Card>
      <CardHeader 
        title="API Key Management" 
        description="Create and manage API keys for widget integration" 
        icon={Key} 
      />
      <CardContent>
        {/* Create New Key Button */}
        <div className="mb-4 flex justify-between items-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            You can create up to 5 API keys. Active keys: {apiKeys.filter(k => k.status === "active").length}
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            disabled={apiKeys.length >= 5}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white rounded-lg transition-colors text-sm"
          >
            <Plus size={16} />
            Create New Key
          </button>
        </div>

        {/* Newly Created Key Display */}
        {createdKey && (
          <div className="mb-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
            <div className="flex items-start gap-2 mb-2">
              <AlertCircle size={20} className="text-green-600 dark:text-green-400 mt-0.5" />
              <div className="flex-1">
                <h4 className="font-semibold text-green-900 dark:text-green-100 mb-1">
                  API Key Created Successfully!
                </h4>
                <p className="text-sm text-green-700 dark:text-green-300 mb-2">
                  Save this key now - you won't be able to see it again.
                </p>
                <div className="flex items-center gap-2 p-3 bg-slate-900 rounded-lg">
                  <code className="flex-1 font-mono text-sm text-green-400 break-all">
                    {createdKey.key}
                  </code>
                  <button
                    onClick={() => copyToClipboard(createdKey.key, "new")}
                    className="text-gray-400 hover:text-white p-1 shrink-0"
                  >
                    {copiedKey === "new" ? (
                      <Check size={18} className="text-green-500" />
                    ) : (
                      <Copy size={18} />
                    )}
                  </button>
                </div>
              </div>
              <button
                onClick={() => setCreatedKey(null)}
                className="text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-200"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {/* API Keys Table */}
        {loading ? (
          <p className="text-center py-8 text-gray-500">Loading...</p>
        ) : apiKeys.length === 0 ? (
          <div className="text-center py-12 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg">
            <Key size={48} className="mx-auto text-gray-400 mb-3" />
            <p className="text-gray-500 dark:text-gray-400 mb-4">No API keys created yet</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors text-sm"
            >
              Create Your First API Key
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">Name</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">Key</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">Created</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">Last Used</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700 dark:text-gray-300">Actions</th>
                </tr>
              </thead>
              <tbody>
                {apiKeys.map((key) => (
                  <tr key={key.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className="py-3 px-4">
                      <div className="flex flex-col">
                        <span className="font-medium text-gray-900 dark:text-white">{key.name}</span>
                        {key.allowed_domains && key.allowed_domains.length > 0 ? (
                          <span className="text-xs text-purple-600 dark:text-purple-400 truncate max-w-[200px]" title={key.allowed_domains.join(", ")}>
                            Domains: {key.allowed_domains.join(", ")}
                          </span>
                        ) : (
                          <span className="text-xs text-gray-400 dark:text-gray-500 italic">All domains allowed</span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        {visibleKeys[key.id] ? (
                          <code className="text-sm font-mono text-gray-700 dark:text-gray-300 break-all">
                            {visibleKeys[key.id]}
                          </code>
                        ) : (
                          <code className="text-sm font-mono text-gray-500">
                            {key.key_prefix}
                          </code>
                        )}
                        <button
                          onClick={() => toggleKeyVisibility(key.id)}
                          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                          title={visibleKeys[key.id] ? "Hide key" : "Show key"}
                        >
                          {visibleKeys[key.id] ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                        {visibleKeys[key.id] && (
                          <button
                            onClick={() => copyToClipboard(visibleKeys[key.id], key.id)}
                            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                          >
                            {copiedKey === key.id ? (
                              <Check size={16} className="text-green-500" />
                            ) : (
                              <Copy size={16} />
                            )}
                          </button>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">{getStatusBadge(key.status)}</td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                      {formatDate(key.created_at)}
                    </td>
                    <td className="py-3 px-4 text-sm text-gray-600 dark:text-gray-400">
                      {formatDate(key.last_used)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-2">
                        {key.status === "active" && (
                          <button
                            onClick={() => setSelectedEditKey(key)}
                            className="p-1.5 text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded transition-colors"
                            title="Edit domains and name"
                          >
                            <Edit2 size={16} />
                          </button>
                        )}
                        {key.status === "active" && (
                          <button
                            onClick={() => regenerateApiKey(key.id, key.name)}
                            className="p-1.5 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
                            title="Regenerate"
                          >
                            <RefreshCw size={16} />
                          </button>
                        )}
                        {key.status === "active" && (
                          <button
                            onClick={() => deleteApiKey(key.id, key.name)}
                            className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                            title="Delete"
                          >
                            <Trash2 size={16} />
                          </button>
                        )}
                        {key.status === "revoked" && (
                          <span className="text-xs text-gray-500 italic">Revoked by admin</span>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Create API Key Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="bg-white dark:bg-slate-900 rounded-xl p-6 w-full max-w-md shadow-2xl">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Create New API Key</h3>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Key Name
                </label>
                <input
                  type="text"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="e.g., Production Website, Testing Environment"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-slate-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 outline-none"
                />
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Choose a descriptive name to identify where this key will be used.
                </p>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={createApiKey}
                  className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
                >
                  Create Key
                </button>
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewKeyName("");
                  }}
                  className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Edit API Key Modal */}
        {selectedEditKey && (
          <EditApiKeyModal
            apiKey={selectedEditKey}
            onClose={() => setSelectedEditKey(null)}
            onSave={fetchApiKeys}
          />
        )}
      </CardContent>
    </Card>
  );
}

function EditApiKeyModal({ apiKey, onClose, onSave }) {
  const [name, setName] = useState(apiKey.name);
  const [domainsText, setDomainsText] = useState((apiKey.allowed_domains || []).join("\n"));
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const domains = domainsText
        .split("\n")
        .map(d => d.trim())
        .filter(d => d.length > 0);

      await authenticatedFetch(`/auth/api-keys/${apiKey.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          name,
          allowed_domains: domains
        })
      });
      onSave();
      onClose();
    } catch (err) {
      alert(err.message || "Failed to update API key");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-slate-900 rounded-xl p-6 w-full max-w-md shadow-2xl">
        <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Edit API Key Settings</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Key Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-slate-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Whitelisted Domains
            </label>
            <textarea
              value={domainsText}
              onChange={(e) => setDomainsText(e.target.value)}
              placeholder="e.g.&#10;elanka.com&#10;*.example.com&#10;localhost"
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-slate-800 text-gray-900 dark:text-white font-mono text-sm focus:ring-2 focus:ring-purple-500 outline-none"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Enter one domain per line. Wildcards are supported. Leave empty to allow all domains.
            </p>
          </div>
          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              disabled={saving}
              className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white rounded-lg transition-colors text-sm"
            >
              {saving ? "Saving..." : "Save Changes"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-lg transition-colors text-sm"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
