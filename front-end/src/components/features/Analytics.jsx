import { useState, useEffect } from "react";
import { TrendingUp, Users, Upload, Activity, BarChart3, RefreshCw, Cpu } from "lucide-react";
import { authenticatedFetch } from "../../config";
import { Card, CardContent } from "../ui/Card";

export default function Analytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);
  const [tokenData, setTokenData] = useState([]);
  const [tokenLoading, setTokenLoading] = useState(false);

  useEffect(() => {
    fetchAnalytics();
    fetchTokenAnalytics();
  }, [days]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await authenticatedFetch(`/admin/analytics/overview?days=${days}`);
      setData(response);
    } catch (err) {
      console.error("Failed to fetch analytics:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTokenAnalytics = async () => {
    try {
      setTokenLoading(true);
      const res = await authenticatedFetch(`/analytics/super-admin/tokens?days=${days}`);
      setTokenData(res);
    } catch (err) {
      console.error("Failed to fetch admin token analytics:", err);
    } finally {
      setTokenLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 dark:text-gray-400">Loading analytics...</p>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <BarChart3 className="text-purple-600" size={28} />
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Platform Analytics</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Last {days} days of activity
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="px-4 py-2 border border-gray-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800 dark:text-white"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
          <button
            onClick={fetchAnalytics}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition disabled:opacity-50"
          >
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-4 gap-6">
        <MetricCard
          icon={Users}
          label="Total Users"
          value={data.total_users}
          color="blue"
        />
        <MetricCard
          icon={TrendingUp}
          label="Active Users"
          value={data.active_users}
          subtitle={`${data.activity_rate}% activity rate`}
          color="green"
        />
        <MetricCard
          icon={Users}
          label="New Registrations"
          value={data.registrations_over_time.reduce((sum, r) => sum + r.count, 0)}
          color="purple"
        />
        <MetricCard
          icon={Upload}
          label="Document Uploads"
          value={data.uploads_over_time.reduce((sum, u) => sum + u.count, 0)}
          color="orange"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-6">
        {/* Registrations Over Time */}
        <Card>
          <CardContent>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Users size={20} />
              User Registrations
            </h3>
            {data.registrations_over_time.length > 0 ? (
              <SimpleBarChart
                data={data.registrations_over_time}
                color="bg-purple-500"
              />
            ) : (
              <p className="text-center text-gray-500 py-8">No registrations in this period</p>
            )}
          </CardContent>
        </Card>

        {/* Uploads Over Time */}
        <Card>
          <CardContent>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Upload size={20} />
              Document Uploads
            </h3>
            {data.uploads_over_time.length > 0 ? (
              <SimpleBarChart
                data={data.uploads_over_time}
                color="bg-blue-500"
              />
            ) : (
              <p className="text-center text-gray-500 py-8">No uploads in this period</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Activity Breakdown & Top Users */}
      <div className="grid grid-cols-2 gap-6">
        {/* Activity by Type */}
        <Card>
          <CardContent>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Activity size={20} />
              Activity Breakdown
            </h3>
            <div className="space-y-3">
              {data.activity_by_type.slice(0, 10).map((activity, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">
                        {activity._id.replace(/_/g, " ")}
                      </span>
                      <span className="text-sm font-semibold text-gray-900 dark:text-white">
                        {activity.count}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full"
                        style={{
                          width: `${(activity.count / data.activity_by_type[0].count) * 100}%`
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Top Storage Users */}
        <Card>
          <CardContent>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <TrendingUp size={20} />
              Top Storage Users
            </h3>
            <div className="space-y-3">
              {data.top_storage_users.map((user, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-slate-800 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-brand-500 to-purple-600 text-white flex items-center justify-center font-bold text-xs">
                      #{idx + 1}
                    </div>
                    <span className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-[200px]">
                      {user.email}
                    </span>
                  </div>
                  <span className="text-sm font-bold text-purple-600 dark:text-purple-400">
                    {user.storage_mb.toFixed(2)} MB
                  </span>
                </div>
              ))}
              {data.top_storage_users.length === 0 && (
                <p className="text-center text-gray-500 py-8">No storage data available</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Client Token Usage Section */}
      <Card>
        <CardContent>
          <div className="flex items-center gap-3 mb-4">
            <Cpu className="text-purple-600" size={20} />
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              AI Token Consumption by Client
            </h3>
          </div>
          {tokenLoading ? (
            <p className="text-center text-gray-500 py-8">Loading token usage...</p>
          ) : tokenData.length === 0 ? (
            <p className="text-center text-gray-500 py-8">No token usage data available</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-slate-800 text-sm font-medium text-gray-500 dark:text-slate-400">
                    <th className="py-3 px-4">Client</th>
                    <th className="py-3 px-4">Company Name</th>
                    <th className="py-3 px-4">Total Tokens Used</th>
                    <th className="py-3 px-4">Prompt Tokens</th>
                    <th className="py-3 px-4">Completion Tokens</th>
                    <th className="py-3 px-4">API Queries</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 dark:divide-slate-800">
                  {tokenData.map((client) => {
                    const stats = client.token_usage || { total_tokens: 0, prompt_tokens: 0, completion_tokens: 0, request_count: 0 };
                    return (
                      <tr key={client._id} className="text-sm text-gray-900 dark:text-slate-100">
                        <td className="py-3 px-4 font-semibold">{client.email}</td>
                        <td className="py-3 px-4 text-gray-600 dark:text-slate-400">{client.name}</td>
                        <td className="py-3 px-4 font-bold text-purple-600 dark:text-purple-400">{stats.total_tokens.toLocaleString()}</td>
                        <td className="py-3 px-4 text-gray-600 dark:text-slate-400">{stats.prompt_tokens.toLocaleString()}</td>
                        <td className="py-3 px-4 text-gray-600 dark:text-slate-400">{stats.completion_tokens.toLocaleString()}</td>
                        <td className="py-3 px-4">{stats.request_count.toLocaleString()}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({ icon: Icon, label, value, subtitle, color }) {
  const colors = {
    blue: "bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400",
    green: "bg-green-50 text-green-600 dark:bg-green-900/20 dark:text-green-400",
    purple: "bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400",
    orange: "bg-orange-50 text-orange-600 dark:bg-orange-900/20 dark:text-orange-400"
  };

  return (
    <Card>
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">{label}</p>
            <p className="text-3xl font-bold text-gray-900 dark:text-white">{value}</p>
            {subtitle && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>
            )}
          </div>
          <div className={`p-3 rounded-xl ${colors[color]}`}>
            <Icon size={24} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function SimpleBarChart({ data, color }) {
  const maxValue = Math.max(...data.map(d => d.count));

  return (
    <div className="space-y-2">
      {data.map((item, idx) => (
        <div key={idx} className="flex items-center gap-3">
          <span className="text-xs text-gray-500 dark:text-gray-400 w-20 text-right">
            {new Date(item._id).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
          </span>
          <div className="flex-1 bg-gray-200 dark:bg-slate-700 rounded-full h-6 relative overflow-hidden">
            <div
              className={`${color} h-6 rounded-full flex items-center justify-end pr-2 transition-all`}
              style={{ width: `${(item.count / maxValue) * 100}%` }}
            >
              <span className="text-xs font-semibold text-white">{item.count}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
