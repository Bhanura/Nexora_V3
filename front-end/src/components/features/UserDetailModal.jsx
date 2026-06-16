import { useState, useEffect } from "react";
import { X, User, Settings, FileText, Key, HardDrive, Trash2, Calendar, Mail, Shield, Activity } from "lucide-react";
import { authenticatedFetch } from "../../config";
import ActivityLog from "./ActivityLog";

export default function UserDetailModal({ userId, onClose, onUpdate }) {
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState("info");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUserDetails();
  }, [userId]);

  const fetchUserDetails = async () => {
    try {
      setLoading(true);
      const response = await authenticatedFetch(`/admin/user/${userId}/details`);
      setData(response);
    } catch (err) {
      console.error("Failed to fetch user details:", err);
    } finally {
      setLoading(false);
    }
  };

  const deleteDocument = async (docId) => {
    if (!confirm("Delete this document? This will also remove its vectors from Qdrant.")) return;
    try {
      await authenticatedFetch(`/admin/user/${userId}/document/${docId}`, {
        method: "DELETE"
      });
      fetchUserDetails();
      if (onUpdate) onUpdate();
    } catch (err) {
      alert(err.message);
    }
  };

  const revokeApiKey = async (keyId) => {
    if (!confirm("Revoke this API key? This action cannot be undone. The user will be notified.")) return;
    try {
      await authenticatedFetch(`/admin/user/${userId}/api-key/${keyId}/revoke`, {
        method: "POST"
      });
      fetchUserDetails();
      if (onUpdate) onUpdate();
    } catch (err) {
      alert(err.message);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
        <div className="bg-white dark:bg-slate-900 rounded-xl p-8">
          <p className="text-gray-600 dark:text-gray-300">Loading...</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const tabs = [
    { id: "info", label: "User Info", icon: User },
    { id: "widget", label: "Widget Settings", icon: Settings },
    { id: "documents", label: `Documents (${data.documents.length})`, icon: FileText },
    { id: "api-keys", label: `API Keys (${data.api_keys.length})`, icon: Key },
    { id: "storage", label: "Storage", icon: HardDrive },
    { id: "activity", label: "Activity", icon: Activity }
  ];

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-slate-700 flex justify-between items-center bg-gradient-to-r from-purple-50 to-blue-50 dark:from-slate-800 dark:to-slate-900">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-brand-500 to-purple-600 text-white flex items-center justify-center font-bold text-lg">
              {data.user.name?.charAt(0).toUpperCase() || "U"}
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                {data.user.name || "Unnamed User"}
              </h2>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Mail size={12} />
                {data.user.email}
                <span className={`ml-2 px-2 py-0.5 rounded text-xs ${
                  data.user.status === 'banned' ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                }`}>
                  {data.user.status || 'active'}
                </span>
              </div>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="p-2 hover:bg-gray-200 dark:hover:bg-slate-700 rounded-lg transition"
          >
            <X size={20} className="text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 dark:border-slate-700 px-6 bg-gray-50 dark:bg-slate-900/50">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition text-sm font-medium ${
                activeTab === tab.id
                  ? "border-brand-600 text-brand-600 dark:text-brand-400"
                  : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
              }`}
            >
              <tab.icon size={16} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === "info" && <InfoTab user={data.user} chatSessions={data.chat_sessions} />}
          {activeTab === "widget" && <WidgetTab settings={data.chatbot_settings} />}
          {activeTab === "documents" && <DocumentsTab documents={data.documents} onDelete={deleteDocument} />}
          {activeTab === "api-keys" && <ApiKeysTab keys={data.api_keys} onRevoke={revokeApiKey} />}
          {activeTab === "storage" && <StorageTab storage={data.storage} />}
          {activeTab === "activity" && <ActivityLog userId={userId} />}
        </div>
      </div>
    </div>
  );
}

// ==================== TAB COMPONENTS ====================

function InfoTab({ user, chatSessions }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <InfoCard label="User ID" value={user._id} icon={Shield} />
        <InfoCard label="Role" value={user.role?.replace('_', ' ') || 'client'} icon={User} />
        <InfoCard label="Member Since" value={user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'} icon={Calendar} />
        <InfoCard label="Last Login" value={user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'} icon={Calendar} />
        <InfoCard label="Total Logins" value={user.login_count || 0} />
        <InfoCard label="Chat Sessions" value={chatSessions.length} />
      </div>

      <div>
        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Recent Chat Sessions</h3>
        <div className="space-y-2">
          {chatSessions.slice(0, 5).map(session => (
            <div key={session._id} className="p-3 bg-gray-50 dark:bg-slate-800 rounded-lg">
              <div className="flex justify-between items-start">
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Session ID: {session._id.slice(-8)}
                  </p>
                  <p className="text-xs text-gray-500">
                    Messages: {session.messages?.length || 0}
                  </p>
                </div>
                <p className="text-xs text-gray-400">
                  {session.created_at ? new Date(session.created_at).toLocaleDateString() : 'N/A'}
                </p>
              </div>
            </div>
          ))}
          {chatSessions.length === 0 && (
            <p className="text-sm text-gray-500 italic">No chat sessions yet</p>
          )}
        </div>
      </div>
    </div>
  );
}

function WidgetTab({ settings }) {
  if (!settings || Object.keys(settings).length === 0) {
    return (
      <div className="text-center py-12">
        <Settings size={48} className="mx-auto text-gray-300 dark:text-gray-600 mb-3" />
        <p className="text-gray-500 dark:text-gray-400">No widget customization configured</p>
        <p className="text-sm text-gray-400 dark:text-gray-500 mt-1">User hasn't customized their chatbot yet</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Appearance */}
      <Section title="Appearance">
        <div className="grid grid-cols-2 gap-4">
          <SettingRow label="Chatbot Name" value={settings.chatbot_name || "eLanka Chat AI Assistant"} />
          <SettingRow label="Primary Color" value={
            <div className="flex items-center gap-2">
              <div 
                className="w-6 h-6 rounded border border-gray-300" 
                style={{ backgroundColor: settings.primary_color || "#7C3AED" }}
              />
              <span>{settings.primary_color || "#7C3AED"}</span>
            </div>
          } />
          <SettingRow label="Theme" value={settings.theme || "light"} />
          <SettingRow label="Position" value={settings.position || "bottom-right"} />
        </div>
      </Section>

      {/* Messages */}
      <Section title="Messages & Greetings">
        <div className="space-y-3">
          <SettingRow label="Welcome Message" value={settings.chatbot_greeting || "Welcome! How can I help you today?"} />
          <SettingRow label="Placeholder Text" value={settings.placeholder_text || "Type your message..."} />
        </div>
      </Section>

      {/* Personality */}
      <Section title="Personality & Behavior">
        <div className="space-y-3">
          <SettingRow label="Personality" value={settings.chatbot_personality || "friendly and helpful"} />
          <SettingRow label="Temperature" value={settings.temperature || 0.7} />
          <SettingRow label="Max Response Length" value={settings.max_tokens || 500} />
        </div>
      </Section>

      {/* Features */}
      <Section title="Features">
        <div className="grid grid-cols-2 gap-4">
          <SettingRow label="Show Branding" value={settings.show_branding !== false ? "✓ Yes" : "✗ No"} />
          <SettingRow label="Allow File Upload" value={settings.allow_file_upload ? "✓ Yes" : "✗ No"} />
          <SettingRow label="Enable Voice" value={settings.enable_voice ? "✓ Yes" : "✗ No"} />
          <SettingRow label="Enable Feedback" value={settings.enable_feedback !== false ? "✓ Yes" : "✗ No"} />
        </div>
      </Section>
    </div>
  );
}

function DocumentsTab({ documents, onDelete }) {
  if (documents.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText size={48} className="mx-auto text-gray-300 dark:text-gray-600 mb-3" />
        <p className="text-gray-500 dark:text-gray-400">No documents uploaded</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {documents.map(doc => (
        <div key={doc._id} className="flex justify-between items-center p-4 bg-gray-50 dark:bg-slate-800 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700 transition">
          <div className="flex-1">
            <p className="font-medium text-gray-900 dark:text-white">{doc.filename}</p>
            <div className="flex gap-4 text-xs text-gray-500 mt-1">
              <span>{((doc.file_size || 0) / 1024).toFixed(2)} KB</span>
              <span>Uploaded: {doc.uploaded_at ? new Date(doc.uploaded_at).toLocaleDateString() : 'N/A'}</span>
              <span className={`px-2 py-0.5 rounded ${
                doc.status === 'completed' ? 'bg-green-100 text-green-700' : 
                doc.status === 'processing' ? 'bg-yellow-100 text-yellow-700' : 
                'bg-red-100 text-red-700'
              }`}>
                {doc.status || 'unknown'}
              </span>
            </div>
          </div>
          <button
            onClick={() => onDelete(doc._id)}
            className="ml-4 p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition"
            title="Delete document"
          >
            <Trash2 size={16} />
          </button>
        </div>
      ))}
    </div>
  );
}

function ApiKeysTab({ keys, onRevoke }) {
  if (keys.length === 0) {
    return (
      <div className="text-center py-12">
        <Key size={48} className="mx-auto text-gray-300 dark:text-gray-600 mb-3" />
        <p className="text-gray-500 dark:text-gray-400">No API keys generated</p>
      </div>
    );
  }

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

  return (
    <div className="space-y-3">
      {keys.map(key => (
        <div key={key._id} className="p-4 bg-gray-50 dark:bg-slate-800 rounded-lg">
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <p className="font-medium text-gray-900 dark:text-white">
                  {key.name || "API Key"}
                </p>
                {getStatusBadge(key.status)}
              </div>
              <p className="font-mono text-sm text-gray-600 dark:text-gray-400 mb-2">
                {key.key_prefix}
              </p>
              <div className="flex gap-4 text-xs text-gray-500">
                <span>Created: {key.created_at ? new Date(key.created_at).toLocaleDateString() : 'N/A'}</span>
                {key.last_used && (
                  <span>Last used: {new Date(key.last_used).toLocaleDateString()}</span>
                )}
                {key.revoked_at && (
                  <span className="text-red-600">Revoked: {new Date(key.revoked_at).toLocaleDateString()}</span>
                )}
              </div>
            </div>
            {key.status === "active" && (
              <button
                onClick={() => onRevoke(key._id)}
                className="ml-4 px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition"
              >
                Revoke
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function StorageTab({ storage }) {
  const breakdown = storage.breakdown || {};
  
  return (
    <div className="space-y-6">
      {/* Total Storage */}
      <div className="p-6 bg-gradient-to-br from-purple-50 to-blue-50 dark:from-slate-800 dark:to-slate-900 rounded-xl border border-purple-200 dark:border-purple-900">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Total Storage Used</p>
            <p className="text-4xl font-bold text-purple-600 dark:text-purple-400 mt-1">
              {storage.total_mb} MB
            </p>
          </div>
          <HardDrive size={48} className="text-purple-400" />
        </div>
      </div>

      {/* Breakdown Cards */}
      <div className="grid grid-cols-2 gap-4">
        <StorageCard label="Documents" value={breakdown.documents || "0.00 MB"} color="blue" />
        <StorageCard label="Vectors (Qdrant)" value={breakdown.vectors || "0.00 MB"} color="purple" />
        <StorageCard label="Chat History" value={breakdown.chats || "0.00 MB"} color="green" />
        <StorageCard label="Crawled Data" value={breakdown.crawls || "0.00 MB"} color="orange" />
        <StorageCard label="Form Submissions" value={breakdown.submissions || "0.00 MB"} color="pink" />
        <StorageCard label="Metadata" value={breakdown.metadata || "0.00 MB"} color="gray" />
      </div>

      {/* Detailed Stats */}
      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-slate-700">
        <StatRow label="Vector Count" value={storage.vector_count?.toLocaleString() || 0} />
        <StatRow label="Documents" value={storage.document_count || 0} />
        <StatRow label="Chat Sessions" value={storage.chat_session_count || 0} />
        <StatRow label="Crawl Jobs" value={storage.crawl_job_count || 0} />
      </div>
    </div>
  );
}

// ==================== UTILITY COMPONENTS ====================

function Section({ title, children }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 pb-2 border-b border-gray-200 dark:border-slate-700">
        {title}
      </h3>
      {children}
    </div>
  );
}

function SettingRow({ label, value }) {
  return (
    <div className="flex justify-between py-2">
      <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
      <span className="text-sm font-medium text-gray-900 dark:text-white">{value}</span>
    </div>
  );
}

function InfoCard({ label, value, icon: Icon }) {
  return (
    <div className="p-4 bg-gray-50 dark:bg-slate-800 rounded-lg">
      {Icon && <Icon size={16} className="text-gray-400 mb-2" />}
      <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
      <p className="text-lg font-semibold text-gray-900 dark:text-white mt-1">{value}</p>
    </div>
  );
}

function StorageCard({ label, value, color }) {
  const colorClasses = {
    blue: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-800",
    purple: "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-900/20 dark:text-purple-400 dark:border-purple-800",
    green: "bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400 dark:border-green-800",
    orange: "bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-900/20 dark:text-orange-400 dark:border-orange-800",
    pink: "bg-pink-50 text-pink-700 border-pink-200 dark:bg-pink-900/20 dark:text-pink-400 dark:border-pink-800",
    gray: "bg-gray-50 text-gray-700 border-gray-200 dark:bg-gray-900/20 dark:text-gray-400 dark:border-gray-800"
  };

  return (
    <div className={`p-4 rounded-lg border ${colorClasses[color]}`}>
      <p className="text-xs opacity-80 mb-1">{label}</p>
      <p className="text-lg font-bold">{value}</p>
    </div>
  );
}

function StatRow({ label, value }) {
  return (
    <div className="flex justify-between items-center py-2">
      <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
      <span className="text-sm font-semibold text-gray-900 dark:text-white">{value}</span>
    </div>
  );
}
