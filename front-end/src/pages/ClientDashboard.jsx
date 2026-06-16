import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { authenticatedFetch } from "../config";
import IngestPanel from "../components/features/IngestPanel"; 
import ApiKeyManagement from "../components/features/ApiKeyManagement";
import ChatPreview from "../components/features/ChatPreview";
import DocumentList from "../components/features/DocumentList";
import ProfileModal from "../components/features/ProfileModal";
import ChatbotSettingsPanel from "../components/features/ChatbotSettingsPanel";
import WidgetEmbedPanel from "../components/features/WidgetEmbedPanel";
import UserDataCollectionPanel from "../components/features/UserDataCollectionPanel";
import UserSubmissionsTable from "../components/features/UserSubmissionsTable";
import { LogOut, LayoutGrid, Server, UserCog, Home, Database, MessageSquare, Key, Users, Cpu, Loader2, Calendar, TrendingUp, Bot, Send, X, User as UserIcon, Globe } from "lucide-react";
import ThemeToggle from "../components/ui/ThemeToggle";
import NotificationCenter from "../components/features/NotificationCenter";
import CrawlJobList from "../components/features/CrawlJobList";

export default function ClientDashboard() {
  const { user, logout, setUser } = useAuth();
  const [showProfile, setShowProfile] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");
  const [dashboardStats, setDashboardStats] = useState(null);

  // Fetch dashboard statistics
  useEffect(() => {
    if (activeTab === "overview") {
      fetchDashboardStats();
    }
  }, [activeTab]);

  const fetchDashboardStats = async () => {
    try {
      // Fetch user's storage info which includes document count
      const storageData = await authenticatedFetch("/auth/storage");
      setDashboardStats({
        totalDocuments: storageData.document_count || 0,
        storageMB: storageData.total_mb || 0,
        vectorCount: storageData.vector_count || 0,
        chatSessions: storageData.chat_session_count || 0
      });
    } catch (err) {
      console.error("Failed to fetch dashboard stats:", err);
      setDashboardStats({
        totalDocuments: 0,
        storageMB: 0,
        vectorCount: 0,
        chatSessions: 0
      });
    }
  };

  // Helper to update local user state without page reload
  const handleProfileUpdate = (newData) => {
    // setUser({ ...user, ...newData }); // Enable this if you expose setUser in Context
    window.location.reload(); // Simple fallback: reload to fetch fresh data
  };

return (
    <div className="min-h-screen bg-gray-50 dark:bg-slate-950 transition-colors">
      {/* Top Navigation */}
      <nav className="bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-800 px-6 py-3 flex justify-between items-center sticky top-0 z-50 shadow-sm transition-colors">
        <div className="flex items-center gap-2 text-brand-600 dark:text-brand-400 font-bold text-xl tracking-tight">
          <div className="bg-brand-600 dark:bg-brand-500 text-white p-1.5 rounded-lg transition-colors">
            <LayoutGrid size={20} />
          </div>
          eLanka Chat AI <span className="text-gray-400 dark:text-slate-500 font-normal text-sm ml-1">/ Client</span>
        </div>
        <div className="flex items-center gap-6">
          <div className="hidden md:flex items-center gap-2 text-xs font-medium text-green-600 bg-green-50 dark:bg-green-950 dark:text-green-400 px-3 py-1 rounded-full border border-green-100 dark:border-green-900 transition-colors">
            <Server size={12} /> System Operational
          </div>
          <div className="flex items-center gap-4 pl-6 border-l border-gray-200 dark:border-slate-800 transition-colors">
            <NotificationCenter />
            <ThemeToggle />
            <div className="text-right hidden sm:block">
              <span className="block text-sm font-semibold text-gray-900 dark:text-slate-100 transition-colors">{user?.name}</span>
              <span className="block text-xs text-gray-500 dark:text-slate-400 transition-colors">{user?.email}</span>
            </div>
            
            {/* Profile Button */}
            <button 
              onClick={() => setShowProfile(true)}
              className="p-2 text-gray-400 dark:text-slate-500 hover:text-brand-600 hover:bg-brand-50 dark:hover:bg-slate-800 dark:hover:text-brand-400 rounded-xl transition-all"
              title="Edit Profile"
            >
              <UserCog size={20} />
            </button>

            <button 
              onClick={logout}
              className="p-2 text-gray-400 dark:text-slate-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-slate-800 dark:hover:text-red-400 rounded-xl transition-all"
              title="Logout"
            >
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </nav>

      {/* Tab Navigation */}
      <div className="bg-white dark:bg-slate-900 border-b border-gray-200 dark:border-slate-800 transition-colors">
        <div className="max-w-[1600px] mx-auto px-6">
          <nav className="flex gap-1">
            <TabButton 
              icon={Home} 
              label="Overview" 
              active={activeTab === "overview"} 
              onClick={() => setActiveTab("overview")} 
            />
            <TabButton 
              icon={Database} 
              label="Knowledge Base" 
              active={activeTab === "knowledge"} 
              onClick={() => setActiveTab("knowledge")} 
            />
            <TabButton 
              icon={MessageSquare} 
              label="Chatbot" 
              active={activeTab === "chatbot"} 
              onClick={() => setActiveTab("chatbot")} 
            />
            <TabButton 
              icon={Key} 
              label="API & Integration" 
              active={activeTab === "api"} 
              onClick={() => setActiveTab("api")} 
            />
            <TabButton 
              icon={Users} 
              label="User Data" 
              active={activeTab === "users"} 
              onClick={() => setActiveTab("users")} 
            />
            <TabButton 
              icon={Cpu} 
              label="Token Usage" 
              active={activeTab === "tokens"} 
              onClick={() => setActiveTab("tokens")} 
            />
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-[1600px] mx-auto p-6">
        {activeTab === "overview" && <OverviewTab user={user} stats={dashboardStats} onTabChange={setActiveTab} />}
        {activeTab === "knowledge" && <KnowledgeBaseTab />}
        {activeTab === "chatbot" && <ChatbotTab />}
        {activeTab === "api" && <ApiTab />}
        {activeTab === "users" && <UserDataTab />}
        {activeTab === "tokens" && <TokenUsageTab />}
      </main>

      {/* Profile Modal */}
      {showProfile && (
        <ProfileModal 
          user={user} 
          onClose={() => setShowProfile(false)} 
          onUpdate={handleProfileUpdate} 
        />
      )}
    </div>
  );
}

