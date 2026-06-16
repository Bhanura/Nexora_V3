import { useState, useEffect } from "react";
import { Key, Copy, RefreshCw, Check } from "lucide-react";
import { authenticatedFetch } from "../../config";
import { Card, CardHeader, CardContent } from "../ui/Card";

export default function ApiKeyPanel() {
  const [apiKey, setApiKey] = useState("");
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);

  const fetchKey = async () => {
    setLoading(true);
    try {
      // POST to generate or retrieve existing key
      const res = await authenticatedFetch("/auth/api-key", { method: "POST" });
      setApiKey(res.key);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchKey(); }, []);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card>
      <CardHeader title="Widget Integration" description="Use this key in your website HTML." icon={Key} />
      <CardContent>
        <div className="flex items-center gap-2 p-3 bg-slate-900 rounded-lg group relative">
          <code className="flex-1 font-mono text-sm text-green-400 truncate">
            {apiKey || "Loading key..."}
          </code>
          
          <button onClick={copyToClipboard} className="text-gray-400 hover:text-white p-1">
            {copied ? <Check size={18} className="text-green-500" /> : <Copy size={18} />}
          </button>
        </div>
        
        <div className="mt-4 flex justify-end">
          <button 
            onClick={fetchKey} 
            disabled={loading}
            className="text-xs text-gray-500 hover:text-brand-600 flex items-center gap-1"
          >
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} /> Regenerate Key
          </button>
        </div>
      </CardContent>
    </Card>
  );
}