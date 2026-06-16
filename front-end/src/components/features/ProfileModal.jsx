import { useState } from "react";
import { X, User, Mail, Save, Loader2, Lock } from "lucide-react";
import { authenticatedFetch } from "../../config";
import { cn } from "../../lib/utils";

export default function ProfileModal({ user, onClose, onUpdate }) {
  const [tab, setTab] = useState("details"); // 'details' | 'password'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Form States
  const [profileData, setProfileData] = useState({ name: user.name, email: user.email });
  const [passData, setPassData] = useState("");

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      await authenticatedFetch("/auth/me", {
        method: "PUT",
        body: JSON.stringify(profileData)
      });
      onUpdate(profileData); // Update global context locally
      setError(""); // Clear any previous errors
      
      // Show success and close after delay
      setTimeout(() => {
        onClose();
      }, 1500);
      
      // Show success message
      setError("Profile updated successfully! Closing...");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      await authenticatedFetch("/auth/password", { 
        method: "PUT", 
        body: JSON.stringify({ new_password: passData }) 
      });
      
      // Clear password field on success
      setPassData("");
      
      // Show success message
      setError("Password changed successfully!");
    } catch (err) { 
      setError(err.message); 
    } finally { 
      setLoading(false); 
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl w-full max-w-md overflow-hidden transform transition-all scale-100">
        
        {/* Header with Tabs */}
        <div className="px-6 py-4 border-b border-gray-100 dark:border-slate-800 flex flex-col bg-gray-50 dark:bg-slate-800">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold text-gray-900 dark:text-white">Edit Profile</h3>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors">
              <X size={20} />
            </button>
          </div>
          
          {/* Tabs */}
          <div className="flex border-b border-gray-100 dark:border-slate-700 -mx-6 -mb-4">
            <button 
              onClick={() => setTab("details")} 
              className={cn(
                "flex-1 py-3 text-sm font-medium", 
                tab === "details" 
                  ? "text-brand-600 dark:text-brand-400 border-b-2 border-brand-600 dark:border-brand-400" 
                  : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
              )}
            >
              Details
            </button>
            <button 
              onClick={() => setTab("password")} 
              className={cn(
                "flex-1 py-3 text-sm font-medium", 
                tab === "password" 
                  ? "text-brand-600 dark:text-brand-400 border-b-2 border-brand-600 dark:border-brand-400" 
                  : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
              )}
            >
              Password
            </button>
          </div>
        </div>

        {/* Form Content */}
        <div className="p-6">
          {error && (
            <div className={`mb-4 p-3 text-sm rounded ${error.includes("success") ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'}`}>
              {error}
            </div>
          )}

          {/* DETAILS FORM */}
          {tab === "details" && (
            <form onSubmit={handleProfileSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-1">Full Name</label>
                <div className="relative">
                  <User className="absolute left-3 top-2.5 text-gray-400 dark:text-gray-500" size={16} />
                  <input 
                    type="text" 
                    required 
                    value={profileData.name} 
                    onChange={(e) => setProfileData({...profileData, name: e.target.value})} 
                    className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-slate-700 rounded-lg text-sm dark:bg-slate-800 dark:text-white focus:ring-2 focus:ring-brand-500 dark:focus:ring-brand-400 outline-none"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-1">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 text-gray-400 dark:text-gray-500" size={16} />
                  <input 
                    type="email" 
                    required 
                    value={profileData.email} 
                    onChange={(e) => setProfileData({...profileData, email: e.target.value})} 
                    className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-slate-700 rounded-lg text-sm dark:bg-slate-800 dark:text-white focus:ring-2 focus:ring-brand-500 dark:focus:ring-brand-400 outline-none"
                  />
                </div>
              </div>

              <div className="pt-4 flex gap-3">
                <button 
                  type="button" 
                  onClick={onClose}
                  className="flex-1 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-slate-800 rounded-lg hover:bg-gray-200 dark:hover:bg-slate-700 transition-colors"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  disabled={loading}
                  className="flex-1 py-2 text-sm font-medium text-white bg-brand-600 rounded-lg hover:bg-brand-700 flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
                >
                  {loading ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
                  Save Changes
                </button>
              </div>
            </form>
          )}

          {/* PASSWORD FORM */}
          {tab === "password" && (
            <form onSubmit={handlePasswordSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase mb-1">New Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 text-gray-400 dark:text-gray-500" size={16} />
                  <input 
                    type="password" 
                    required 
                    value={passData} 
                    onChange={(e) => setPassData(e.target.value)} 
                    className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-slate-700 rounded-lg text-sm dark:bg-slate-800 dark:text-white focus:ring-2 focus:ring-brand-500 dark:focus:ring-brand-400 outline-none"
                    placeholder="Minimum 8 characters"
                  />
                </div>
              </div>

              <div className="pt-4 flex gap-3">
                <button 
                  type="button" 
                  onClick={() => {
                    setTab("details");
                    setPassData("");
                  }}
                  className="flex-1 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-slate-800 rounded-lg hover:bg-gray-200 dark:hover:bg-slate-700 transition-colors"
                >
                  Back
                </button>
                <button 
                  type="submit" 
                  disabled={loading || !passData}
                  className="flex-1 py-2 text-sm font-medium text-white bg-slate-900 dark:bg-slate-700 rounded-lg hover:bg-slate-800 dark:hover:bg-slate-600 flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
                >
                  {loading ? <Loader2 className="animate-spin" size={16} /> : <Lock size={16} />}
                  Update Password
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}