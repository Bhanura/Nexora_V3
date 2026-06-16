import { useState, useEffect } from "react";
import { Save, Loader2, CheckCircle, Sparkles } from "lucide-react";
import { authenticatedFetch } from "../../config";
import Card from "../ui/Card";

export default function ChatbotSettingsPanel({ onSave } = {}) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [settings, setSettings] = useState({
    chatbot_name: "",
    chatbot_greeting: "",
    chatbot_personality: "",
    theme_color: "#EF4444"
  });

  // Load current settings when component mounts
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const data = await authenticatedFetch("/chat/settings/chatbot");
      setSettings(data);
    } catch (err) {
      console.error("Failed to load settings:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSuccess(false);
    
    try {
      const saved = await authenticatedFetch("/chat/settings/chatbot", {
        method: "PUT",
        body: JSON.stringify(settings)
      });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
      // Notify parent (live preview) with the newly saved settings
      if (onSave) onSave(saved || settings);
    } catch (err) {
      alert("Error saving settings: " + err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card>
      <div className="flex items-center gap-2 mb-4">
        <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
          <Sparkles size={20} className="text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">
            Chatbot Identity
          </h2>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Customize how your chatbot presents itself to visitors
          </p>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-8">
          <Loader2 className="animate-spin text-gray-400" size={32} />
        </div>
      ) : (
        <form onSubmit={handleSave} className="space-y-4">
          {/* Chatbot Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Chatbot Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={settings.chatbot_name}
              onChange={(e) => setSettings({...settings, chatbot_name: e.target.value})}
              placeholder="e.g., TechSupport Pro"
              required
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-800 dark:text-white"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Visitors will see this name in the chat widget header
            </p>
          </div>

          {/* Greeting Message */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Greeting Message <span className="text-red-500">*</span>
            </label>
            <textarea
              value={settings.chatbot_greeting}
              onChange={(e) => setSettings({...settings, chatbot_greeting: e.target.value})}
              placeholder="e.g., Welcome to TechCorp! How can we assist you today?"
              rows={3}
              required
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-800 dark:text-white resize-none"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              First message visitors see when opening the widget
            </p>
          </div>

          {/* Personality */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Personality Traits <span className="text-red-500">*</span>
            </label>
            <textarea
              value={settings.chatbot_personality}
              onChange={(e) => setSettings({...settings, chatbot_personality: e.target.value})}
              placeholder="e.g., professional, concise, and technical"
              rows={2}
              required
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-800 dark:text-white resize-none"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Describes how the bot should communicate (e.g., friendly, professional, casual)
            </p>
          </div>

          {/* Custom Theme Color */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Widget Theme Color
            </label>
            <div className="flex items-center gap-3">
              <input
                type="color"
                value={settings.theme_color || "#EF4444"}
                onChange={(e) => setSettings({...settings, theme_color: e.target.value})}
                className="w-10 h-10 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer bg-transparent"
              />
              <input
                type="text"
                value={settings.theme_color || "#EF4444"}
                onChange={(e) => setSettings({...settings, theme_color: e.target.value})}
                placeholder="#EF4444"
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 dark:bg-gray-800 dark:text-white font-mono"
              />
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Select or type a hex color for the widget header, send button, and accents.
            </p>
          </div>

          {/* Example Suggestions */}
          <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-900 rounded-lg p-3">
            <p className="text-xs font-medium text-blue-900 dark:text-blue-300 mb-2">💡 Personality Examples:</p>
            <ul className="text-xs text-blue-700 dark:text-blue-400 space-y-1">
              <li>• "friendly and helpful"</li>
              <li>• "professional and concise"</li>
              <li>• "casual and enthusiastic"</li>
              <li>• "technical and detailed"</li>
            </ul>
          </div>

          {/* Save Button */}
          <button
            type="submit"
            disabled={saving}
            className="w-full flex items-center justify-center gap-2 bg-purple-600 hover:bg-purple-700 dark:bg-purple-700 dark:hover:bg-purple-600 text-white font-medium py-2.5 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Saving...
              </>
            ) : success ? (
              <>
                <CheckCircle size={16} />
                Saved Successfully!
              </>
            ) : (
              <>
                <Save size={16} />
                Save Settings
              </>
            )}
          </button>
        </form>
      )}
    </Card>
  );
}
