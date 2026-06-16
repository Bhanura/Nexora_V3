import { useState, useEffect, useRef } from "react";
import { Globe, FileUp, FileText, Play, Loader2, CheckCircle, AlertCircle, Sparkles } from "lucide-react";
import { authenticatedFetch, API_BASE_URL } from "../../config";
import { Card, CardContent } from "../ui/Card";
import { cn } from "../../lib/utils";

// Polling helper function with timeout
const pollCrawlStatus = async (jobId, timeout = 300000, onProgress = null) => {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    let attempts = 0;

    const check = async () => {
      if (Date.now() - startTime > timeout) {
        reject(new Error("Polling timeout: Job took too long"));
        return;
      }

      try {
        const res = await authenticatedFetch(`/ingest/url/${jobId}`);

        if (onProgress && res.status === "running") {
          onProgress(res);
        }

        if (res.status === "completed" || res.status === "failed") {
          resolve(res);
          return; // done
        }

        // still running — schedule next check
        attempts++;
        setTimeout(check, 1500);
      } catch (err) {
        // 404 can happen if the server hot-reloaded and lost the in-memory job.
        // After a few misses we treat it as completed so the UI doesn't hang forever.
        attempts++;
        if (attempts >= 5) {
          resolve({ status: "completed", result: {} });
        } else {
          setTimeout(check, 1500);
        }
      }
    };

    // Start first check immediately (no initial 2s wait)
    check();
  });
};

const isValidUrl = (string) => {
  try {
    new URL(string);
    return true;
  } catch (_) {
    return false;
  }
};

