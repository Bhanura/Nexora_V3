import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import SystemStats from "../components/features/SystemStats";
import UserTable from "../components/features/UserTable";
import ActivityLog from "../components/features/ActivityLog";
import SystemHealth from "../components/features/SystemHealth";
import Analytics from "../components/features/Analytics";
import ThemeToggle from "../components/ui/ThemeToggle";
import NotificationCenter from "../components/features/NotificationCenter"; // Add this
import ProfileModal from "../components/features/ProfileModal"; // Add this
import { LogOut, ShieldCheck, RefreshCw, UserPlus, Copy, Check, UserCog, Activity, Heart, BarChart3 } from "lucide-react";
import { authenticatedFetch } from "../config";

export default function SuperAdminDashboard() {
  const { user, logout } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("users"); // New: Tab state
  
  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showNotifyModal, setShowNotifyModal] = useState(null); // holds email string
  const [showProfile, setShowProfile] = useState(false);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await authenticatedFetch("/admin/users");
      setUsers(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchUsers(); }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-black transition-colors">
      <nav className="bg-slate-900 border-b border-slate-800 px-6 py-3 flex justify-between items-center sticky top-0 z-50 shadow-md">
        <div className="flex items-center gap-2 text-white font-bold text-xl tracking-tight">
          <div className="bg-red-600 text-white p-1.5 rounded-lg"><ShieldCheck size={20} /></div>
          eLanka Chat AI <span className="text-red-400 font-normal text-sm ml-1">/ Admin</span>
        </div>
        
        <div className="flex items-center gap-4">
          <NotificationCenter />
          <ThemeToggle />
          <div className="h-6 w-px bg-slate-700 mx-2"></div>
          <div className="text-right hidden sm:block text-slate-300">
             <span className="block text-sm font-semibold text-white">{user?.name}</span>
             <span className="block text-xs opacity-60">Super Admin</span>
          </div>
          
          <button 
            onClick={() => setShowProfile(true)}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-all"
            title="Edit Profile"
          >
            <UserCog size={20} />
          </button>

          <button 
            onClick={logout}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-xl transition-all"
          >
            <LogOut size={20} />
          </button>
        </div>
      </nav>

      <main className="max-w-[1600px] mx-auto p-6 space-y-6">
        <div className="flex justify-between items-end">
          <div>
             <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Platform Overview</h1>
             <p className="text-gray-500 dark:text-gray-400 text-sm">Monitor system health and client activities.</p>
          </div>
          <div className="flex gap-2">
            <button 
               onClick={() => setShowCreateModal(true)}
               className="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 transition-colors"
            >
               <UserPlus size={16} /> New Client
            </button>
            <button 
               onClick={fetchUsers}
               className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-lg text-sm font-medium hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
            >
               <RefreshCw size={16} className={loading ? "animate-spin" : ""} /> Refresh
            </button>
          </div>
        </div>

        <SystemStats users={users} />
        
        {/* Tabs */}
        <div className="flex border-b border-gray-200 dark:border-slate-700 mb-6">
          <button
            onClick={() => setActiveTab("users")}
            className={`px-6 py-3 font-medium transition border-b-2 ${
              activeTab === "users"
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            }`}
          >
            <UserCog size={16} className="inline mr-2" />
            Users
          </button>
          <button
            onClick={() => setActiveTab("activity")}
            className={`px-6 py-3 font-medium transition border-b-2 ${
              activeTab === "activity"
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            }`}
          >
            <Activity size={16} className="inline mr-2" />
            Activity Logs
          </button>
          <button
            onClick={() => setActiveTab("health")}
            className={`px-6 py-3 font-medium transition border-b-2 ${
              activeTab === "health"
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            }`}
          >
            <Heart size={16} className="inline mr-2" />
            System Health
          </button>
          <button
            onClick={() => setActiveTab("analytics")}
            className={`px-6 py-3 font-medium transition border-b-2 ${
              activeTab === "analytics"
                ? "border-brand-600 text-brand-600"
                : "border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            }`}
          >
            <BarChart3 size={16} className="inline mr-2" />
            Analytics
          </button>
        </div>
        
        <div className="min-h-[600px]">
           {activeTab === "users" && (
             <UserTable users={users} onUpdate={fetchUsers} onNotify={(email) => setShowNotifyModal(email)} />
           )}
           {activeTab === "activity" && (
             <ActivityLog />
           )}
           {activeTab === "health" && (
             <SystemHealth />
           )}
           {activeTab === "analytics" && (
             <Analytics />
           )}
        </div>
      </main>

      {/* --- MODALS --- */}
      {showCreateModal && <CreateClientModal onClose={() => setShowCreateModal(false)} onSuccess={fetchUsers} />}
      {showNotifyModal && <NotifyModal email={showNotifyModal} onClose={() => setShowNotifyModal(null)} />}
      {showProfile && (
        <ProfileModal 
          user={user} 
          onClose={() => setShowProfile(false)} 
          onUpdate={() => window.location.reload()} 
        />
      )}
    </div>
  );
}

