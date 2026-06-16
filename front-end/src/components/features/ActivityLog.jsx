import { useState, useEffect } from "react";
import { Activity, Filter, ChevronLeft, ChevronRight, Calendar, User, FileText, Key, Shield, Trash2, Upload, LogIn, Ban } from "lucide-react";
import { authenticatedFetch } from "../../config";
import { Card, CardContent } from "../ui/Card";

export default function ActivityLog({ userId = null }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    actionType: "",
    resourceType: "",
    startDate: "",
    endDate: ""
  });
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 50,
    total: 0,
    pages: 1
  });

  useEffect(() => {
    fetchLogs();
  }, [userId, filters, pagination.page]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        skip: (pagination.page - 1) * pagination.limit,
        limit: pagination.limit
      });

      if (userId) params.append("user_id", userId);
      if (filters.actionType) params.append("action_type", filters.actionType);
      if (filters.resourceType) params.append("resource_type", filters.resourceType);
      if (filters.startDate) params.append("start_date", new Date(filters.startDate).toISOString());
      if (filters.endDate) params.append("end_date", new Date(filters.endDate).toISOString());

      const endpoint = userId 
        ? `/admin/user/${userId}/activity?days=30`
        : `/admin/activity-logs?${params}`;
      
      const data = await authenticatedFetch(endpoint);
      
      if (userId) {
        // User-specific summary
        setLogs(data.recent_activities || []);
        setPagination(prev => ({ ...prev, total: data.total_actions || 0 }));
      } else {
        // All logs
        setLogs(data.logs || []);
        setPagination(prev => ({
          ...prev,
          total: data.total,
          pages: data.pages
        }));
      }
    } catch (err) {
      console.error("Failed to fetch activity logs:", err);
    } finally {
      setLoading(false);
    }
  };

  const getActionIcon = (actionType) => {
    const icons = {
      login: LogIn,
      logout: LogIn,
      upload: Upload,
      delete: Trash2,
      delete_document: Trash2,
      delete_user: Trash2,
      create_user: User,
      ban_user: Ban,
      unban_user: Shield,
      revoke_api_key: Key,
      create: FileText
    };
    const Icon = icons[actionType] || Activity;
    return <Icon size={16} />;
  };

  const getActionColor = (actionType) => {
    const colors = {
      login: "text-green-600 bg-green-50",
      logout: "text-gray-600 bg-gray-50",
      upload: "text-blue-600 bg-blue-50",
      delete: "text-red-600 bg-red-50",
      delete_document: "text-red-600 bg-red-50",
      delete_user: "text-red-600 bg-red-50",
      create_user: "text-green-600 bg-green-50",
      ban_user: "text-orange-600 bg-orange-50",
      unban_user: "text-green-600 bg-green-50",
      revoke_api_key: "text-red-600 bg-red-50",
      create: "text-blue-600 bg-blue-50"
    };
    return colors[actionType] || "text-gray-600 bg-gray-50";
  };

  const formatActionText = (log) => {
    const actions = {
      login: `logged in`,
      logout: `logged out`,
      upload: `uploaded document "${log.details?.filename}"`,
      delete_document: `deleted document "${log.details?.filename}"`,
      delete_user: `deleted user ${log.details?.target_email}`,
      create_user: `created user ${log.details?.created_email}`,
      ban_user: `banned user ${log.details?.target_email}`,
      unban_user: `unbanned user ${log.details?.target_email}`,
      revoke_api_key: `revoked API key ${log.details?.key_prefix || ""}`,
      create: `created ${log.resource_type}`
    };
    return actions[log.action_type] || `performed ${log.action_type}`;
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, page: 1 })); // Reset to first page
  };

  const clearFilters = () => {
    setFilters({
      actionType: "",
      resourceType: "",
      startDate: "",
      endDate: ""
    });
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  return (
    <Card>
      <CardContent>
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Activity className="text-purple-600" size={24} />
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              {userId ? "User Activity" : "Activity Logs"}
            </h2>
          </div>
          {pagination.total > 0 && (
            <span className="text-sm text-gray-500">
              {pagination.total} total activities
            </span>
          )}
        </div>

        {/* Filters (only for global view) */}
        {!userId && (
          <div className="mb-6 p-4 bg-gray-50 dark:bg-slate-800 rounded-lg">
            <div className="flex items-center gap-2 mb-3">
              <Filter size={16} className="text-gray-500" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Filters</span>
            </div>
            <div className="grid grid-cols-4 gap-3">
              <select
                value={filters.actionType}
                onChange={(e) => handleFilterChange("actionType", e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-700 dark:text-white"
              >
                <option value="">All Actions</option>
                <option value="login">Login</option>
                <option value="logout">Logout</option>
                <option value="upload">Upload</option>
                <option value="delete_document">Delete Document</option>
                <option value="delete_user">Delete User</option>
                <option value="create_user">Create User</option>
                <option value="ban_user">Ban User</option>
                <option value="unban_user">Unban User</option>
                <option value="revoke_api_key">Revoke API Key</option>
              </select>

              <select
                value={filters.resourceType}
                onChange={(e) => handleFilterChange("resourceType", e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-700 dark:text-white"
              >
                <option value="">All Resources</option>
                <option value="document">Document</option>
                <option value="user">User</option>
                <option value="api_key">API Key</option>
                <option value="chat_session">Chat Session</option>
              </select>

              <input
                type="date"
                value={filters.startDate}
                onChange={(e) => handleFilterChange("startDate", e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-700 dark:text-white"
                placeholder="Start Date"
              />

              <input
                type="date"
                value={filters.endDate}
                onChange={(e) => handleFilterChange("endDate", e.target.value)}
                className="px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-700 dark:text-white"
                placeholder="End Date"
              />
            </div>
            {(filters.actionType || filters.resourceType || filters.startDate || filters.endDate) && (
              <button
                onClick={clearFilters}
                className="mt-3 text-sm text-purple-600 hover:text-purple-700 font-medium"
              >
                Clear Filters
              </button>
            )}
          </div>
        )}

        {/* Activity List */}
        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500 dark:text-gray-400">Loading activity...</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center py-12">
            <Activity size={48} className="mx-auto text-gray-300 dark:text-gray-600 mb-3" />
            <p className="text-gray-500 dark:text-gray-400">No activity logged yet</p>
          </div>
        ) : (
          <>
            <div className="space-y-2">
              {logs.map((log, index) => (
                <div
                  key={log._id || index}
                  className="flex items-start gap-4 p-4 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg hover:shadow-sm transition"
                >
                  {/* Icon */}
                  <div className={`p-2 rounded-lg ${getActionColor(log.action_type)}`}>
                    {getActionIcon(log.action_type)}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        {/* User Info */}
                        {!userId && (
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            {log.user_name || "Unknown User"}
                            <span className="text-gray-500 text-xs ml-2">
                              ({log.user_email || "unknown@example.com"})
                            </span>
                          </p>
                        )}
                        {/* Action Description */}
                        <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                          {formatActionText(log)}
                        </p>
                        {/* Resource Info */}
                        {log.resource_type && (
                          <div className="flex items-center gap-2 mt-2">
                            <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-400 rounded">
                              {log.resource_type}
                            </span>
                            {log.ip_address && (
                              <span className="text-xs text-gray-400">
                                IP: {log.ip_address}
                              </span>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Timestamp */}
                      <div className="text-right flex-shrink-0">
                        <p className="text-xs text-gray-400">
                          {new Date(log.timestamp).toLocaleDateString()}
                        </p>
                        <p className="text-xs text-gray-400">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination (only for global view) */}
            {!userId && pagination.pages > 1 && (
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200 dark:border-slate-700">
                <button
                  onClick={() => setPagination(prev => ({ ...prev, page: Math.max(1, prev.page - 1) }))}
                  disabled={pagination.page === 1}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  <ChevronLeft size={16} />
                  Previous
                </button>

                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Page {pagination.page} of {pagination.pages}
                </span>

                <button
                  onClick={() => setPagination(prev => ({ ...prev, page: Math.min(prev.pages, prev.page + 1) }))}
                  disabled={pagination.page === pagination.pages}
                  className="flex items-center gap-2 px-4 py-2 text-sm bg-gray-100 dark:bg-slate-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  Next
                  <ChevronRight size={16} />
                </button>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