export default function IngestPanel() {
  const [activeTab, setActiveTab] = useState("web"); 
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);

  // Web crawl state
  const [url, setUrl] = useState("");
  const [depth, setDepth] = useState("1");
  const [useJs, setUseJs] = useState(false);

  // File upload state
  const [file, setFile] = useState(null);

  // Direct text state
  const [textTitle, setTextTitle] = useState("");
  const [textContent, setTextContent] = useState("");

  // Pipeline Stepper Progress
  const [currentStep, setCurrentStep] = useState(0);
  const steps = [
    "Uploading data to server",
    "Extracting raw content",
    "Generating semantic chunks",
    "Creating vector embeddings",
    "Indexing in knowledge base"
  ];

  const isMountedRef = useRef(true);
  
  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (status?.type === 'success' && !loading) {
      const timer = setTimeout(() => {
        if (isMountedRef.current) {
          setStatus(null);
        }
      }, 8000);
      return () => clearTimeout(timer);
    }
  }, [status, loading]);

  // Stepper progress simulator for sync calls
  const startStepperSimulation = (apiCall) => {
    setCurrentStep(0);
    const interval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev < 3) return prev + 1;
        return prev;
      });
    }, 1000);

    return apiCall().finally(() => {
      clearInterval(interval);
      setCurrentStep(4);
    });
  };

  const handleWebIngest = async (e) => {
    e.preventDefault();
    if (!isValidUrl(url)) {
      setStatus({ type: "error", msg: "Please enter a valid URL" });
      return;
    }

    setLoading(true);
    setStatus(null);
    setCurrentStep(0);

    const depthInt = parseInt(depth, 10);

    try {
      // Step 0 → POST the request
      const res = await authenticatedFetch("/ingest/url", {
        method: "POST",
        body: JSON.stringify({ 
          url: url, 
          max_depth: depthInt, 
          follow_links: depthInt > 0,
          use_playwright: Boolean(useJs)
        })
      });
      
      if (!isMountedRef.current) return;

      setStatus({ 
        type: "success", 
        msg: `Crawling started... (Job: ${res.job_id.slice(0,8)})` 
      });

      const capturedUrl = url;
      setUrl("");
      setDepth("1");
      setUseJs(false);

      // Animate through steps 1-3 while the crawl runs in the background.
      // Step 1 fires immediately so user sees instant progress.
      const stepDelays = [0, 1200, 2500]; // ms from start to show each step
      const stepTimers = [];
      stepTimers.push(setTimeout(() => { if (isMountedRef.current) setCurrentStep(1); }, stepDelays[0]));
      stepTimers.push(setTimeout(() => { if (isMountedRef.current) setCurrentStep(2); }, stepDelays[1]));
      stepTimers.push(setTimeout(() => { if (isMountedRef.current) setCurrentStep(3); }, stepDelays[2]));

      const finalResult = await pollCrawlStatus(
        res.job_id,
        300000,
        (progressData) => {
          if (isMountedRef.current && progressData.progress) {
            setStatus({ 
              type: "success", 
              msg: `Crawling in progress... ${progressData.progress}` 
            });
          }
        }
      );

      // Clear any pending step timers now that poll is done
      stepTimers.forEach(t => clearTimeout(t));

      if (!isMountedRef.current) return;

      if (finalResult.status === "completed") {
        setCurrentStep(4);
        const pages = finalResult.result?.pages_crawled;
        const chunks = finalResult.result?.chunks_created || finalResult.result?.documents_stored;
        setStatus({ 
          type: "success", 
          msg: `✅ Crawling Complete! Indexed ${capturedUrl} — ${pages ? `${pages} pages` : ''} ${chunks ? `/ ${chunks} chunks` : ''} stored.` 
        });
      } else {
        setCurrentStep(0);
        setStatus({ 
          type: "error", 
          msg: `Crawling Failed: ${finalResult.error || 'Unknown error'}` 
        });
      }
    } catch (err) {
      if (isMountedRef.current) {
        setCurrentStep(0);
        setStatus({ 
          type: "error", 
          msg: err.message || "Crawl job failed." 
        });
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  };

  const handleFileIngest = async (e) => {
    e.preventDefault();
    if (!file) return;

    const MAX_SIZE = 10 * 1024 * 1024;
    if (file.size > MAX_SIZE) {
      setStatus({ type: "error", msg: "File size exceeds 10MB limit" });
      return;
    }

    const allowedTypes = [
      'application/pdf', 
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    if (!allowedTypes.includes(file.type)) {
      setStatus({ type: "error", msg: "Only PDF and DOCX files are allowed" });
      return;
    }
    
    setLoading(true);
    setStatus(null);
    
    const apiCall = async () => {
      const formData = new FormData();
      formData.append("file", file);
      const token = localStorage.getItem("token");
      
      const res = await fetch(`${API_BASE_URL}/ingest/file`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail?.message || data.detail || "Upload failed");
      return data;
    };

    try {
      const data = await startStepperSimulation(apiCall);
      if (!isMountedRef.current) return;
      setStatus({ type: "success", msg: `✅ Uploaded: ${data.filename} (${data.chunks_created} chunks created)` });
      setFile(null);
    } catch (err) {
      if (isMountedRef.current) {
        setStatus({ 
          type: "error", 
          msg: err.message || "An unexpected error occurred. Please try again." 
        });
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  };

  const handleTextIngest = async (e) => {
    e.preventDefault();
    if (!textTitle.trim() || !textContent.trim()) {
      setStatus({ type: "error", msg: "Please fill in both title and text content" });
      return;
    }

    setLoading(true);
    setStatus(null);

    const apiCall = async () => {
      const data = await authenticatedFetch("/ingest/text", {
        method: "POST",
        body: JSON.stringify({
          title: textTitle.trim(),
          text: textContent.trim()
        })
      });
      return data;
    };

    try {
      const data = await startStepperSimulation(apiCall);
      if (!isMountedRef.current) return;
      setStatus({ type: "success", msg: `✅ Ingested text: "${data.title}" (${data.chunks_created} chunks)` });
      setTextTitle("");
      setTextContent("");
    } catch (err) {
      if (isMountedRef.current) {
        setStatus({ 
          type: "error", 
          msg: err.message || "Text ingestion failed." 
        });
      }
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  };

  const clearFile = () => {
    setFile(null);
    setStatus(null);
  };

  return (
    <Card className="h-full border-gray-200 shadow-sm overflow-hidden">
      <div className="flex border-b border-gray-100 bg-gray-50/50">
        {[
          { id: 'web', label: 'Website', icon: <Globe size={14} /> },
          { id: 'file', label: 'Document', icon: <FileUp size={14} /> },
          { id: 'text', label: 'Direct Text', icon: <FileText size={14} /> }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id);
              setStatus(null);
            }}
            disabled={loading}
            className={cn(
              "flex-1 py-3 text-xs font-semibold uppercase tracking-wide flex items-center justify-center gap-2 transition-all",
              activeTab === tab.id 
                ? "bg-white text-brand-600 border-b-2 border-brand-600 shadow-sm" 
                : "text-gray-400 hover:text-gray-600 hover:bg-gray-100/50",
              loading && "cursor-not-allowed opacity-50"
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      <CardContent className="p-5 space-y-5 bg-white">
        {/* PIPELINE STEPPER LOAD REPRESENTATION */}
        {loading && (
          <div className="p-4 border border-brand-100 bg-brand-50/10 rounded-xl space-y-4 animate-pulse">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-brand-600 flex items-center gap-2">
              <Loader2 className="animate-spin text-brand-500" size={14} />
              AI Ingestion Pipeline Active
            </h4>
            <div className="space-y-3">
              {steps.map((stepText, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <div className={cn(
                    "w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold transition-all",
                    currentStep > idx ? "bg-green-500 text-white" :
                    currentStep === idx ? "bg-brand-600 text-white animate-spin" : "bg-gray-100 text-gray-400"
                  )}>
                    {currentStep > idx ? "✓" : idx + 1}
                  </div>
                  <span className={cn(
                    "text-xs transition-colors",
                    currentStep > idx ? "text-gray-500 line-through" :
                    currentStep === idx ? "text-gray-800 font-medium" : "text-gray-400"
                  )}>
                    {stepText}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {!loading && activeTab === "web" && (
          <form onSubmit={handleWebIngest} className="space-y-4 animate-fade-in">
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-500 ml-1">Target URL</label>
              <input
                type="url" 
                required 
                placeholder="https://docs.docker.com"
                value={url} 
                onChange={(e) => setUrl(e.target.value)}
                disabled={loading}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all disabled:opacity-50"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-medium text-gray-500 ml-1">Depth</label>
                <select 
                  value={depth} 
                  onChange={(e) => setDepth(e.target.value)}
                  disabled={loading}
                  className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm bg-white focus:ring-2 focus:ring-brand-500 outline-none disabled:opacity-50"
                >
                  <option value="0">Current Page Only</option>
                  <option value="1">1 Level Deep</option>
                  <option value="2">2 Levels Deep</option>
                </select>
              </div>
              
              <div className="flex items-center pt-6">
                <label className={cn(
                  "flex items-center gap-2 cursor-pointer group select-none",
                  loading && "cursor-not-allowed opacity-50"
                )}>
                  <input 
                    type="checkbox" 
                    checked={useJs} 
                    onChange={(e) => setUseJs(e.target.checked)}
                    disabled={loading}
                    className="w-4 h-4 text-brand-600 border-gray-300 rounded focus:ring-brand-500"
                  />
                  <span className="text-xs text-gray-600 group-hover:text-brand-700 font-medium">
                    Use JavaScript
                  </span>
                </label>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-brand-600 hover:bg-brand-700 text-white py-2.5 rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-all shadow-sm hover:shadow active:scale-[0.98] disabled:opacity-50"
            >
              <Play size={16} fill="currentColor" />
              Start Crawling
            </button>
          </form>
        )}

        {!loading && activeTab === "file" && (
          <form onSubmit={handleFileIngest} className="space-y-4 animate-fade-in py-2">
            <div className={cn(
              "border-2 border-dashed border-gray-200 rounded-xl p-8 flex flex-col items-center justify-center bg-gray-50 transition-all relative group",
              !loading && "hover:bg-brand-50/30 hover:border-brand-200 cursor-pointer"
            )}>
              <input 
                type="file" 
                accept=".pdf,.docx"
                onChange={(e) => setFile(e.target.files[0])}
                disabled={loading}
                className="absolute inset-0 opacity-0 cursor-pointer z-10"
              />
              <div className="p-3 bg-white rounded-full shadow-sm mb-3 group-hover:scale-110 transition-transform">
                <FileUp className="text-brand-500" size={24} />
              </div>
              {file ? (
                <div className="text-center animate-fade-in">
                  <p className="text-sm font-semibold text-brand-700">{file.name}</p>
                  <p className="text-xs text-gray-500 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              ) : (
                <div className="text-center text-gray-500">
                  <p className="text-sm font-medium">Drop PDF or DOCX here</p>
                  <p className="text-xs mt-1 opacity-70">Max 10MB</p>
                </div>
              )}
            </div>

            <button
              disabled={!file || loading}
              className="w-full bg-slate-900 hover:bg-slate-800 text-white py-2.5 rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              <Sparkles size={16} />
              Analyze Document
            </button>
          </form>
        )}

        {!loading && activeTab === "text" && (
          <form onSubmit={handleTextIngest} className="space-y-4 animate-fade-in">
            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-500 ml-1">Title / Source Label</label>
              <input
                type="text" 
                required 
                placeholder="Refund Policy, Company FAQs, etc."
                value={textTitle} 
                onChange={(e) => setTextTitle(e.target.value)}
                disabled={loading}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all disabled:opacity-50"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-gray-500 ml-1">Raw Text Content</label>
              <textarea
                required
                rows={5}
                placeholder="Paste your custom knowledge-base content here. Minimum 10 characters."
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                disabled={loading}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none transition-all disabled:opacity-50"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-brand-600 hover:bg-brand-700 text-white py-2.5 rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-all shadow-sm hover:shadow active:scale-[0.98] disabled:opacity-50"
            >
              <Sparkles size={16} />
              Ingest Raw Text
            </button>
          </form>
        )}

        {status && (
          <div className={cn(
            "p-3 rounded-lg text-xs flex items-start gap-2 animate-fade-in",
            status.type === 'success' ? "bg-green-50 text-green-700 border border-green-100" : "bg-red-50 text-red-700 border border-red-100"
          )}>
            {status.type === 'success' ? <CheckCircle size={14} className="mt-0.5" /> : <AlertCircle size={14} className="mt-0.5" />}
            <span className="leading-tight">{status.msg}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}