// --- SUB-COMPONENTS (Can be in same file for now) ---

function CreateClientModal({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({ email: "", name: "" });
  const [result, setResult] = useState(null);
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await authenticatedFetch("/admin/client", { method: "POST", body: JSON.stringify(formData) });
      setResult(res);
      onSuccess();
    } catch (err) { alert(err.message); }
  };

  const copyPass = () => {
    navigator.clipboard.writeText(result.temporary_password);
    setCopied(true);
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl p-6 w-full max-w-md">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Onboard New Client</h3>
        
        {!result ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <input type="text" placeholder="Company Name" required className="w-full p-2 border rounded dark:bg-slate-800 dark:border-slate-700 dark:text-white" onChange={e => setFormData({...formData, name: e.target.value})} />
            <input type="email" placeholder="Email" required className="w-full p-2 border rounded dark:bg-slate-800 dark:border-slate-700 dark:text-white" onChange={e => setFormData({...formData, email: e.target.value})} />
            <div className="flex gap-2 justify-end pt-2">
              <button type="button" onClick={onClose} className="px-4 py-2 text-gray-500 hover:text-gray-700">Cancel</button>
              <button className="px-4 py-2 bg-brand-600 text-white rounded hover:bg-brand-700">Create Account</button>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            <div className="p-3 bg-green-50 text-green-800 rounded border border-green-200 text-sm">
              User created! Send these details securely.
            </div>
            <div className="space-y-1">
              <p className="text-xs text-gray-500 uppercase">Temporary Password</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 p-2 bg-slate-100 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700 font-mono text-lg select-all">
                  {result.temporary_password}
                </code>
                <button onClick={copyPass} className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded">{copied ? <Check size={16} className="text-green-600"/> : <Copy size={16}/>}</button>
              </div>
            </div>
            <button onClick={onClose} className="w-full py-2 bg-slate-900 dark:bg-slate-700 text-white rounded">Done</button>
          </div>
        )}
      </div>
    </div>
  );
}

function NotifyModal({ email, onClose }) {
  const [msg, setMsg] = useState("");
  const handleSend = async (e) => {
    e.preventDefault();
    await authenticatedFetch("/admin/notify", { method: "POST", body: JSON.stringify({ email, message: msg, type: "info" }) });
    alert("Notification Sent!"); onClose();
  };
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-white dark:bg-slate-900 p-6 rounded-xl w-full max-w-md">
        <h3 className="font-bold dark:text-white mb-2">Message to {email}</h3>
        <form onSubmit={handleSend}>
          <textarea className="w-full p-2 border rounded mb-4 dark:bg-slate-800 dark:border-slate-700 dark:text-white" rows={4} onChange={e => setMsg(e.target.value)} placeholder="Type notification..."></textarea>
          <div className="flex justify-end gap-2">
             <button type="button" onClick={onClose} className="px-3 py-1 text-gray-500">Cancel</button>
             <button className="px-3 py-1 bg-brand-600 text-white rounded">Send</button>
          </div>
        </form>
      </div>
    </div>
  )
}