import { useState, useEffect } from "react";
import { Code, Copy, Check, ExternalLink, Download, Globe, Blocks } from "lucide-react";
import { Card, CardHeader, CardContent } from "../ui/Card";

export default function WidgetEmbedPanel() {
  const [apiKeys, setApiKeys] = useState([]);
  const [selectedKey, setSelectedKey] = useState("");
  const [copied, setCopied] = useState(false);
  const [copiedExternal, setCopiedExternal] = useState(false);
  const [framework, setFramework] = useState("html"); // 'html', 'react', 'nextjs'

  useEffect(() => {
    // Fetch all API keys
    fetchApiKeys();
  }, []);

  const fetchApiKeys = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/auth/api-keys", {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const activeKeys = data.filter(k => k.status === "active");
        setApiKeys(activeKeys);
        if (activeKeys.length > 0) {
          setSelectedKey(activeKeys[0]._id);
        }
      }
    } catch (err) {
      console.error("Failed to fetch API keys:", err);
    }
  };

  const getSelectedKeyValue = async () => {
    if (!selectedKey) return "YOUR_API_KEY_HERE";
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(`/api/auth/api-keys/${selectedKey}`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        return data.key;
      }
    } catch (err) {
      console.error("Failed to fetch key details:", err);
    }
    return "YOUR_API_KEY_HERE";
  };

  const embedCodeCDN = async () => {
    const apiKey = await getSelectedKeyValue();
    return `<!-- Option 2: Load widget from eLanka Chat AI server (Recommended) -->
<script>
  (function() {
    var script = document.createElement('script');
    script.src = '${window.location.origin}/widget.iife.js';
    script.onload = function() {
      window.eLankaChatAIWidget.init('${apiKey}', {
        apiUrl: '${window.location.origin}/api'
      });
    };
    document.body.appendChild(script);
  })();
</script>`;
  };

  const embedCodeSelfHosted = async () => {
    const apiKey = await getSelectedKeyValue();
    return `<!-- Option 1: Self-hosted widget -->
<!-- 1. Download widget.iife.js from your dashboard -->
<!-- 2. Upload it to your website's directory -->
<!-- 3. Add this code: -->
<script src="/path/to/widget.iife.js"></script>
<script>
  window.eLankaChatAIWidget.init('${apiKey}', {
    apiUrl: '${window.location.origin}/api'  // Your eLanka Chat AI server URL
  });
</script>`;
  };

  const handleCopySelfHosted = async () => {
    const code = await embedCodeSelfHosted();
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyCDN = async () => {
    const code = await embedCodeCDN();
    navigator.clipboard.writeText(code);
    setCopiedExternal(true);
    setTimeout(() => setCopiedExternal(false), 2000);
  };

  const handleDownloadWidget = () => {
    window.open('/widget.iife.js', '_blank');
  };

  const getReactSnippet = async () => {
    const apiKey = await getSelectedKeyValue();
    return `import { useEffect } from 'react';

export default function ChatWidget() {
  useEffect(() => {
    // Prevent multiple injections
    if (document.getElementById('elanka-chat-widget')) return;

    const script = document.createElement('script');
    script.id = 'elanka-chat-widget';
    script.src = '${window.location.origin}/widget.iife.js';
    script.async = true;
    script.onload = () => {
      if (window.eLankaChatAIWidget) {
        window.eLankaChatAIWidget.init('${apiKey}', {
          apiUrl: '${window.location.origin}/api'
        });
      }
    };
    document.body.appendChild(script);
  }, []);

  return null;
}`;
  };

  const getNextjsSnippet = async () => {
    const apiKey = await getSelectedKeyValue();
    return `'use client';

import Script from 'next/script';

export default function ChatWidget() {
  return (
    <Script 
      src="${window.location.origin}/widget.iife.js" 
      strategy="afterInteractive"
      onLoad={() => {
        if (window.eLankaChatAIWidget) {
          window.eLankaChatAIWidget.init('${apiKey}', {
            apiUrl: '${window.location.origin}/api'
          });
        }
      }}
    />
  );
}`;
  };

  const handleCopyReact = async () => {
    const code = await getReactSnippet();
    navigator.clipboard.writeText(code);
    setCopiedExternal(true);
    setTimeout(() => setCopiedExternal(false), 2000);
  };

  const handleCopyNextjs = async () => {
    const code = await getNextjsSnippet();
    navigator.clipboard.writeText(code);
    setCopiedExternal(true);
    setTimeout(() => setCopiedExternal(false), 2000);
  };

  return (
    <Card className="bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950 dark:to-emerald-950 border-green-200 dark:border-green-800 transition-colors">
      <CardHeader>
        <div className="flex items-center gap-2">
          <Code className="w-5 h-5 text-green-600 dark:text-green-400" />
          <h3 className="font-semibold text-lg text-gray-900 dark:text-white">Embed Widget on Website</h3>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* API Key Selector */}
        {apiKeys.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Select API Key to use:
            </label>
            <select
              value={selectedKey}
              onChange={(e) => setSelectedKey(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 dark:bg-gray-800 dark:text-white"
            >
              {apiKeys.map(key => (
                <option key={key._id} value={key._id}>
                  {key.name} - {key.key_prefix}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="flex gap-2 overflow-x-auto pb-2 border-b border-gray-200 dark:border-gray-800">
          <button
            onClick={() => setFramework("html")}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              framework === "html"
                ? "bg-green-100 text-green-800 border-b-2 border-green-600 dark:bg-green-900/30 dark:text-green-400"
                : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            }`}
          >
            HTML / Vanilla JS
          </button>
          <button
            onClick={() => setFramework("react")}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              framework === "react"
                ? "bg-blue-100 text-blue-800 border-b-2 border-blue-600 dark:bg-blue-900/30 dark:text-blue-400"
                : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            }`}
          >
            React
          </button>
          <button
            onClick={() => setFramework("nextjs")}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
              framework === "nextjs"
                ? "bg-slate-200 text-slate-800 border-b-2 border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-400"
                : "text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
            }`}
          >
            Next.js
          </button>
        </div>

        {/* HTML Content */}
        {framework === "html" && (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <p className="text-sm text-blue-900 dark:text-blue-300 font-medium mb-2">
                📌 Choose Your Integration Method:
              </p>
              <p className="text-xs text-blue-800 dark:text-blue-400">
                You can either host the widget file yourself (Option 1) or load it directly from this server (Option 2 - Recommended for easier updates).
              </p>
            </div>

            {/* Option 2: CDN-Hosted (Recommended) */}
            <div className="border-2 border-green-300 dark:border-green-700 rounded-lg p-4 bg-green-50/50 dark:bg-green-950/30">
              <div className="flex items-start gap-3 mb-3">
                <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg shrink-0">
                  <Globe className="w-5 h-5 text-green-600 dark:text-green-400" />
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                    Option 2: Load from Server (Recommended)
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Widget loads directly from your eLanka Chat AI server. Best for external websites - always gets automatic updates.
                  </p>
                </div>
              </div>
              
              <div className="relative">
                <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-xs overflow-x-auto max-h-60">
                  <code>{`<!-- Option 2: Load widget from eLanka Chat AI server (Recommended) -->
<script>
  (function() {
    var script = document.createElement('script');
    script.src = '${window.location.origin}/widget.iife.js';
    script.onload = function() {
      window.eLankaChatAIWidget.init('${apiKeys.find(k => k._id === selectedKey)?.key || "YOUR_API_KEY_HERE"}', {
        apiUrl: '${window.location.origin}/api'
      });
    };
    document.body.appendChild(script);
  })();
</script>`}</code>
                </pre>
                <button
                  onClick={handleCopyCDN}
                  className="absolute top-2 right-2 p-2 bg-gray-800 hover:bg-gray-700 rounded transition-colors"
                  title="Copy to clipboard"
                >
                  {copiedExternal ? (
                    <Check className="w-4 h-4 text-green-400" />
                  ) : (
                    <Copy className="w-4 h-4 text-gray-400" />
                  )}
                </button>
              </div>

              <div className="mt-3 bg-white dark:bg-slate-800 rounded-lg p-3">
                <p className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">✨ Benefits:</p>
                <ul className="text-xs text-gray-600 dark:text-gray-400 space-y-1 list-disc list-inside">
                  <li>Always loads the latest widget version</li>
                  <li>No manual updates needed</li>
                  <li>Perfect for external websites</li>
                </ul>
              </div>
            </div>

            {/* Option 1: Self-Hosted */}
            <div className="border border-gray-300 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-start gap-3 mb-3">
                <div className="p-2 bg-gray-100 dark:bg-gray-800 rounded-lg shrink-0">
                  <Download className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                    Option 1: Download & Self-Host
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Download the widget file and host it on your own server. Requires manual updates.
                  </p>
                </div>
              </div>

              <button
                onClick={handleDownloadWidget}
                className="w-full mb-3 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                <Download size={16} />
                Download widget.iife.js
              </button>
              
              <div className="relative">
                <pre className="bg-gray-900 text-green-400 p-4 rounded-lg text-xs overflow-x-auto max-h-60">
                  <code>{`<!-- Option 1: Self-hosted widget -->
<!-- 1. Download widget.iife.js from your dashboard -->
<!-- 2. Upload it to your website's directory -->
<!-- 3. Add this code: -->
<script src="/path/to/widget.iife.js"></script>
<script>
  window.eLankaChatAIWidget.init('${apiKeys.find(k => k._id === selectedKey)?.key || "YOUR_API_KEY_HERE"}', {
    apiUrl: '${window.location.origin}/api'  // Your eLanka Chat AI server URL
  });
</script>`}</code>
                </pre>
                <button
                  onClick={handleCopySelfHosted}
                  className="absolute top-2 right-2 p-2 bg-gray-800 hover:bg-gray-700 rounded transition-colors"
                  title="Copy to clipboard"
                >
                  {copied ? (
                    <Check className="w-4 h-4 text-green-400" />
                  ) : (
                    <Copy className="w-4 h-4 text-gray-400" />
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* React Content */}
        {framework === "react" && (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300 border border-blue-200 dark:border-blue-900 bg-blue-50/30 dark:bg-blue-950/20 rounded-lg p-5">
            <div className="flex items-start gap-3 mb-4">
              <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg shrink-0">
                <Blocks className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                  React Integration
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Create a new component (e.g. <code>ChatWidget.jsx</code>) and include it in your app (like in <code>App.jsx</code>).
                </p>
              </div>
            </div>

            <div className="relative">
                <pre className="bg-gray-900 text-blue-400 p-4 rounded-lg text-xs overflow-x-auto max-h-[400px]">
                  <code>{`import { useEffect } from 'react';

export default function ChatWidget() {
  useEffect(() => {
    // Prevent multiple injections in development
    if (document.getElementById('elanka-chat-widget')) return;

    const script = document.createElement('script');
    script.id = 'elanka-chat-widget';
    script.src = '${window.location.origin}/widget.iife.js';
    script.async = true;
    script.onload = () => {
      if (window.eLankaChatAIWidget) {
        window.eLankaChatAIWidget.init('${apiKeys.find(k => k._id === selectedKey)?.key || "YOUR_API_KEY_HERE"}', {
          apiUrl: '${window.location.origin}/api'
        });
      }
    };
    document.body.appendChild(script);
  }, []);

  return null;
}`}</code>
                </pre>
                <button
                  onClick={handleCopyReact}
                  className="absolute top-2 right-2 p-2 bg-gray-800 hover:bg-gray-700 rounded transition-colors"
                  title="Copy to clipboard"
                >
                  {copiedExternal ? (
                    <Check className="w-4 h-4 text-green-400" />
                  ) : (
                    <Copy className="w-4 h-4 text-gray-400" />
                  )}
                </button>
            </div>
          </div>
        )}

        {/* Next.js Content */}
        {framework === "nextjs" && (
          <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300 border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 rounded-lg p-5">
            <div className="flex items-start gap-3 mb-4">
              <div className="p-2 bg-slate-200 dark:bg-slate-800 rounded-lg shrink-0">
                <Blocks className="w-5 h-5 text-slate-700 dark:text-slate-300" />
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                  Next.js Integration
                </h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Create a new file called <code>ChatWidget.jsx</code> (or <code>.tsx</code>), paste this code, and then include <code>&lt;ChatWidget /&gt;</code> in your root layout (<code>app/layout.tsx</code>).
                </p>
              </div>
            </div>

            <div className="relative">
                <pre className="bg-gray-900 text-slate-300 p-4 rounded-lg text-xs overflow-x-auto max-h-[400px]">
                  <code>{`'use client';

import Script from 'next/script';

export default function ChatWidget() {
  return (
    <Script 
      src="${window.location.origin}/widget.iife.js" 
      strategy="afterInteractive"
      onLoad={() => {
        if (window.eLankaChatAIWidget) {
          window.eLankaChatAIWidget.init('${apiKeys.find(k => k._id === selectedKey)?.key || "YOUR_API_KEY_HERE"}', {
            apiUrl: '${window.location.origin}/api'
          });
        }
      }}
    />
  );
}`}</code>
                </pre>
                <button
                  onClick={handleCopyNextjs}
                  className="absolute top-2 right-2 p-2 bg-gray-800 hover:bg-gray-700 rounded transition-colors"
                  title="Copy to clipboard"
                >
                  {copiedExternal ? (
                    <Check className="w-4 h-4 text-green-400" />
                  ) : (
                    <Copy className="w-4 h-4 text-gray-400" />
                  )}
                </button>
            </div>
          </div>
        )}

        {/* Installation Instructions (HTML only for simplicity, as React/Next have inline instructions) */}
        {framework === "html" && (
          <div className="bg-white dark:bg-slate-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 transition-colors">
            <h4 className="font-medium text-sm mb-3 flex items-center gap-2 text-gray-900 dark:text-white">
              <ExternalLink className="w-4 h-4 text-green-600 dark:text-green-400" />
              Installation Steps:
            </h4>
            <ol className="text-sm text-gray-700 dark:text-slate-300 space-y-2 list-decimal list-inside">
              <li>Copy your preferred embed code above</li>
              <li>Open your website's HTML file</li>
              <li>Paste the code before the closing <code className="bg-gray-100 dark:bg-slate-700 px-1 rounded text-xs">&lt;/body&gt;</code> tag</li>
              <li>If you see "YOUR_API_KEY_HERE", replace it with your actual API key</li>
              <li>Save and deploy your website</li>
              <li>The chat widget will appear in the bottom-right corner!</li>
            </ol>
          </div>
        )}

        {/* Testing Instructions */}
        <div className="bg-yellow-50 dark:bg-yellow-950 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <h4 className="font-medium text-sm mb-2 text-yellow-900 dark:text-yellow-300">
            🧪 Test Your Widget Locally:
          </h4>
          <ol className="text-xs text-yellow-800 dark:text-yellow-400 space-y-2 list-decimal list-inside">
            <li>Create a file named <code className="bg-yellow-100 dark:bg-yellow-900 px-1 rounded">test.html</code></li>
            <li>Paste the embed code inside the HTML file</li>
            <li>Open <code className="bg-yellow-100 dark:bg-yellow-900 px-1 rounded">test.html</code> in your browser</li>
            <li>The widget should appear and respond to your queries!</li>
          </ol>
        </div>

        <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-3">
          <p className="text-xs text-red-800 dark:text-red-400">
            🔒 <strong>Security Warning:</strong> Since the widget is embedded in the client HTML/JavaScript, the API key is visible to visitors. To prevent abuse, configure <strong>Whitelisted Domains</strong> under your <strong>API Key Settings</strong> so that requests from other domains are rejected.
          </p>
        </div>

        <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
          <p className="text-xs text-blue-800 dark:text-blue-400">
            💡 <strong>Tip:</strong> The widget will automatically use your customized chatbot name, greeting, and personality. Update these in the "Chatbot Identity" panel above to change how your widget appears to visitors.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
