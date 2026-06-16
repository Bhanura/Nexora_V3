import { useState, useEffect } from "react";
import { Bell, X, Check } from "lucide-react";
import { authenticatedFetch } from "../../config";

export default function NotificationCenter() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const unreadCount = notifications.filter(n => !n.read).length;

  const fetchNotes = async () => {
    try {
      const data = await authenticatedFetch("/notifications/");
      setNotifications(data);
    } catch (e) { console.error(e); }
  };

  const markRead = async (id) => {
    try {
      await authenticatedFetch(`/notifications/${id}/read`, { method: "PUT" });
      setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
    } catch (e) { console.error(e); }
  };

  // Poll every 60 seconds
  useEffect(() => { 
    fetchNotes(); 
    const interval = setInterval(fetchNotes, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 text-gray-400 hover:text-brand-600 relative transition-colors"
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border border-white"></span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-xl shadow-xl z-50 overflow-hidden animate-fade-in">
          <div className="p-3 border-b border-gray-100 dark:border-slate-800 bg-gray-50 dark:bg-slate-950 flex justify-between items-center">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white">Notifications</h4>
            <button onClick={() => setIsOpen(false)}><X size={14} className="text-gray-400" /></button>
          </div>
          <div className="max-h-64 overflow-y-auto">
            {notifications.length === 0 ? (
              <p className="p-4 text-xs text-center text-gray-400">No messages</p>
            ) : (
              notifications.map(note => (
                <div key={note.id} className={`p-3 border-b border-gray-50 dark:border-slate-800 text-sm ${note.read ? 'opacity-50' : 'bg-blue-50/30 dark:bg-blue-900/10'}`}>
                  <p className="text-gray-800 dark:text-gray-200">{note.message}</p>
                  <div className="mt-2 flex justify-between items-center">
                    <span className="text-[10px] text-gray-400">{new Date(note.created_at).toLocaleDateString()}</span>
                    {!note.read && (
                      <button onClick={() => markRead(note.id)} className="text-xs text-brand-600 hover:underline flex items-center gap-1">
                        <Check size={10} /> Mark read
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}