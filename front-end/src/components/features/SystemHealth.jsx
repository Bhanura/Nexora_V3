import { useState, useEffect } from "react";
import { Activity, Cpu, HardDrive, Database, RefreshCw, AlertTriangle, CheckCircle, XCircle } from "lucide-react";
import { authenticatedFetch } from "../../config";
import { Card, CardContent } from "../ui/Card";

export default function SystemHealth() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    fetchHealth();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchHealth, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [autoRefresh]);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      const data = await authenticatedFetch("/admin/system/health");
      setHealth(data);
    } catch (err) {
      console.error("Failed to fetch system health:", err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "healthy":
        return <CheckCircle className="text-green-500" size={20} />;
      case "warning":
        return <AlertTriangle className="text-yellow-500" size={20} />;
      case "critical":
      case "error":
        return <XCircle className="text-red-500" size={20} />;
      default:
        return <Activity className="text-gray-500" size={20} />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "healthy":
        return "bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800";
      case "warning":
        return "bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-800";
      case "critical":
      case "error":
        return "bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800";
      default:
        return "bg-gray-50 border-gray-200 dark:bg-gray-900/20 dark:border-gray-800";
    }
  };

  const getProgressColor = (percent) => {
    if (percent >= 90) return "bg-red-500";
    if (percent >= 75) return "bg-yellow-500";
    return "bg-green-500";
  };

  if (loading && !health) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">Loading system health...</p>
      </div>
    );
  }

  if (!health) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Activity className="text-purple-600" size={28} />
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">System Health</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Last updated: {new Date(health.timestamp).toLocaleTimeString()}
            </p>
          </div>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
              autoRefresh
                ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                : "bg-gray-100 text-gray-700 dark:bg-slate-700 dark:text-gray-300"
            }`}
          >
            <RefreshCw size={16} className={autoRefresh ? "animate-spin" : ""} />
            {autoRefresh ? "Auto-refresh ON" : "Auto-refresh OFF"}
          </button>
          <button
            onClick={fetchHealth}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition disabled:opacity-50"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {/* Overall Status Banner */}
      <div className={`p-6 rounded-xl border-2 ${getStatusColor(health.overall_status)}`}>
        <div className="flex items-center gap-4">
          {getStatusIcon(health.overall_status)}
          <div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white capitalize">
              System Status: {health.overall_status}
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {health.overall_status === "healthy"
                ? "All systems operating normally"
                : health.overall_status === "warning"
                ? "Some metrics approaching thresholds"
                : "Critical issues detected - immediate attention required"}
            </p>
          </div>
        </div>
      </div>

      {/* System Resources */}
      <Card>
        <CardContent>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <Cpu size={20} />
            System Resources
          </h3>

          <div className="grid grid-cols-3 gap-6">
            {/* CPU */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getStatusIcon(health.system.cpu.status)}
                  <span className="font-medium text-gray-700 dark:text-gray-300">CPU</span>
                </div>
                <span className="text-2xl font-bold text-gray-900 dark:text-white">
                  {health.system.cpu.usage_percent}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all ${getProgressColor(health.system.cpu.usage_percent)}`}
                  style={{ width: `${health.system.cpu.usage_percent}%` }}
                />
              </div>
              <p className="text-xs text-gray-500">{health.system.cpu.cores} cores available</p>
            </div>

            {/* Memory */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getStatusIcon(health.system.memory.status)}
                  <span className="font-medium text-gray-700 dark:text-gray-300">Memory</span>
                </div>
                <span className="text-2xl font-bold text-gray-900 dark:text-white">
                  {health.system.memory.usage_percent}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all ${getProgressColor(health.system.memory.usage_percent)}`}
                  style={{ width: `${health.system.memory.usage_percent}%` }}
                />
              </div>
              <p className="text-xs text-gray-500">
                {health.system.memory.used_gb} GB / {health.system.memory.total_gb} GB
              </p>
            </div>

            {/* Disk */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getStatusIcon(health.system.disk.status)}
                  <span className="font-medium text-gray-700 dark:text-gray-300">Disk</span>
                </div>
                <span className="text-2xl font-bold text-gray-900 dark:text-white">
                  {health.system.disk.usage_percent}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all ${getProgressColor(health.system.disk.usage_percent)}`}
                  style={{ width: `${health.system.disk.usage_percent}%` }}
                />
              </div>
              <p className="text-xs text-gray-500">
                {health.system.disk.free_gb} GB free of {health.system.disk.total_gb} GB
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Database Stats */}
      <div className="grid grid-cols-2 gap-6">
        {/* MongoDB */}
        <Card>
          <CardContent>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <Database size={20} />
                MongoDB
              </h3>
              {getStatusIcon(health.mongodb.status)}
            </div>

            {health.mongodb.connected ? (
              <>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <MetricCard label="Total Documents" value={health.mongodb.total_documents.toLocaleString()} />
                  <MetricCard label="Collections" value={Object.keys(health.mongodb.collections).length} />
                  <MetricCard label="Data Size" value={`${health.mongodb.data_size_mb} MB`} />
                  <MetricCard label="Total Size" value={`${health.mongodb.total_size_mb} MB`} />
                </div>

                <div className="space-y-2">
                  <p className="text-xs font-semibold text-gray-600 dark:text-gray-400">Collection Counts:</p>
                  {Object.entries(health.mongodb.collections).map(([name, count]) => (
                    <div key={name} className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400 capitalize">{name}</span>
                      <span className="font-medium text-gray-900 dark:text-white">{count.toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <XCircle className="mx-auto text-red-500 mb-2" size={32} />
                <p className="text-red-600 font-medium">Connection Failed</p>
                <p className="text-xs text-gray-500 mt-1">{health.mongodb.error}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Qdrant */}
        <Card>
          <CardContent>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
                <HardDrive size={20} />
                Qdrant
              </h3>
              {getStatusIcon(health.qdrant.status)}
            </div>

            {health.qdrant.connected ? (
              <>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <MetricCard label="Total Vectors" value={health.qdrant.total_vectors.toLocaleString()} />
                  <MetricCard label="Collections" value={health.qdrant.total_collections} />
                </div>

                <div className="space-y-2 max-h-48 overflow-y-auto">
                  <p className="text-xs font-semibold text-gray-600 dark:text-gray-400">Vector Collections:</p>
                  {health.qdrant.collections.map((col) => (
                    <div key={col.name} className="flex justify-between items-center text-sm p-2 bg-gray-50 dark:bg-slate-800 rounded">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(col.status)}
                        <span className="text-gray-600 dark:text-gray-400 text-xs truncate max-w-[200px]">
                          {col.name}
                        </span>
                      </div>
                      <span className="font-medium text-gray-900 dark:text-white text-xs">
                        {col.vectors.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <XCircle className="mx-auto text-red-500 mb-2" size={32} />
                <p className="text-red-600 font-medium">Connection Failed</p>
                <p className="text-xs text-gray-500 mt-1">{health.qdrant.error}</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Network Stats */}
      <Card>
        <CardContent>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Network Activity</h3>
          <div className="grid grid-cols-2 gap-4">
            <MetricCard label="Data Sent" value={`${health.system.network.bytes_sent_mb} MB`} />
            <MetricCard label="Data Received" value={`${health.system.network.bytes_recv_mb} MB`} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({ label, value }) {
  return (
    <div className="p-3 bg-gray-50 dark:bg-slate-800 rounded-lg">
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{label}</p>
      <p className="text-lg font-bold text-gray-900 dark:text-white">{value}</p>
    </div>
  );
}