// Tab Button Component
function TabButton({ icon: Icon, label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-3 font-medium text-sm border-b-2 transition-all ${
        active
          ? "border-brand-600 text-brand-600 dark:text-brand-400 dark:border-brand-400"
          : "border-transparent text-gray-600 dark:text-slate-400 hover:text-gray-900 dark:hover:text-slate-200 hover:bg-gray-50 dark:hover:bg-slate-800"
      }`}
    >
      <Icon size={18} />
      {label}
    </button>
  );
}

// Overview Tab - Dashboard with key metrics and quick actions
function OverviewTab({ user, stats, onTabChange }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white transition-colors">
          Welcome back, {user?.name}!
        </h2>
        <p className="text-gray-600 dark:text-slate-400 transition-colors">
          Here's what's happening with your chatbot today.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard 
          title="Total Documents" 
          value={stats?.totalDocuments || 0} 
          subtitle="Documents indexed" 
          color="blue" 
        />
        <StatCard 
          title="Vector Embeddings" 
          value={stats?.vectorCount || 0} 
          subtitle="Embeddings created" 
          color="green" 
        />
        <StatCard 
          title="Chat Sessions" 
          value={stats?.chatSessions || 0} 
          subtitle="Conversations" 
          color="purple" 
        />
        <StatCard 
          title="Storage Used" 
          value={`${stats?.storageMB?.toFixed(2) || 0} MB`} 
          subtitle="of your storage" 
          color="orange" 
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-6 transition-colors">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 transition-colors">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <QuickActionCard 
            icon={Database} 
            title="Upload Documents" 
            description="Add knowledge to your chatbot"
            color="blue"
            onClick={() => onTabChange("knowledge")}
          />
          <QuickActionCard 
            icon={MessageSquare} 
            title="Test Chatbot" 
            description="Preview your chatbot"
            color="purple"
            onClick={() => onTabChange("chatbot")}
          />
          <QuickActionCard 
            icon={Key} 
            title="Get API Key" 
            description="Integrate with your app"
            color="green"
            onClick={() => onTabChange("api")}
          />
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-6 transition-colors">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 transition-colors">Recent Activity</h3>
        {stats && stats.totalDocuments > 0 ? (
          <div className="space-y-2">
            <p className="text-sm text-gray-600 dark:text-slate-400">
              📄 You have <strong>{stats.totalDocuments}</strong> documents in your knowledge base
            </p>
            <p className="text-sm text-gray-600 dark:text-slate-400">
              💬 <strong>{stats.chatSessions}</strong> chat sessions created
            </p>
            <p className="text-sm text-gray-600 dark:text-slate-400">
              🔢 <strong>{stats.vectorCount}</strong> vector embeddings generated
            </p>
          </div>
        ) : (
          <p className="text-gray-500 dark:text-slate-400 text-center py-8 transition-colors">No recent activity</p>
        )}
      </div>
    </div>
  );
}

// Knowledge Base Tab - Documents and crawlers
function KnowledgeBaseTab() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white transition-colors">Knowledge Base</h2>
        <p className="text-gray-600 dark:text-slate-400 transition-colors">
          Manage your documents and web content
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-2">
          <IngestPanel />
        </div>
        <div className="lg:col-span-3 space-y-6">
          <CrawlJobList />
          <DocumentList />
        </div>
      </div>
    </div>
  );
}

// Chatbot Tab - Settings and floating widget preview
function ChatbotTab() {
  const [liveSettings, setLiveSettings] = useState(null);

  // Load settings so the preview can reflect saved state
  useEffect(() => {
    authenticatedFetch("/chat/settings/chatbot")
      .then(res => {
        // authenticatedFetch returns the parsed JSON directly
        setLiveSettings(res);
      })
      .catch(() => {});
  }, []);

  const handleSettingsSaved = (newSettings) => {
    setLiveSettings(newSettings);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white transition-colors">Chatbot Configuration</h2>
        <p className="text-gray-600 dark:text-slate-400 transition-colors">
          Customize your chatbot's appearance — preview updates live on the right
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 items-start">
        {/* Settings Panel */}
        <div className="lg:col-span-2 space-y-6">
          <ChatbotSettingsPanelWithCallback onSave={handleSettingsSaved} />
        </div>

        {/* Floating Widget Preview */}
        <div className="lg:col-span-3">
          <FloatingWidgetPreview settings={liveSettings} />
        </div>
      </div>
    </div>
  );
}

// Thin wrapper that intercepts save to notify the preview
function ChatbotSettingsPanelWithCallback({ onSave }) {
  return <ChatbotSettingsPanel onSave={onSave} />;
}

// Floating Widget Preview — mimics the actual embedded chat widget
function FloatingWidgetPreview({ settings }) {
  const [isOpen, setIsOpen] = useState(true);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [config, setConfig] = useState({
    chatbot_name: "AI Assistant",
    chatbot_greeting: "Hello! How can I help you today?",
    theme_color: "#EF4444"
  });

  // Reload config whenever parent passes new settings OR on mount
  useEffect(() => {
    const load = () => {
      authenticatedFetch("/chat/settings/chatbot")
        .then(data => {
          setConfig(data);
          setMessages([{ role: "assistant", content: data.chatbot_greeting }]);
        })
        .catch(() => {});
    };
    load();
  }, [settings]); // re-runs when settings prop changes (after save)

  const themeColor = config.theme_color || "#EF4444";

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const userMsg = input;
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setInput("");
    setLoading(true);
    try {
      const res = await authenticatedFetch("/chat/", {
        method: "POST",
        body: JSON.stringify({ message: userMsg, use_history: true })
      });
      setMessages(prev => [...prev, { role: "assistant", content: res.answer }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "assistant", content: "Error: " + err.message }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-2xl border border-gray-200 dark:border-slate-700 overflow-hidden shadow-lg">
      {/* Mock Browser Chrome */}
      <div className="bg-gray-100 dark:bg-slate-800 px-4 py-2.5 flex items-center gap-3 border-b border-gray-200 dark:border-slate-700">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-400" />
          <div className="w-3 h-3 rounded-full bg-yellow-400" />
          <div className="w-3 h-3 rounded-full bg-green-400" />
        </div>
        <div className="flex-1 bg-white dark:bg-slate-700 rounded-full px-3 py-1 flex items-center gap-2">
          <Globe size={12} className="text-gray-400" />
          <span className="text-xs text-gray-400 truncate">yourwebsite.com</span>
        </div>
        <span className="text-xs text-gray-400 font-medium bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400 px-2 py-0.5 rounded-full">Live Preview</span>
      </div>

      {/* Mock Website Content */}
      <div className="relative bg-gradient-to-br from-slate-50 to-gray-100 dark:from-slate-900 dark:to-slate-950 h-[520px] overflow-hidden">
        {/* Fake website placeholder */}
        <div className="p-8 space-y-3 opacity-20 dark:opacity-10 select-none pointer-events-none">
          <div className="h-6 bg-gray-400 rounded w-48" />
          <div className="h-3 bg-gray-300 rounded w-full" />
          <div className="h-3 bg-gray-300 rounded w-5/6" />
          <div className="h-3 bg-gray-300 rounded w-4/6" />
          <div className="mt-6 grid grid-cols-3 gap-4">
            {[1,2,3].map(i => (
              <div key={i} className="h-24 bg-gray-300 rounded-lg" />
            ))}
          </div>
        </div>

        {/* Floating Chat Widget */}
        <div className="absolute bottom-4 right-4 z-10 font-sans">
          {/* Chat Window */}
          <div
            className={`bg-white w-[300px] rounded-2xl shadow-2xl flex flex-col border border-gray-100 overflow-hidden mb-3 transition-all duration-300 origin-bottom-right ${
              isOpen ? "scale-100 opacity-100" : "scale-0 opacity-0 pointer-events-none absolute bottom-0 right-0"
            }`}
            style={{ height: "360px" }}
          >
            {/* Header */}
            <div className="p-3 flex justify-between items-center text-white shrink-0" style={{ backgroundColor: themeColor }}>
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 bg-white/20 rounded-full flex items-center justify-center">
                  <MessageSquare size={14} />
                </div>
                <div>
                  <p className="font-bold text-xs">{config.chatbot_name}</p>
                  <p className="text-[10px] opacity-80 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 bg-green-300 rounded-full inline-block" />
                    Online
                  </p>
                </div>
              </div>
              <button onClick={() => setIsOpen(false)} className="hover:bg-white/10 p-1 rounded transition-colors">
                <X size={14} />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-3 space-y-3 bg-gray-50 text-xs">
              {messages.map((m, i) => (
                <div key={i} className={`flex gap-1.5 ${ m.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 ${
                      m.role === 'user' ? 'bg-gray-200 text-gray-600' : 'text-white'
                    }`}
                    style={m.role !== 'user' ? { backgroundColor: themeColor } : {}}
                  >
                    {m.role === 'user' ? <UserIcon size={10}/> : <MessageSquare size={10}/>}
                  </div>
                  <div
                    className={`px-2.5 py-1.5 rounded-xl max-w-[75%] leading-relaxed ${
                      m.role === 'user' ? 'text-white' : 'bg-white border border-gray-100 text-gray-800'
                    }`}
                    style={m.role === 'user' ? { backgroundColor: themeColor } : {}}
                  >
                    {m.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex gap-1.5">
                  <div className="w-6 h-6 rounded-full flex items-center justify-center text-white" style={{ backgroundColor: themeColor }}>
                    <MessageSquare size={10}/>
                  </div>
                  <div className="px-3 py-2 bg-white border border-gray-100 rounded-xl">
                    <Loader2 size={12} className="animate-spin text-gray-400" />
                  </div>
                </div>
              )}
            </div>

            {/* Input */}
            <div className="p-2 bg-white border-t border-gray-100 shrink-0">
              <form onSubmit={handleSend} className="flex gap-1.5">
                <input
                  className="flex-1 px-3 py-1.5 border border-gray-200 rounded-full text-xs outline-none focus:border-gray-400 transition-colors"
                  placeholder="Type a message..."
                  value={input}
                  onChange={e => setInput(e.target.value)}
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="text-white p-1.5 rounded-full disabled:opacity-50 transition-colors"
                  style={{ backgroundColor: themeColor }}
                >
                  <Send size={12} />
                </button>
              </form>
            </div>
          </div>

          {/* Toggle Bubble */}
          <div className="flex justify-end">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className={`w-12 h-12 text-white rounded-full shadow-xl flex items-center justify-center transition-all hover:scale-110 active:scale-95 ${
                isOpen ? 'rotate-90' : 'rotate-0'
              }`}
              style={{ backgroundColor: themeColor }}
            >
              {isOpen ? <X size={22} /> : <MessageSquare size={22} />}
            </button>
          </div>
        </div>
      </div>

      {/* Caption */}
      <div className="bg-gray-50 dark:bg-slate-800 px-4 py-2 text-xs text-gray-500 dark:text-gray-400 text-center border-t border-gray-200 dark:border-slate-700">
        💡 Save settings above — the preview reflects your latest saved configuration
      </div>
    </div>
  );
}

// API Tab - Keys and integration
function ApiTab() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white transition-colors">API & Integration</h2>
        <p className="text-gray-600 dark:text-slate-400 transition-colors">
          Manage API keys and embed your chatbot
        </p>
      </div>

      <div className="space-y-6">
        <ApiKeyManagement />
        <WidgetEmbedPanel />
      </div>
    </div>
  );
}

// User Data Tab - Collection settings and submissions
function UserDataTab() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white transition-colors">User Data Collection</h2>
        <p className="text-gray-600 dark:text-slate-400 transition-colors">
          Configure data collection and view user submissions
        </p>
      </div>

      <UserDataCollectionPanel />
      <UserSubmissionsTable />
    </div>
  );
}

// Stat Card Component
function StatCard({ title, value, subtitle, color }) {
  const colors = {
    blue: "bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400",
    green: "bg-green-50 text-green-600 dark:bg-green-900/20 dark:text-green-400",
    purple: "bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400",
    orange: "bg-orange-50 text-orange-600 dark:bg-orange-900/20 dark:text-orange-400"
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-6 transition-colors">
      <p className="text-sm text-gray-600 dark:text-slate-400 mb-2 transition-colors">{title}</p>
      <p className="text-3xl font-bold text-gray-900 dark:text-white mb-1 transition-colors">{value}</p>
      <p className="text-xs text-gray-500 dark:text-slate-500 transition-colors">{subtitle}</p>
    </div>
  );
}

// Quick Action Card Component
function QuickActionCard({ icon: Icon, title, description, color, onClick }) {
  const colors = {
    blue: "text-blue-600 bg-blue-50 dark:bg-blue-900/20 dark:text-blue-400",
    green: "text-green-600 bg-green-50 dark:bg-green-900/20 dark:text-green-400",
    purple: "text-purple-600 bg-purple-50 dark:bg-purple-900/20 dark:text-purple-400"
  };

  return (
    <button
      onClick={onClick}
      className="bg-gray-50 dark:bg-slate-800 rounded-lg p-4 hover:bg-gray-100 dark:hover:bg-slate-700 cursor-pointer transition-all border border-gray-200 dark:border-slate-700 w-full text-left"
    >
      <div className={`w-10 h-10 rounded-lg ${colors[color]} flex items-center justify-center mb-3 transition-colors`}>
        <Icon size={20} />
      </div>
      <h4 className="font-semibold text-gray-900 dark:text-white mb-1 transition-colors">{title}</h4>
      <p className="text-sm text-gray-600 dark:text-slate-400 transition-colors">{description}</p>
    </button>
  );
}

function TokenUsageTab() {
  const [days, setDays] = useState(30);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchTokenStats();
  }, [days]);

  const fetchTokenStats = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await authenticatedFetch(`/chat/analytics/token-usage`);
      setStats(data);
    } catch (err) {
      console.error(err);
      setError("Failed to fetch token stats");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="flex justify-center p-12"><Loader2 className="animate-spin text-brand-600" size={32} /></div>;
  if (error) return <div className="p-4 bg-red-50 text-red-600 rounded-lg">{error}</div>;

  const summary = stats || { total_prompt_tokens: 0, total_completion_tokens: 0, total_tokens: 0 };
  const daily = stats?.daily_usage || [];
  const top_sessions = stats?.top_sessions || [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white transition-colors">AI Token Analytics</h2>
          <p className="text-gray-600 dark:text-slate-400 transition-colors">
            Monitor Gemini AI token usage and request patterns
          </p>
        </div>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="px-4 py-2 border border-gray-300 dark:border-slate-700 bg-white dark:bg-slate-900 rounded-lg text-sm text-gray-900 dark:text-white"
        >
          <option value={7}>Last 7 Days</option>
          <option value={30}>Last 30 Days</option>
          <option value={90}>Last 90 Days</option>
        </select>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-gray-200 dark:border-slate-800">
          <p className="text-sm font-medium text-gray-600 dark:text-slate-400">Total Tokens</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{summary.total_tokens.toLocaleString()}</p>
          <span className="text-xs text-brand-600 dark:text-brand-400 flex items-center gap-1 mt-1">
            <TrendingUp size={12} /> Prompt + Completion
          </span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-gray-200 dark:border-slate-800">
          <p className="text-sm font-medium text-gray-600 dark:text-slate-400">Prompt Tokens</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{summary.total_prompt_tokens.toLocaleString()}</p>
          <span className="text-xs text-gray-500 mt-1 block">Context & input messages</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-gray-200 dark:border-slate-800">
          <p className="text-sm font-medium text-gray-600 dark:text-slate-400">Completion Tokens</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{summary.total_completion_tokens.toLocaleString()}</p>
          <span className="text-xs text-gray-500 mt-1 block">AI-generated answers</span>
        </div>
        <div className="bg-white dark:bg-slate-900 p-6 rounded-xl border border-gray-200 dark:border-slate-800">
          <p className="text-sm font-medium text-gray-600 dark:text-slate-400">Top Sessions</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-2">{top_sessions.length}</p>
          <span className="text-xs text-gray-500 mt-1 block">Most active sessions</span>
        </div>
      </div>

      {/* Daily Breakdown */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-gray-200 dark:border-slate-800 p-6">
        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Daily Usage Breakdown</h3>
        {daily.length === 0 ? (
          <div className="text-center py-12 text-gray-500 dark:text-slate-400">
            No token activity recorded in this period.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-gray-200 dark:border-slate-800 text-sm font-medium text-gray-500 dark:text-slate-400">
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4">Total Tokens</th>
                  <th className="py-3 px-4">Prompt Tokens</th>
                  <th className="py-3 px-4">Completion Tokens</th>
                  <th className="py-3 px-4">Relative Volume</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-slate-800">
                {daily.map((day) => {
                  const maxTotal = Math.max(...daily.map(d => d.total_tokens));
                  const percentage = maxTotal > 0 ? (day.total_tokens / maxTotal) * 100 : 0;
                  return (
                    <tr key={day._id} className="text-sm text-gray-900 dark:text-slate-100">
                      <td className="py-3 px-4 flex items-center gap-2">
                        <Calendar size={14} className="text-gray-400" />
                        {day._id}
                      </td>
                      <td className="py-3 px-4 font-semibold">{day.total_tokens.toLocaleString()}</td>
                      <td className="py-3 px-4 text-gray-600 dark:text-slate-400">{(day.prompt_tokens || 0).toLocaleString()}</td>
                      <td className="py-3 px-4 text-gray-600 dark:text-slate-400">{(day.completion_tokens || 0).toLocaleString()}</td>
                      <td className="py-3 px-4 w-1/3">
                        <div className="w-full bg-gray-100 dark:bg-slate-800 h-2.5 rounded-full overflow-hidden">
                          <div
                            className="bg-brand-600 h-full rounded-full"
                            style={{ width: `${percentage}%` }}
                          />
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}